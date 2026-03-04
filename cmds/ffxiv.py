import time
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks


GARLAND_SEARCH = "https://www.garlandtools.org/api/search.php"
GARLAND_ITEM   = "https://www.garlandtools.org/db/doc/item/{lang}/3/{item_id}.json"
GARLAND_DB     = "https://www.garlandtools.org/db/#item/{item_id}"


# =============================
# Simple In-Memory Cache (TTL Based + Cleanup)
# =============================
class TTLCache:
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time() + self.ttl)

    def cleanup(self):
        now = time.time()
        expired = [k for k, (_, exp) in self.cache.items() if now >= exp]
        for k in expired:
            del self.cache[k]


class FFXIVCog(commands.Cog, name="FFXIV"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = TTLCache(ttl=300)
        self.location_cache = {
            "worlds": {},       # lower -> proper name
            "datacenters": {},  # lower -> proper name
            "regions": {},      # lower -> proper name
            "last_updated": 0,
        }
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        await self.fetch_locations()
        self.cache_cleanup_task.start()

    async def cog_unload(self):
        self.cache_cleanup_task.cancel()
        if self.session:
            await self.session.close()

    # =============================
    # Background Cache Cleanup Task
    # =============================
    @tasks.loop(minutes=5)
    async def cache_cleanup_task(self):
        self.cache.cleanup()

    # =============================
    # Location Fetching (Worlds, Data Centers, Regions via Universalis)
    # =============================
    async def fetch_locations(self):
        async with self.session.get("https://universalis.app/api/v2/worlds") as resp:
            if resp.status == 200:
                data = await resp.json()
                self.location_cache["worlds"] = {
                    w["name"].lower(): w["name"] for w in data
                }

        async with self.session.get("https://universalis.app/api/v2/data-centers") as resp:
            if resp.status == 200:
                data = await resp.json()
                for dc in data:
                    self.location_cache["datacenters"][dc["name"].lower()] = dc["name"]
                    region = dc["region"]
                    self.location_cache["regions"][region.lower()] = region

        self.location_cache["last_updated"] = time.time()

    def is_valid_location(self, name: str) -> bool:
        lower = name.lower()
        return (
            lower in self.location_cache["worlds"]
            or lower in self.location_cache["datacenters"]
            or lower in self.location_cache["regions"]
        )

    def normalize_location(self, name: str) -> str:
        lower = name.lower()
        return (
            self.location_cache["worlds"].get(lower)
            or self.location_cache["datacenters"].get(lower)
            or self.location_cache["regions"].get(lower)
        )

    def location_type(self, name: str) -> str:
        lower = name.lower()
        if lower in self.location_cache["worlds"]:
            return "World"
        if lower in self.location_cache["datacenters"]:
            return "Data Center"
        if lower in self.location_cache["regions"]:
            return "Region"
        return "Location"

    # =============================
    # Helper: Detect Japanese vs English
    # =============================
    @staticmethod
    def detect_language(text: str) -> str:
        for ch in text:
            if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9faf":
                return "ja"
        return "en"

    # =============================
    # Garland Tools Helpers
    # =============================
    async def garland_search(self, name: str, lang: str = "en") -> list:
        """Search items via Garland Tools. Returns list of result objects."""
        params = {"text": name, "lang": lang, "type": "item"}
        async with self.session.get(GARLAND_SEARCH, params=params) as resp:
            if resp.status != 200:
                return []
            return await resp.json()

    async def garland_item(self, item_id: int, lang: str = "en") -> dict:
        """Fetch item details from Garland Tools in the given language."""
        url = GARLAND_ITEM.format(lang=lang, item_id=item_id)
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
            return data.get("item", {})

    @staticmethod
    def _normalize_icon_url(icon_value) -> str | None:
        if not icon_value:
            return None
        if isinstance(icon_value, int):
            return f"https://www.garlandtools.org/files/icons/item/{icon_value}.png"
        if isinstance(icon_value, float):
            return f"https://www.garlandtools.org/files/icons/item/{int(icon_value)}.png"
        if isinstance(icon_value, str):
            if icon_value.isdigit():
                return f"https://www.garlandtools.org/files/icons/item/{icon_value}.png"
            if icon_value.startswith("http://") or icon_value.startswith("https://"):
                return icon_value
            if icon_value.startswith("//"):
                return f"https:{icon_value}"
            if icon_value.startswith("/"):
                return f"https://www.garlandtools.org{icon_value}"
            return f"https://www.garlandtools.org/{icon_value.lstrip('/')}"
        return None

    @staticmethod
    def _format_item_stats(item: dict, compact: bool = False) -> str | None:
        label_map = [
            ("Item Level", "ilvl"),
            ("Required Level", "rlv"),
            ("Rarity", "rarity"),
            ("Materia Slots", "materiaSlotCount"),
            ("Stack Size", "stack"),
            ("Defense", "defense"),
            ("Magic Defense", "magicDefense"),
            ("Physical Damage", "damage"),
            ("Auto-Attack", "autoAttack"),
            ("Delay", "delay"),
            ("Block", "block"),
            ("Block Rate", "blockRate"),
            ("Can Be HQ", "canBeHq"),
            ("Unique", "isUnique"),
            ("Untradable", "isUntradable"),
        ]

        lines = []
        for label, key in label_map:
            value = item.get(key)
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(f"{label}: {value}")

        nested_stats = item.get("stats")
        if isinstance(nested_stats, dict):
            for key, value in nested_stats.items():
                if value is None or value == "":
                    continue
                lines.append(f"{str(key).replace('_', ' ').title()}: {value}")

        if not lines:
            return None

        if compact:
            lines = lines[:6]

        stats_text = "\n".join(lines)
        return stats_text[:1021] + "..." if len(stats_text) > 1024 else stats_text

    # =============================
    # Item Search — !item <name>
    # =============================
    @commands.command(
        name="item",
        help="Search for an FFXIV item by name (English/Japanese). Use !item short <name> for compact output",
        description="Command: !item [short|--short] <name>",
        brief="Search for an FFXIV item"
    )
    async def item_search(self, ctx: commands.Context, *, name: str):
        compact = False
        query_name = name.strip()
        lowered = query_name.lower()

        if lowered.startswith("short "):
            compact = True
            query_name = query_name[6:].strip()
        elif lowered.startswith("--short "):
            compact = True
            query_name = query_name[8:].strip()

        if not query_name:
            await ctx.send("Please provide an item name. Usage: `!item [short|--short] <name>`")
            return

        detected_lang = self.detect_language(query_name)
        cache_key = f"item:auto:{query_name.lower()}"
        results = self.cache.get(cache_key)

        if results is None:
            results = await self.garland_search(query_name, lang=detected_lang)
            self.cache.set(cache_key, results)

        if not results:
            await ctx.send("No items found.")
            return

        item_id = results[0]["obj"]["i"]

        # Fetch EN and JP details in parallel
        en_item, ja_item = await asyncio.gather(
            self.garland_item(item_id, "en"),
            self.garland_item(item_id, "ja"),
        )

        embed = discord.Embed(
            title=en_item.get("name", "Unknown Item"),
            url=GARLAND_DB.format(item_id=item_id),
            color=discord.Color.blurple()
        )

        icon_url = self._normalize_icon_url(en_item.get("icon") or ja_item.get("icon"))
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        embed.add_field(name="English", value=en_item.get("name", "N/A"), inline=False)
        embed.add_field(name="Japanese", value=ja_item.get("name", "N/A"), inline=False)
        embed.add_field(name="Item Level", value=en_item.get("ilvl", "N/A"))
        embed.add_field(name="Required Level", value=en_item.get("rlv", "N/A"))

        category = en_item.get("category")
        if isinstance(category, dict):
            category = category.get("name")
        if category:
            embed.add_field(name="Category", value=category)

        stats_text = self._format_item_stats(en_item, compact=compact)
        if stats_text:
            embed.add_field(name="Stats", value=stats_text, inline=False)

        embed.add_field(name="Detected Input Language", value=detected_lang.upper())
        embed.set_footer(text="Data & image from garlandtools.org")

        await ctx.send(embed=embed)

    @item_search.error
    async def item_search_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide an item name. Usage: `!item [short|--short] <name>`")

    # =============================
    # Cross-Language Translation — !translate_item <en|ja> <name>
    # =============================
    @commands.command(
        name="translate_item",
        help="Translate an FFXIV item name between EN and JP. Usage: !translate_item <en|ja> <name>",
        description="Command: !translate_item <en|ja> <name>",
        brief="Translate an item name EN \u2194 JP"
    )
    async def translate_item(self, ctx: commands.Context, target_language: str, *, name: str):
        target_language = target_language.lower()
        if target_language not in ["en", "ja"]:
            await ctx.send("Target language must be `en` or `ja`. Usage: `!translate_item <en|ja> <name>`")
            return

        source_language = self.detect_language(name)
        results = await self.garland_search(name, lang=source_language)

        if not results:
            await ctx.send("Item not found.")
            return

        item_id = results[0]["obj"]["i"]
        translated = await self.garland_item(item_id, target_language)

        embed = discord.Embed(title="Item Translation", color=discord.Color.purple())
        embed.add_field(name="Original", value=name, inline=False)
        embed.add_field(
            name=f"Translated ({target_language.upper()})",
            value=translated.get("name", "N/A"),
            inline=False
        )
        await ctx.send(embed=embed)

    @translate_item.error
    async def translate_item_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `!translate_item <en|ja> <name>`")

    # =============================
    # Market Board Pricing — !market <world|dc|region> <item name>
    # =============================
    @commands.command(
        name="market",
        help="Get market board pricing for an item including HQ/NQ, retainers, and servers. Usage: !market <world|dc|region> <item name>",
        description="Command: !market <world|dc|region> <item name>",
        brief="Get detailed market board pricing"
    )
    async def market_price(self, ctx: commands.Context, location: str, *, item_name: str):
        if not self.is_valid_location(location):
            await ctx.send(f"`{location}` is not a valid world, data center, or region.")
            return

        loc_type = self.location_type(location)
        location = self.normalize_location(location)

        results = await self.garland_search(item_name)
        if not results:
            await ctx.send(f"No item found for `{item_name}`.")
            return

        item_id = results[0]["obj"]["i"]
        resolved_name = results[0]["obj"]["n"]

        cache_key = f"market:{item_id}:{location.lower()}"
        data = self.cache.get(cache_key)

        if not data:
            async with self.session.get(
                f"https://universalis.app/api/v2/{location}/{item_id}"
            ) as resp:
                if resp.status != 200:
                    await ctx.send("Failed to fetch market data.")
                    return
                data = await resp.json()
                self.cache.set(cache_key, data)

        # Separate NQ and HQ listings
        nq_listings = [l for l in data.get("listings", []) if not l.get("hq")]
        hq_listings = [l for l in data.get("listings", []) if l.get("hq")]

        embed = discord.Embed(
            title=resolved_name,
            url=GARLAND_DB.format(item_id=item_id),
            description=f"{loc_type}: {location}",
            color=discord.Color.gold()
        )

        # Overall pricing
        overall_min = data.get("minPrice")
        overall_avg = data.get("averagePrice")
        embed.add_field(
            name="Overall Pricing",
            value=f"Min: {overall_min or 'N/A'} | Avg: {overall_avg or 'N/A'}",
            inline=False
        )

        # NQ Pricing
        if nq_listings:
            nq_min = min(l["pricePerUnit"] for l in nq_listings)
            nq_avg = sum(l["pricePerUnit"] for l in nq_listings) / len(nq_listings)
            embed.add_field(
                name="NQ Pricing",
                value=f"Min: {nq_min} | Avg: {nq_avg:.0f} | Listings: {len(nq_listings)}",
                inline=False
            )

        # HQ Pricing
        if hq_listings:
            hq_min = min(l["pricePerUnit"] for l in hq_listings)
            hq_avg = sum(l["pricePerUnit"] for l in hq_listings) / len(hq_listings)
            embed.add_field(
                name="HQ Pricing",
                value=f"Min: {hq_min} | Avg: {hq_avg:.0f} | Listings: {len(hq_listings)}",
                inline=False
            )

        # Cheapest listings with retainer and server info
        all_listings = sorted(data.get("listings", [])[:5], key=lambda x: x.get("pricePerUnit", 0))
        if all_listings:
            listings_text = ""
            for i, listing in enumerate(all_listings, 1):
                quality = "HQ" if listing.get("hq") else "NQ"
                price = listing.get("pricePerUnit", "N/A")
                qty = listing.get("quantity", "?")
                retainer = listing.get("retainerName", "Unknown")
                server = listing.get("worldName", "?")
                listings_text += f"`{quality}` {price}g (x{qty}) - {retainer} @ {server}\n"

            embed.add_field(
                name="Cheapest Listings (Top 5)",
                value=listings_text.strip(),
                inline=False
            )

        # Server breakdown for regions/data centers
        if loc_type in ["Data Center", "Region"]:
            server_prices = {}
            for listing in data.get("listings", []):
                world = listing.get("worldName", "Unknown")
                price = listing.get("pricePerUnit", 0)
                hq_status = listing.get("hq", False)

                if world not in server_prices:
                    server_prices[world] = {"NQ": [], "HQ": []}

                key = "HQ" if hq_status else "NQ"
                server_prices[world][key].append(price)

            server_text = ""
            for world in sorted(server_prices.keys()):
                prices = server_prices[world]
                nq_min = min(prices["NQ"]) if prices["NQ"] else None
                hq_min = min(prices["HQ"]) if prices["HQ"] else None

                price_str = ""
                if nq_min:
                    price_str += f"NQ: {nq_min}g"
                if hq_min:
                    if price_str:
                        price_str += f" | HQ: {hq_min}g"
                    else:
                        price_str = f"HQ: {hq_min}g"

                if price_str:
                    server_text += f"{world}: {price_str}\n"

            if server_text:
                embed.add_field(
                    name="Server Breakdown",
                    value=server_text.strip(),
                    inline=False
                )

        await ctx.send(embed=embed)

    @market_price.error
    async def market_price_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `!market <world|dc|region> <item name>`")


async def setup(bot: commands.Bot):
    await bot.add_cog(FFXIVCog(bot))
