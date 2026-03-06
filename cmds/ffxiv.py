import re
import time
import asyncio
import html as html_lib
from html.parser import HTMLParser
import aiohttp
import discord
from discord.ext import commands, tasks


# Eriones.com — used by !item (JP site for search + JP names, EN site for EN names)
ERIONES_JP      = "https://eriones.com"
ERIONES_EN      = "https://en.eriones.com"
ERIONES_SEARCH_JP = "https://eriones.com/tmp/load/db"
ERIONES_SEARCH_EN = "https://en.eriones.com/tmp/load/db"

# Garland Tools — still used by !market and !translate_item
GARLAND_SEARCH = "https://www.garlandtools.org/api/search.php"
GARLAND_ITEM   = "https://www.garlandtools.org/db/doc/item/{lang}/3/{item_id}.json"
GARLAND_DB     = "https://www.garlandtools.org/db/#item/{item_id}"


class _VisibleTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str):
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


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
    EQUIPMENT_SLOT_KEYWORDS = {
        "weapon": "Weapon",
        "secondary": "Secondary Weapon",
        "shield": "Shield",
        "head": "Head",
        "body": "Body",
        "hands": "Hands",
        "feet": "Feet",
        "legs": "Legs",
        "neck": "Neck",
        "ring": "Finger",
        "finger": "Finger",
        "ear": "Ear",
        "wrist": "Wrist",
    }

    FULLWIDTH_TRANSLATION = str.maketrans({
        "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
        "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
        "＋": "+", "－": "-", "：": ":", "／": "/", "　": " ",
    })

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

    # =============================
    # Eriones Helpers
    # =============================
    @staticmethod
    def _normalize_search_name(value: str | None) -> str:
        if not value:
            return ""
        lowered = html_lib.unescape(value).casefold()
        return re.sub(r"[\W_]+", "", lowered, flags=re.UNICODE)

    def _match_priority(self, query: str, candidate: str) -> tuple[int, int, int]:
        query_norm = self._normalize_search_name(query)
        cand_norm = self._normalize_search_name(candidate)

        if not query_norm or not cand_norm:
            return (4, 9999, 9999)
        if cand_norm == query_norm:
            return (0, 0, len(cand_norm))
        if cand_norm.startswith(query_norm):
            return (1, len(cand_norm) - len(query_norm), len(cand_norm))
        if query_norm in cand_norm:
            return (2, cand_norm.find(query_norm), len(cand_norm))
        return (3, abs(len(cand_norm) - len(query_norm)), len(cand_norm))

    @staticmethod
    def _find_tag_open_end(source: str, start_index: int) -> int:
        """Return the index of the '>' that closes a tag, ignoring quoted content."""
        quote: str | None = None
        i = start_index
        length = len(source)

        while i < length:
            ch = source[i]
            if quote:
                if ch == quote:
                    quote = None
            else:
                if ch == '"' or ch == "'":
                    quote = ch
                elif ch == ">":
                    return i
            i += 1

        return -1

    @classmethod
    def _extract_numeric_href_anchors(cls, source: str) -> list[tuple[int, str]]:
        """Extract (item_id, anchor_text) for anchors like <a href=\"123\">...</a>."""
        anchors: list[tuple[int, str]] = []

        for match in re.finditer(r'<a\b[^>]*\bhref="(\d+)"', source, re.IGNORECASE):
            item_id = int(match.group(1))
            tag_start = match.start()
            open_end = cls._find_tag_open_end(source, tag_start)
            if open_end == -1:
                continue

            close_tag = source.find("</a>", open_end + 1)
            if close_tag == -1:
                continue

            inner_html = source[open_end + 1:close_tag]
            text = cls._strip_html_text(inner_html)
            if text:
                anchors.append((item_id, text))

        return anchors

    async def eriones_search(self, name: str, lang: str = "jp") -> int | None:
        """Search eriones.com and return the best matching item ID."""
        url = ERIONES_SEARCH_EN if lang == "en" else ERIONES_SEARCH_JP
        ssl_verify = lang != "en"
        params = {"i": name, "il": "1-275", "img": "on"}
        async with self.session.get(url, params=params, ssl=ssl_verify) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(encoding="utf-8", errors="ignore")

        # Search results contain multiple duplicate links per item (icon + text).
        # Capture all numeric href item links and rank by name similarity.
        raw_matches = self._extract_numeric_href_anchors(html)
        candidates: list[tuple[int, str]] = []
        seen_ids: set[int] = set()

        for item_id, clean_name in raw_matches:
            if not re.search(r"[A-Za-z0-9\u3040-\u30ff\u4e00-\u9faf]", clean_name):
                continue

            if item_id in seen_ids:
                continue

            seen_ids.add(item_id)
            candidates.append((item_id, clean_name))

        if not candidates:
            return None

        best_id, _ = min(candidates, key=lambda c: self._match_priority(name, c[1]))
        return best_id

    async def eriones_item(self, item_id: int, lang: str = "jp") -> dict:
        """Fetch item details from eriones.com (lang='jp') or en.eriones.com (lang='en').
        en.eriones.com uses ssl=False because their certificate has expired."""
        base = ERIONES_EN if lang == "en" else ERIONES_JP
        url = f"{base}/{item_id}"
        ssl_verify = lang != "en"  # en.eriones.com has an expired cert
        async with self.session.get(url, ssl=ssl_verify) as resp:
            if resp.status != 200:
                return {}
            html = await resp.text(encoding="utf-8", errors="ignore")
        return self._parse_eriones_page(html, lang=lang)

    @staticmethod
    def _strip_html_text(value: str | None) -> str | None:
        if not value:
            return None

        parser = _VisibleTextExtractor()
        parser.feed(value)
        parser.close()

        normalized = html_lib.unescape(parser.get_text()).strip()
        return normalized or None

    @classmethod
    def _parse_eriones_page(cls, html: str, lang: str = "jp") -> dict:
        result = {}

        # First h2 contains the primary localized name and a secondary name in <small>.
        h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
        if h2_match:
            h2_html = h2_match.group(1)
            anchors = cls._extract_numeric_href_anchors(h2_html)
            small_match = re.search(r"<small[^>]*>(.*?)</small>", h2_html, re.IGNORECASE | re.DOTALL)

            primary_name = anchors[0][1] if anchors else None
            secondary_name = cls._strip_html_text(small_match.group(1)) if small_match else None

            if lang == "en":
                result["name"] = primary_name or secondary_name
            else:
                result["name"] = primary_name or secondary_name

            if secondary_name:
                result["alt_name"] = secondary_name

        # Fallback for older layouts that still expose item name as the second h3.
        if not result.get("name"):
            all_h3 = re.findall(r'<h3[^>]*>([^<]+)</h3>', html)
            if len(all_h3) >= 2:
                result["name"] = all_h3[1].strip()

        ilvl_match = re.search(r'(?:アイテムレベル|Item level)[：:]\s*(\d+)', html, re.IGNORECASE)
        if ilvl_match:
            result["ilvl"] = ilvl_match.group(1)
        rlv_match = re.search(r'(?:装備レベル|Equip level)[：:]\s*(\d+)', html, re.IGNORECASE)
        if rlv_match:
            result["rlv"] = rlv_match.group(1)
        icon_match = re.search(r'src="(//cdn\.eriones\.com/img/icon/ls_nq/[^"]+)"', html)
        if icon_match:
            result["icon"] = f"https:{icon_match.group(1)}"
        cat_match = re.search(r'db_view\?cid=\d+">([^<]+)</a>', html)
        if cat_match:
            result["category"] = cat_match.group(1).strip()

        result.update(cls._parse_eriones_stats_from_text(html))
        return result

    @classmethod
    def _normalize_eriones_text(cls, html: str) -> str:
        text = cls._strip_html_text(html) or ""
        text = text.translate(cls.FULLWIDTH_TRANSLATION)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _extract_named_stat(cls, text: str, labels: list[str], *, signed: bool = False) -> str | None:
        value_pattern = r"([+\-]?\d+(?:\(\d+\))?)" if signed else r"(\d+(?:\(\d+\))?)"
        for label in labels:
            pattern = rf"{re.escape(label)}\s*:?\s*{value_pattern}"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @classmethod
    def _extract_stat_pair(cls, text: str, labels: list[str]) -> str | None:
        return cls._extract_named_stat(text, labels, signed=True)

    @classmethod
    def _extract_class_name(cls, text: str) -> str | None:
        patterns = [
            r"Class\s*:?\s*([A-Z]{2,3}(?:\s+[A-Z]{2,3})+|[A-Z]{2,3})",
            r"クラス\s*:?\s*([^\-]+?)(?:\s+Sale\s+price|\s+Category|\s+Item\s+level|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip(" -")
                value = re.sub(r"\s+", " ", value)
                if value:
                    return value
        return None

    @classmethod
    def _equipment_slot_from_category(cls, category: str | None) -> str | None:
        if not category:
            return None
        lowered = category.lower()
        for keyword, slot in cls.EQUIPMENT_SLOT_KEYWORDS.items():
            if keyword in lowered:
                return slot
        return None

    @classmethod
    def _parse_eriones_stats_from_text(cls, html: str) -> dict:
        text = cls._normalize_eriones_text(html)
        if not text:
            return {}

        stats: dict[str, str] = {}

        ilvl = cls._extract_named_stat(text, ["Item level", "アイテムレベル"])
        if ilvl:
            stats["ilvl"] = ilvl

        rlv = cls._extract_named_stat(text, ["Equip Level", "装備レベル"])
        if rlv:
            stats["rlv"] = rlv

        class_name = cls._extract_class_name(text)
        if class_name:
            stats["class"] = class_name

        labeled_stats = [
            ("Defense", ["Defense", "防御力"], False),
            ("Magic Defense", ["Magic Defense", "魔法防御力"], False),
            ("Physical Damage", ["Physical Damage", "物理攻撃力"], False),
            ("Auto-Attack", ["Auto-Attack", "オートアタック"], False),
            ("Delay", ["Delay", "攻撃間隔"], False),
            ("Block Strength", ["Block Strength", "受け流し発動力"], False),
            ("Block Rate", ["Block Rate", "受け流し発動率"], False),
            ("Craftsmanship", ["Craftsmanship", "作業精度"], True),
            ("Control", ["Control", "加工精度"], True),
            ("CP", ["CP", "クラフターCP", "クラフターＣＰ"], True),
            ("STR", ["STR", "Strength"], True),
            ("DEX", ["DEX", "Dexterity"], True),
            ("VIT", ["VIT", "Vitality"], True),
            ("INT", ["INT", "Intelligence"], True),
            ("MND", ["MND", "Mind"], True),
            ("CRT", ["CRT", "Critical Hit"], True),
            ("DET", ["DET", "Determination"], True),
            ("DH", ["DH", "Direct Hit"], True),
            ("SKS", ["SKS", "Skill Speed"], True),
            ("SPS", ["SPS", "Spell Speed"], True),
            ("TEN", ["TEN", "Tenacity"], True),
            ("PIE", ["PIE", "Piety"], True),
        ]

        for key, labels, signed in labeled_stats:
            value = cls._extract_named_stat(text, labels, signed=signed)
            if value:
                stats[key] = value.replace(" ", "")

        return stats

    @classmethod
    def _format_equipment_stats(cls, item: dict, input_language: str = "en") -> str | None:
        lines = []
        class_name = item.get("class")
        if class_name:
            lines.append(f"Class: {class_name}")

        ordered_keys = [
            "Defense",
            "Magic Defense",
            "Physical Damage",
            "Auto-Attack",
            "Delay",
            "Block Strength",
            "Block Rate",
            "Craftsmanship",
            "Control",
            "CP",
            "STR",
            "DEX",
            "VIT",
            "INT",
            "MND",
            "CRT",
            "DET",
            "DH",
            "SKS",
            "SPS",
            "TEN",
            "PIE",
        ]

        for key in ordered_keys:
            value = item.get(key)
            if value:
                if key == "Craftsmanship":
                    if input_language == "en":
                        lines.append(f"Craftsmanship: {value}")
                    else:
                        lines.append(f"Craftsmanship (作業精度): {value}")
                elif key == "Control":
                    if input_language == "en":
                        lines.append(f"Control: {value}")
                    else:
                        lines.append(f"Control (加工精度): {value}")
                elif key == "CP":
                    if input_language == "en":
                        lines.append(f"CP: {value}")
                    else:
                        lines.append(f"CP (クラフターCP): {value}")
                else:
                    lines.append(f"{key}: {value}")

        if not lines:
            return None

        text = "\n".join(lines)
        return text[:1021] + "..." if len(text) > 1024 else text

    @staticmethod
    def _clean_item_name(name: str | None) -> str | None:
        if not name:
            return None
        normalized = name.strip()
        if not normalized:
            return None

        # Ignore section header placeholders returned by some eriones page layouts.
        lower = normalized.lower()
        condensed = re.sub(r"\s+", " ", lower)
        if (
            "item information" in condensed
            or "アイテム情報" in normalized
        ):
            return None
        return normalized

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
        help="Search for an FFXIV item by name (English/Japanese) via eriones.com",
        description="Command: !item <name>",
        brief="Search for an FFXIV item"
    )
    async def item_search(self, ctx: commands.Context, *, name: str):
        query_name = name.strip()

        if not query_name:
            await ctx.send("Please provide an item name. Usage: `!item [short|--short] <name>`")
            return

        detected_lang = self.detect_language(query_name)
        cache_key = f"item:eriones:v2:{query_name.lower()}"
        item_id = self.cache.get(cache_key)

        if item_id is None:
            item_id = await self.eriones_search(query_name, lang=detected_lang)
            if item_id:
                self.cache.set(cache_key, item_id)

        if not item_id:
            await ctx.send("No items found.")
            return

        # Fetch EN/JP details from Eriones only.
        en_item, jp_item = await asyncio.gather(
            self.eriones_item(item_id, lang="en"),
            self.eriones_item(item_id, lang="jp"),
        )

        en_name = (
            self._clean_item_name(en_item.get("name"))
            or self._clean_item_name(jp_item.get("name"))
            or "Unknown Item"
        )
        jp_name = (
            self._clean_item_name(jp_item.get("name"))
            or self._clean_item_name(en_item.get("name"))
            or "N/A"
        )

        embed = discord.Embed(
            title=en_name,
            url=f"{ERIONES_EN}/{item_id}",
            color=discord.Color.blurple()
        )

        icon_url = en_item.get("icon") or jp_item.get("icon")
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        embed.add_field(name="English", value=en_name, inline=False)
        embed.add_field(name="Japanese", value=jp_name, inline=False)
        embed.add_field(name="Item Level", value=jp_item.get("ilvl") or en_item.get("ilvl") or "N/A")
        embed.add_field(name="Required Level", value=jp_item.get("rlv") or en_item.get("rlv") or "N/A")

        category = en_item.get("category") or jp_item.get("category")
        if category:
            embed.add_field(name="Category", value=category)

        equipment_slot = self._equipment_slot_from_category(category)
        if equipment_slot:
            embed.add_field(name="Equipment Slot", value=equipment_slot)

        equipment_stats = self._format_equipment_stats(en_item, input_language=detected_lang)
        if equipment_stats:
            stats_field_name = "Equipment Stats" if detected_lang == "en" else "装備ステータス"
            embed.add_field(name=stats_field_name, value=equipment_stats, inline=False)

        embed.add_field(name="Detected Input Language", value=detected_lang.upper())
        embed.set_footer(text="Data from eriones.com")

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
