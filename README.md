# Discord Bot

A feature-rich Discord bot built with discord.py supporting prefix commands (`!` and `！`) and slash commands.

---

## Requirements

### Python Version

Python **3.10 or higher** is required (uses `str | None` union syntax).

### Python Dependencies

Install all dependencies with:

```bash
pip install discord.py aiohttp requests
```

| Package | Used For |
|---|---|
| `discord.py` (2.x) | Core bot framework, slash commands, cogs |
| `aiohttp` | Async HTTP requests in the FFXIV cog |
| `requests` | Weather API calls |

---

## Configuration Files

Before starting the bot, create the following files in the project root:

### `config.json`
Created automatically on first run. Fill in your bot token:
```json
{
    "Token": "YOUR_BOT_TOKEN_HERE",
    "Prefix": "！"
}
```

### `api_key.json`
Create this manually:
```json
{
    "api_key": "YOUR_OPENWEATHERMAP_API_KEY",
    "xivapi_key": "YOUR_XIVAPI_KEY"
}
```

- **OpenWeatherMap API key** — free tier at https://openweathermap.org/api
- **XIVAPI key** — obtain at https://xivapi.com (used for FFXIV commands)

---

## Starting the Bot

```bash
python DiscordBotPython.py
```

---

## Discord Bot Permissions

When inviting the bot to your server, it requires the following permissions:

### General Permissions
| Permission | Required For |
|---|---|
| Read Messages / View Channels | All commands |
| Send Messages | All commands |
| Embed Links | Weather, FFXIV, help, server, ping commands |
| Read Message History | Moderation clear command |
| Manage Messages | Deleting spam messages (anti-spam), clear command |

### Member Permissions
| Permission | Required For |
|---|---|
| Moderate Members (Timeout) | Anti-spam auto-mute |
| Kick Members | `!moderation kick` |
| Ban Members | `!moderation ban` |

### Recommended Permission Integer
Use **`1374891176023`** when generating your invite URL, or enable the permissions listed above manually in the Discord Developer Portal.

### Privileged Gateway Intents
In the [Discord Developer Portal](https://discord.com/developers/applications), under your bot's **Bot** settings, enable:

- **Server Members Intent** — required for moderation (kick/ban/timeout) and anti-spam
- **Message Content Intent** — required for prefix commands (`!`, `！`)

> Without Message Content Intent, prefix commands will not work at all.

---

## Commands Overview

All prefix commands support both `!` and `！` (full-width).

| Command | Description |
|---|---|
| `!help [ja]` | Shows all commands. Add `ja` for Japanese. |
| `!ping` | Responds with pong |
| `!pingme` | Shows your message latency |
| `!whoami` | Shows bot information |
| `!server` | Shows server information |
| `!eightball <question>` | Ask the magic 8-ball |
| `!math add/multiply/divide/minus/squareroot` | Math operations |
| `!weather currentweather <city> [state] [country]` | Current weather by city |
| `!weather city <city>` | Current weather (city only, supports Japanese city names) |
| `!moderation clear/kick/ban/unban` | Moderation tools (requires `moderator` role) |
| `!item <name>` | Search for an FFXIV item |
| `!translate_item <lang> <name>` | Translate an FFXIV item name |
| `!market <server> <item>` | FFXIV market board prices |
| `!tictactoe start/place/stop/finish` | Play tic-tac-toe |

### Anti-Spam (Automatic)
No command needed. The bot automatically monitors for members posting in **3 or more different channels within 30 seconds**. When triggered:
- All spam messages are deleted
- The member is timed out for 10 minutes
- The bot owner receives a DM with a full report

Members with Administrator, Manage Guild, or Manage Messages permissions are exempt.
