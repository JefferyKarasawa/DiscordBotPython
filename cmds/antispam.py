import discord
from discord.ext import commands
from collections import defaultdict
import datetime


WINDOW_SECONDS = 30       # time window to track messages in
CHANNEL_THRESHOLD = 3     # unique channels within the window to trigger
TIMEOUT_DURATION = datetime.timedelta(minutes=10)


class AntiSpamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # {member_id: [{"message": msg, "time": datetime, "channel_id": int}]}
        self.tracker: dict[int, list] = defaultdict(list)
        # set of member IDs currently being actioned (prevents double-trigger)
        self.actioned: set[int] = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        member = message.author

        # skip members with elevated permissions (admins / moderators)
        if (
            member.guild_permissions.administrator
            or member.guild_permissions.manage_guild
            or member.guild_permissions.manage_messages
        ):
            return

        # skip if already being actioned
        if member.id in self.actioned:
            return

        now = datetime.datetime.now(datetime.timezone.utc)

        self.tracker[member.id].append({
            "message": message,
            "time": now,
            "channel_id": message.channel.id,
        })

        # prune entries outside the window
        self.tracker[member.id] = [
            e for e in self.tracker[member.id]
            if (now - e["time"]).total_seconds() <= WINDOW_SECONDS
        ]

        unique_channels = {e["channel_id"] for e in self.tracker[member.id]}

        if len(unique_channels) >= CHANNEL_THRESHOLD:
            spam_entries = self.tracker.pop(member.id, [])
            self.actioned.add(member.id)

            spam_messages = [e["message"] for e in spam_entries]
            channels_hit = len(unique_channels)

            # delete all spam messages
            for msg in spam_messages:
                try:
                    await msg.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

            # timeout the member
            muted = False
            try:
                await member.timeout(TIMEOUT_DURATION, reason="Automated: cross-channel spam detected")
                muted = True
            except discord.Forbidden:
                pass

            # DM the bot owner
            try:
                app_info = await self.bot.application_info()
                owner = app_info.owner
                embed = discord.Embed(
                    title="⚠️ Spam Detected",
                    color=discord.Color.red(),
                    timestamp=now,
                )
                embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
                embed.add_field(name="Server", value=message.guild.name, inline=False)
                embed.add_field(name="Channels Spammed", value=str(channels_hit), inline=True)
                embed.add_field(name="Messages Deleted", value=str(len(spam_messages)), inline=True)
                embed.add_field(
                    name="Action Taken",
                    value=f"Timed out for {int(TIMEOUT_DURATION.total_seconds() // 60)} minutes" if muted else "Could not mute (missing permissions)",
                    inline=False,
                )
                await owner.send(embed=embed)
            except Exception:
                pass

            # allow re-tracking after the timeout expires
            self.bot.loop.call_later(
                TIMEOUT_DURATION.total_seconds(),
                self.actioned.discard,
                member.id,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpamCog(bot))
