import asyncio
from typing import AsyncIterable, Sequence

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import bold, humanize_number
import lavalink

_ = lambda s: s


class AsyncGen(AsyncIterable):
    """Yield entry every `delay` seconds."""

    def __init__(self, contents: Sequence, delay: float = 0.0, steps: int = 500):
        self.delay = delay
        self.content = contents
        self.i = 0
        self.steps = steps
        self.to = len(contents)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.i >= self.to:
            raise StopAsyncIteration
        i = self.content[self.i]
        self.i += 1
        if self.i % self.steps == 0:
            await asyncio.sleep(self.delay)
        return i

class Stats(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def botinfo(self, ctx: commands.Context):
        """
        Show bot information.

        `details`: Shows more information when set to `True`.
        Default to False.
        """
        bot = ctx.bot
        async with ctx.typing():
            audio_cog = bot.get_cog("Audio")
            guild_count = len(bot.guilds)
            unique_user = set([m.id async for s in AsyncGen(bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable])
            large_guilds = len(set([s.id async for s in AsyncGen(bot.guilds) if not s.unavailable and s.large]))
            not_chunked_guilds = len(set([s.id async for s in AsyncGen(bot.guilds) if not s.unavailable and not s.chunked]))
            unavaliable_guilds = len(set([s.id async for s in AsyncGen(bot.guilds) if s.unavailable]))

            channel_categories_count = sum([len(s.categories) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])

            guild_channel_count = sum([len(s.channels) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])
            guild_text_channel_count = sum([len(s.text_channels) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])
            guild_voice_channel_count = sum([len(s.voice_channels) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])
            user_voice_channel_count = sum([len(c.members) async for s in AsyncGen(self.bot.guilds) async for c in AsyncGen(s.voice_channels) if not s.unavailable])
            user_voice_channel_with_me_count = sum([len(c.members) - 1 async for s in AsyncGen(self.bot.guilds) async for c in AsyncGen(s.voice_channels) if not s.unavailable and s.me in c.members])

            boosted_servers = len(set([s.id async for s in AsyncGen(self.bot.guilds) if not s.unavailable and s.premium_tier != 0]))
            tier_3_count = len(set([s.id async for s in AsyncGen(self.bot.guilds) if not s.unavailable and s.premium_tier == 3]))
            tier_1_count = len(set([s.id async for s in AsyncGen(self.bot.guilds) if not s.unavailable and s.premium_tier == 1]))
            tier_2_count = len(set([s.id async for s in AsyncGen(self.bot.guilds) if not s.unavailable and s.premium_tier == 2]))

            role_count = sum([len(s.roles) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])
            emoji_count = sum([len(s.emojis) async for s in AsyncGen(self.bot.guilds) if not s.unavailable])
            animated_emojis = sum([1 async for s in AsyncGen(self.bot.guilds) async for e in AsyncGen(s.emojis) if not s.unavailable and e.animated])
            static_emojis = emoji_count-animated_emojis
            if audio_cog:
                active_music_players = len(lavalink.active_players())
                total_music_players = len(lavalink.all_players())
            online_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and m.status is discord.Status.online])
            idle_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and m.status is discord.Status.idle])
            do_not_disturb_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and m.status is discord.Status.do_not_disturb])
            offline_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and m.status is discord.Status.offline])
            streaming_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) for a in m.activities if not s.unavailable and a.type is discord.ActivityType.streaming])
            online_users = online_users - streaming_users
            idle_users = idle_users - streaming_users
            do_not_disturb_users = do_not_disturb_users - streaming_users
            offline_users = offline_users - streaming_users
            gaming_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and discord.ActivityType.playing in [a.type for a in m.activities if a]])
            listening_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and discord.ActivityType.listening in [a.type for a in m.activities if a]])
            watching_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and discord.ActivityType.watching in [a.type for a in m.activities if a]])
            custom_users = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable and discord.ActivityType.custom in [a.type for a in m.activities if a]])

            humans = set([m.id async for s in AsyncGen(self.bot.guilds) async for m in AsyncGen(s.members) if not s.unavailable if not m.bot])
            bots = unique_user - humans
            discord_latency = int(round(bot.latency * 1000))
            shards = bot.shard_count
            online_stats = {
                _("Humans: "): len(humans),
                _(" • Bots: "): len(bots),
                "\N{LARGE GREEN CIRCLE}": len(online_users),
                "\N{LARGE ORANGE CIRCLE}": len(idle_users),
                "\N{LARGE RED CIRCLE}": len(do_not_disturb_users),
                "\N{MEDIUM WHITE CIRCLE}": len(offline_users),
                "\N{LARGE PURPLE CIRCLE}": len(streaming_users),
                "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": len(streaming_users),
                "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": len(gaming_users),
                "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": len(listening_users),
                "\N{TELEVISION}\N{VARIATION SELECTOR-16}": len(watching_users),
                _("Custom"): len(custom_users),

            }
            vc_regions = {
                "eu-west": _("EU West ") + "\U0001F1EA\U0001F1FA",
                "eu-central": _("EU Central ") + "\U0001F1EA\U0001F1FA",
                "europe": _("Europe ") + "\U0001F1EA\U0001F1FA",
                "london": _("London ") + "\U0001F1EC\U0001F1E7",
                "frankfurt": _("Frankfurt ") + "\U0001F1E9\U0001F1EA",
                "amsterdam": _("Amsterdam ") + "\U0001F1F3\U0001F1F1",
                "us-west": _("US West ") + "\U0001F1FA\U0001F1F8",
                "us-east": _("US East ") + "\U0001F1FA\U0001F1F8",
                "us-south": _("US South ") + "\U0001F1FA\U0001F1F8",
                "us-central": _("US Central ") + "\U0001F1FA\U0001F1F8",
                "singapore": _("Singapore ") + "\U0001F1F8\U0001F1EC",
                "sydney": _("Sydney ") + "\U0001F1E6\U0001F1FA",
                "brazil": _("Brazil ") + "\U0001F1E7\U0001F1F7",
                "hongkong": _("Hong Kong ") + "\U0001F1ED\U0001F1F0",
                "russia": _("Russia ") + "\U0001F1F7\U0001F1FA",
                "japan": _("Japan ") + "\U0001F1EF\U0001F1F5",
                "southafrica": _("South Africa ") + "\U0001F1FF\U0001F1E6",
                "india": _("India ") + "\U0001F1EE\U0001F1F3",
                "dubai": _("Dubai ") + "\U0001F1E6\U0001F1EA",
                "south-korea": _("South Korea ") + "\U0001f1f0\U0001f1f7",
            }
            verif = {
                "none": _("None"),
                "low": _("Low"),
                "medium": _("Medium"),
                "high": _("High"),
                "extreme": _("Extreme"),
            }
            features = {
                "VIP_REGIONS": _("VIP Voice Servers"),
                "VANITY_URL": _("Vanity URL"),
                "INVITE_SPLASH": _("Splash Invite"),
                "VERIFIED": _("Verified"),
                "PARTNERED": _("Partnered"),
                "MORE_EMOJI": _("More Emojis"),
                "DISCOVERABLE": _("Server Discovery"),
                "FEATURABLE": _("Featurable"),
                "COMMERCE": _("Commerce"),
                "PUBLIC": _("Public"),
                "NEWS": _("News Channels"),
                "BANNER": _("Banner Image"),
                "ANIMATED_ICON": _("Animated Icon"),
                "PUBLIC_DISABLED": _("Public disabled"),
                "MEMBER_LIST_DISABLED": _("Member list disabled"),
            }
            region_count = {}
            for k in vc_regions.keys():
                region_count[k] = sum([1 async for s in AsyncGen(self.bot.guilds) if not s.unavailable and f"{s.region}" == k])
            verif_count = {}
            for k in verif.keys():
                verif_count[k] = sum([1 async for s in AsyncGen(self.bot.guilds) if not s.unavailable and f"{s.verification_level}" == k])
            features_count = {}
            for k in features.keys():
                features_count[k] = sum(
                    [1 async for s in AsyncGen(self.bot.guilds) if not s.unavailable and k in s.features])

        data = discord.Embed(
            colour=await ctx.embed_colour(),
        )
        data.set_author(
            name=str(ctx.me),
            icon_url=ctx.me.avatar_url
        )
        member_msg = _("Users online: **{online}/{total_users}**\n").format(
            online=humanize_number(len(online_users)), total_users=humanize_number(len(unique_user))
        )
        count = 1
        for emoji, value in online_stats.items():
            member_msg += f"{emoji} {bold(humanize_number(value))} " + (
                    "\n" if count % 2 == 0 else ""
                )
            count += 1

        data.add_field(
            name=_("General:"),
            value=_(
                "Servers: {total}\n"
                "Discord latency: {lat}ms\n"
                "Shard count: {shards}\n"
                "Large Guilds: {large}\n"
                "Not Chunked Guilds: {chuncked}\n"
                "Unavailable Guilds: {unavaliable}\n"

            ).format(
                lat=bold(humanize_number(discord_latency)),
                shards=bold(humanize_number(shards)),
                total=bold(humanize_number(guild_count)),
                large=bold(humanize_number(large_guilds)),
                chuncked=bold(humanize_number(not_chunked_guilds)),
                unavaliable=bold(humanize_number(unavaliable_guilds))




            )
        )
        data.add_field(name=_("Members:"), value=member_msg)
        data.add_field(
            name=_("Channels:"),
            value=_(
                "\N{SPEECH BALLOON} \N{SPEAKER WITH THREE SOUND WAVES} Total: {total}\n"
                "\N{BOOKMARK TABS} Categories: {categories}\n"
                "\N{SPEECH BALLOON} Text: {text}\n"
                "\N{SPEAKER WITH THREE SOUND WAVES} Voice: {voice}\n"
                "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC: {users}\n"
                "\N{ROBOT FACE}\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC with me: {with_me}\n"
            ).format(total=bold(humanize_number(guild_channel_count)),
                     text=bold(humanize_number(guild_text_channel_count)),
                     voice=bold(humanize_number(guild_voice_channel_count)),
                     users=bold(humanize_number(user_voice_channel_count)),
                     with_me=bold(humanize_number(user_voice_channel_with_me_count)),
                     categories=bold(humanize_number(channel_categories_count))
                     )
        )
        region_data = ""
        for r, value in region_count.items():
            if value:
                region_data += f"{bold(humanize_number(value))} - {vc_regions.get(r)}\n"
        data.add_field(
            name=_("Regions:"),
            value=region_data
        )

        verif_data = ""
        for r, value in verif_count.items():
            if value:
                verif_data += f"{bold(humanize_number(value))} - {verif.get(r)}\n"
        data.add_field(
            name=_("Server Verification:"),
            value=verif_data
        )
        features_data = ""
        for r, value in features_count.items():
            if value:
                features_data += f"{bold(humanize_number(value))} - {features.get(r)}\n"
        data.add_field(
            name=_("Features:"),
            value=features_data
        )
        data.add_field(
            name=_("Nitro boosts:"),
            value=_(
                "Total: {total}\n"
                "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Level: {text}\n"
                "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {voice}\n"
                "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {users}"
            ).format(total=bold(humanize_number(boosted_servers)),
                     text=bold(humanize_number(tier_1_count)),
                     voice=bold(humanize_number(tier_2_count)),
                     users=bold(humanize_number(tier_3_count)))
        )
        data.add_field(
            name=_("Misc:"),
            value=_(
                "Total Roles: {total}\n"
                "Total Custom Emojis: {emoji_count}\n"
                "Total Animated Emojis: {animated_emoji}\n"
                "Total Static Emojis: {static_emojis}\n"

            ).format(total=bold(humanize_number(role_count)),
                     emoji_count=bold(humanize_number(emoji_count)),
                     animated_emoji=bold(humanize_number(animated_emojis)),
                     static_emojis=bold(humanize_number(static_emojis)))
        )
        if audio_cog:
            data.add_field(
                name=_("Audio Stats:"),
                value=_(
                    "Total Players: {total}\n"
                    "Active Players: {active}\n"
                    "Inactive Players: {inactive}"

                ).format(total=bold(humanize_number(total_music_players)),
                         active=bold(humanize_number(active_music_players)),
                         inactive=bold(humanize_number(total_music_players-active_music_players)))
            )
        await ctx.send(embed=data)


