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

    # =============================
    # Item Search — !item <name>
    # =============================
    @commands.command(
        name="item",
        help="Search for an FFXIV item by name (English or Japanese)",
        description="Command: !item <name>",
        brief="Search for an FFXIV item"
    )
    async def item_search(self, ctx: commands.Context, *, name: str):
        detected_lang = self.detect_language(name)
        cache_key = f"item:auto:{name.lower()}"
        results = self.cache.get(cache_key)

        if results is None:
            results = await self.garland_search(name, lang=detected_lang)
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
        embed.add_field(name="English", value=en_item.get("name", "N/A"), inline=False)
        embed.add_field(name="Japanese", value=ja_item.get("name", "N/A"), inline=False)
        embed.add_field(name="Item Level", value=en_item.get("ilvl", "N/A"))
        embed.add_field(name="Detected Input Language", value=detected_lang.upper())

        await ctx.send(embed=embed)

    @item_search.error
    async def item_search_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide an item name. Usage: `!item <name>`")

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
        help="Get market board pricing for an item. Usage: !market <world|dc|region> <item name>",
        description="Command: !market <world|dc|region> <item name>",
        brief="Get market board pricing"
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

        embed = discord.Embed(
            title=resolved_name,
            url=GARLAND_DB.format(item_id=item_id),
            description=f"{loc_type}: {location}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Minimum Price", value=data.get("minPrice") or "N/A")
        embed.add_field(name="Average Price", value=data.get("averagePrice") or "N/A")

        await ctx.send(embed=embed)

    @market_price.error
    async def market_price_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `!market <world|dc|region> <item name>`")


async def setup(bot: commands.Bot):
    await bot.add_cog(FFXIVCog(bot))
