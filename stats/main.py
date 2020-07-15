# -*- coding: utf-8 -*-
# Standard Library
import datetime

from collections import Counter, defaultdict

# Cog Dependencies
from types import SimpleNamespace

import discord
import lavalink

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, humanize_number, humanize_timedelta

_ = lambda s: s


class Stats(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.__version__ = "Nope"

        if hasattr(self.bot, "stats"):
            if not hasattr(self.bot.stats, "guilds"):
                self.bot.stats.guilds = SimpleNamespace()
            if not hasattr(self.bot.stats, "bot"):
                self.bot.stats.bot = SimpleNamespace()
            if not hasattr(self.bot.stats, "shards"):
                self.bot.stats.shards = SimpleNamespace()
            if not hasattr(self.bot.stats, "audio"):
                self.bot.stats.audio = SimpleNamespace()
            if not hasattr(self.bot.stats, "currency"):
                self.bot.stats.currency = SimpleNamespace()
            if not hasattr(self.bot.stats, "guilds_regions"):
                self.bot.stats.guilds_regions = SimpleNamespace()
            if not hasattr(self.bot.stats, "guild_features"):
                self.bot.stats.guild_features = SimpleNamespace()
            if not hasattr(self.bot.stats, "guild_verification"):
                self.bot.stats.guild_verification = SimpleNamespace()
            if not hasattr(self.bot.stats, "adventure"):
                self.bot.stats.adventure = SimpleNamespace()

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def botinfo(self, ctx: commands.Context):
        """Show bot information.

        `details`: Shows more information when set to `True`.
        Default to False.
        """
        async with ctx.typing():
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
                "EU West": _("EU West ") + "\U0001F1EA\U0001F1FA",
                "EU Central": _("EU Central ") + "\U0001F1EA\U0001F1FA",
                "Europe": _("Europe ") + "\U0001F1EA\U0001F1FA",
                "London": _("London ") + "\U0001F1EC\U0001F1E7",
                "Frankfurt": _("Frankfurt ") + "\U0001F1E9\U0001F1EA",
                "Amsterdam": _("Amsterdam ") + "\U0001F1F3\U0001F1F1",
                "US West": _("US West ") + "\U0001F1FA\U0001F1F8",
                "US East": _("US East ") + "\U0001F1FA\U0001F1F8",
                "US South": _("US South ") + "\U0001F1FA\U0001F1F8",
                "US Central": _("US Central ") + "\U0001F1FA\U0001F1F8",
                "Singapore": _("Singapore ") + "\U0001F1F8\U0001F1EC",
                "Sydney": _("Sydney ") + "\U0001F1E6\U0001F1FA",
                "Brazil": _("Brazil ") + "\U0001F1E7\U0001F1F7",
                "Hong Kong": _("Hong Kong ") + "\U0001F1ED\U0001F1F0",
                "Russia": _("Russia ") + "\U0001F1F7\U0001F1FA",
                "Japan": _("Japan ") + "\U0001F1EF\U0001F1F5",
                "South Africa": _("South Africa ") + "\U0001F1FF\U0001F1E6",
                "India": _("India ") + "\U0001F1EE\U0001F1F3",
                "Dubai": _("Dubai ") + "\U0001F1E6\U0001F1EA",
                "South Korea": _("South Korea ") + "\U0001f1f0\U0001f1f7",
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
                "ENABLED_DISCOVERABLE_BEFORE": _("Was in Server Discovery"),
                "WELCOME_SCREEN_ENABLED": _("Welcome Screen"),
            }
            audio_cog = self.bot.get_cog("Audio")
            bot_has_stats = getattr(self.bot, "stats", None)
            if not bot_has_stats:
                counter = Counter()
                counter["guild_count"] = len(self.bot.guilds)
                counter["active_music_players"] = len(lavalink.active_players())
                counter["total_music_players"] = len(lavalink.all_players())
                counter["inactive_music_players"] = (
                    counter["total_music_players"] - counter["active_music_players"]
                )

                counter["discord_latency"] = int(round(self.bot.latency * 1000))
                counter["shards"] = self.bot.shard_count
                temp_data = defaultdict(set)
                region_count = Counter()
                verif_count = Counter()
                features_count = Counter()
                async for s in AsyncIter(self.bot.guilds, steps=1000, delay=0):
                    if s.unavailable:
                        temp_data["unavailable"].add(s.id)
                        continue

                    async for f in AsyncIter(s.features, steps=1000, delay=0):
                        features_count[f] += 1

                    verif_count[f"{s.verification_level}"] += 1
                    region_count[f"{s.region}"] += 1
                    counter["channel_categories_count"] += len(s.categories)
                    counter["guild_channel_count"] += len(s.channels)
                    counter["guild_text_channel_count"] += len(s.text_channels)
                    counter["guild_voice_channel_count"] += len(s.voice_channels)
                    counter["role_count"] += len(s.roles)
                    counter["emoji_count"] += len(s.emojis)

                    if s.large:
                        temp_data["large_guilds"].add(s.id)
                    if not s.chunked:
                        temp_data["not_chunked_guilds"].add(s.id)
                    if s.premium_tier != 0:
                        temp_data["boosted_servers"].add(s.id)

                    if s.premium_tier == 1:
                        temp_data["tier_1_count"].add(s.id)
                    elif s.premium_tier == 2:
                        temp_data["tier_2_count"].add(s.id)
                    elif s.premium_tier == 3:
                        temp_data["tier_3_count"].add(s.id)

                    async for c in AsyncIter(s.text_channels, steps=1000, delay=0):
                        if c.is_nsfw():
                            temp_data["nsfw_text_channel_count"].add(c.id)
                        if c.is_news():
                            temp_data["news_text_channel_count"].add(c.id)
                        if c.type is discord.ChannelType.store:
                            temp_data["store_text_channel_count"].add(c.id)

                    async for vc in AsyncIter(s.voice_channels, steps=1000, delay=0):
                        counter["user_voice_channel_count"] += len(vc.members)

                        if s.me in vc.members:
                            counter["user_voice_channel_with_me_count"] += len(vc.members) - 1

                        async for vcm in AsyncIter(vc.members, steps=1000, delay=0):
                            if vcm.is_on_mobile():
                                temp_data["user_voice_channel_mobile_count"].add(vcm.id)

                    async for e in AsyncIter(s.emojis, steps=1000, delay=0):
                        if e.animated:
                            counter["animated_emojis"] += 1
                        else:
                            counter["static_emojis"] += 1

                    async for m in AsyncIter(s.members, steps=1000, delay=0):
                        if m.bot:
                            temp_data["bots"].add(m.id)
                        else:
                            temp_data["humans"].add(m.id)

                        temp_data["unique_user"].add(m.id)
                        if m.is_on_mobile():
                            temp_data["mobile_users"].add(m.id)
                        streaming = False

                        async for a in AsyncIter(m.activities, steps=1000, delay=0):
                            if a.type is discord.ActivityType.streaming:
                                temp_data["streaming_users"].add(m.id)
                                if m.bot:
                                    temp_data["streaming_bots"].add(m.id)
                                else:
                                    temp_data["streaming_human"].add(m.id)
                                streaming = True
                            elif a.type is discord.ActivityType.playing:
                                temp_data["gaming_users"].add(m.id)
                                if m.bot:
                                    temp_data["gaming_bots"].add(m.id)
                                else:
                                    temp_data["gaming_human"].add(m.id)

                            if a.type is discord.ActivityType.listening:
                                temp_data["listening_users"].add(m.id)
                                if m.bot:
                                    temp_data["listening_bots"].add(m.id)
                                else:
                                    temp_data["listening_human"].add(m.id)
                            if a.type is discord.ActivityType.watching:
                                temp_data["watching_users"].add(m.id)
                                if m.bot:
                                    temp_data["watching_bots"].add(m.id)
                                else:
                                    temp_data["watching_human"].add(m.id)
                            if a.type is discord.ActivityType.custom:
                                temp_data["custom_users"].add(m.id)
                                if m.bot:
                                    temp_data["custom_bots"].add(m.id)
                                else:
                                    temp_data["custom_human"].add(m.id)

                        if not streaming:
                            if m.status is discord.Status.online:
                                temp_data["online_users"].add(m.id)
                                if m.bot:
                                    temp_data["online_bots"].add(m.id)
                                else:
                                    temp_data["online_human"].add(m.id)
                            elif m.status is discord.Status.idle:
                                temp_data["idle_users"].add(m.id)
                                if m.bot:
                                    temp_data["idle_bots"].add(m.id)
                                else:
                                    temp_data["idle_human"].add(m.id)
                            elif m.status is discord.Status.do_not_disturb:
                                temp_data["do_not_disturb_users"].add(m.id)
                                if m.bot:
                                    temp_data["do_not_disturb_bots"].add(m.id)
                                else:
                                    temp_data["do_not_disturb_human"].add(m.id)
                            elif m.status is discord.Status.offline:
                                temp_data["offline_users"].add(m.id)
                                if m.bot:
                                    temp_data["offline_bots"].add(m.id)
                                else:
                                    temp_data["offline_human"].add(m.id)

                        if m.mobile_status is discord.Status.online:
                            temp_data["mobile_online_users"].add(m.id)
                        elif m.mobile_status is discord.Status.idle:
                            temp_data["mobile_idle_users"].add(m.id)
                        elif m.mobile_status is discord.Status.do_not_disturb:
                            temp_data["mobile_do_not_disturb_users"].add(m.id)
                        elif m.mobile_status is discord.Status.offline:
                            temp_data["mobile_offline_users"].add(m.id)

                        if m.desktop_status is discord.Status.online:
                            temp_data["desktop_online_users"].add(m.id)
                        elif m.desktop_status is discord.Status.idle:
                            temp_data["desktop_idle_users"].add(m.id)
                        elif m.desktop_status is discord.Status.do_not_disturb:
                            temp_data["desktop_do_not_disturb_users"].add(m.id)
                        elif m.desktop_status is discord.Status.offline:
                            temp_data["desktop_offline_users"].add(m.id)

                        if m.web_status is discord.Status.online:
                            temp_data["web_online_users"].add(m.id)
                        elif m.web_status is discord.Status.idle:
                            temp_data["web_idle_users"].add(m.id)
                        elif m.web_status is discord.Status.do_not_disturb:
                            temp_data["web_do_not_disturb_users"].add(m.id)
                        elif m.web_status is discord.Status.offline:
                            temp_data["web_offline_users"].add(m.id)

                for key, value in temp_data.items():
                    counter[key] = len(value)

                online_stats = {
                    "\N{LARGE GREEN CIRCLE}": counter["online_users"],
                    "\N{LARGE ORANGE CIRCLE}": counter["idle_users"],
                    "\N{LARGE RED CIRCLE}": counter["do_not_disturb_users"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["offline_users"],
                    "\N{LARGE PURPLE CIRCLE}": counter["streaming_users"],
                    "\N{MOBILE PHONE}": counter["mobile_users"],
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": counter["streaming_users"],
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": counter["gaming_users"],
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": counter["listening_users"],
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": counter["watching_users"],
                    _("Custom"): counter["custom_users"],
                }
                online_stats_web = {
                    "\N{LARGE GREEN CIRCLE}": counter["web_online_users"],
                    "\N{LARGE ORANGE CIRCLE}": counter["web_idle_users"],
                    "\N{LARGE RED CIRCLE}": counter["web_do_not_disturb_users"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["web_offline_users"],
                }
                online_stats_mobile = {
                    "\N{LARGE GREEN CIRCLE}": counter["mobile_online_users"],
                    "\N{LARGE ORANGE CIRCLE}": counter["mobile_idle_users"],
                    "\N{LARGE RED CIRCLE}": counter["mobile_do_not_disturb_users"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["mobile_offline_users"],
                }
                online_stats_desktop = {
                    "\N{LARGE GREEN CIRCLE}": counter["desktop_online_users"],
                    "\N{LARGE ORANGE CIRCLE}": counter["desktop_idle_users"],
                    "\N{LARGE RED CIRCLE}": counter["desktop_do_not_disturb_users"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["desktop_offline_users"],
                }
                online_stats_bots = {
                    "\N{LARGE GREEN CIRCLE}": counter["online_bots"],
                    "\N{LARGE ORANGE CIRCLE}": counter["idle_bots"],
                    "\N{LARGE RED CIRCLE}": counter["do_not_disturb_bots"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["offline_bots"],
                    "\N{LARGE PURPLE CIRCLE}": counter["streaming_bots"],
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": counter["streaming_bots"],
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": counter["gaming_bots"],
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": counter["listening_bots"],
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": counter["watching_bots"],
                    _("Custom"): counter["custom_bots"],
                }
                online_stats_humans = {
                    "\N{LARGE GREEN CIRCLE}": counter["online_human"],
                    "\N{LARGE ORANGE CIRCLE}": counter["idle_human"],
                    "\N{LARGE RED CIRCLE}": counter["do_not_disturb_human"],
                    "\N{MEDIUM WHITE CIRCLE}": counter["offline_human"],
                    "\N{LARGE PURPLE CIRCLE}": counter["streaming_human"],
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": counter["streaming_human"],
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": counter["gaming_human"],
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": counter["listening_human"],
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": counter["watching_human"],
                    _("Custom"): counter["custom_human"],
                }
            else:
                online_stats = {
                    "\N{LARGE GREEN CIRCLE}": getattr(self.bot.stats.bot, "Users Online", 0),
                    "\N{LARGE ORANGE CIRCLE}": getattr(self.bot.stats.bot, "Idle Users", 0),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Users in Do Not Disturb", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(self.bot.stats.bot, "Users Offline", 0),
                    "\N{LARGE PURPLE CIRCLE}": getattr(self.bot.stats.bot, "Users Streaming", 0),
                    "\N{MOBILE PHONE}": getattr(self.bot.stats.bot, "Users Online on Mobile", 0),
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Users Streaming", 0
                    ),
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Users Gaming", 0
                    ),
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Users Listening", 0
                    ),
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Users Watching", 0
                    ),
                    _("Custom"): getattr(self.bot.stats.bot, "Users with Custom Status", 0),
                }
                online_stats_web = {
                    "\N{LARGE GREEN CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Online on Browser", 0
                    ),
                    "\N{LARGE ORANGE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Idle on Browser", 0
                    ),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Users in Do Not Disturb on Browser", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Offline on Browser", 0
                    ),
                }
                online_stats_mobile = {
                    "\N{LARGE GREEN CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Online on Mobile", 0
                    ),
                    "\N{LARGE ORANGE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Idle on Mobile", 0
                    ),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Users in Do Not Disturb on Mobile", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Offline on Mobile", 0
                    ),
                }
                online_stats_desktop = {
                    "\N{LARGE GREEN CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Online on Desktop", 0
                    ),
                    "\N{LARGE ORANGE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Idle on Desktop", 0
                    ),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Users in Do Not Disturb on Desktop", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(
                        self.bot.stats.bot, "Users Offline on Desktop", 0
                    ),
                }
                online_stats_bots = {
                    "\N{LARGE GREEN CIRCLE}": getattr(self.bot.stats.bot, "Bots Online", 0),
                    "\N{LARGE ORANGE CIRCLE}": getattr(self.bot.stats.bot, "Idle Bots", 0),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Bots in Do Not Disturb", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(self.bot.stats.bot, "Bots Offline", 0),
                    "\N{LARGE PURPLE CIRCLE}": getattr(self.bot.stats.bot, "Bots Streaming", 0),
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Bots Streaming", 0
                    ),
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Bots Gaming", 0
                    ),
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Bots Listening", 0
                    ),
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Bots Watching", 0
                    ),
                    _("Custom"): getattr(self.bot.stats.bot, "Bots with Custom Status", 0),
                }
                online_stats_humans = {
                    "\N{LARGE GREEN CIRCLE}": getattr(self.bot.stats.bot, "Humans Online", 0),
                    "\N{LARGE ORANGE CIRCLE}": getattr(self.bot.stats.bot, "Idle Humans", 0),
                    "\N{LARGE RED CIRCLE}": getattr(
                        self.bot.stats.bot, "Humans in Do Not Disturb", 0
                    ),
                    "\N{MEDIUM WHITE CIRCLE}": getattr(self.bot.stats.bot, "Humans Offline", 0),
                    "\N{LARGE PURPLE CIRCLE}": getattr(self.bot.stats.bot, "Humans Streaming", 0),
                    "\N{CLAPPER BOARD}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Humans Streaming", 0
                    ),
                    "\N{VIDEO GAME}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Humans Gaming", 0
                    ),
                    "\N{HEADPHONE}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Humans Listening", 0
                    ),
                    "\N{TELEVISION}\N{VARIATION SELECTOR-16}": getattr(
                        self.bot.stats.bot, "Humans Watching", 0
                    ),
                    _("Custom"): getattr(self.bot.stats.bot, "Humans with Custom Status", 0),
                }

        since = self.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or _("Less than one second")
        description = _("Uptime: **{time_quantity}** (since {timestamp} UTC)").format(
            time_quantity=uptime_str, timestamp=since
        )
        data = discord.Embed(description=description, colour=await ctx.embed_colour(),)

        data.set_author(name=str(ctx.me), icon_url=ctx.me.avatar_url)
        if not bot_has_stats:
            member_msg = _(
                "Users online: {online}/{total_users}\nHumans: {humans}\nBots: {bots}\n"
            ).format(
                online=bold(humanize_number(counter["online_users"])),
                total_users=bold(humanize_number(counter["unique_user"])),
                humans=bold(humanize_number(counter["humans"])),
                bots=bold(humanize_number(counter["bots"])),
            )
        else:
            member_msg = _(
                "Users online: {online}/{total_users}\nHumans: {humans}\nBots: {bots}\n"
            ).format(
                online=bold(humanize_number(getattr(self.bot.stats.bot, "Users Online", 0))),
                total_users=bold(humanize_number(getattr(self.bot.stats.bot, "Unique Users", 0))),
                humans=bold(humanize_number(getattr(self.bot.stats.bot, "Humans Online", 0))),
                bots=bold(humanize_number(getattr(self.bot.stats.bot, "Bots Online", 0))),
            )
        count = 1
        for emoji, value in online_stats.items():
            member_msg += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        if not bot_has_stats:
            data.add_field(
                name=_("General:"),
                value=_(
                    "Servers: {total}\n"
                    "Discord latency: {lat}ms\n"
                    "Shard count: {shards}\n"
                    "Large servers: {large}\n"
                    "Unchunked servers: {chuncked}\n"
                    "Unavailable servers: {unavaliable}\n"
                ).format(
                    lat=bold(humanize_number(counter["discord_latency"])),
                    shards=bold(humanize_number(counter["shards"])),
                    total=bold(humanize_number(counter["guild_count"])),
                    large=bold(humanize_number(counter["large_guilds"])),
                    chuncked=bold(humanize_number(counter["not_chunked_guilds"])),
                    unavaliable=bold(humanize_number(counter["unavaliable_guilds"])),
                ),
            )
        else:
            data.add_field(
                name=_("General:"),
                value=_(
                    "Servers: {total}\n"
                    "Discord latency: {lat}ms\n"
                    "Shard count: {shards}\n"
                    "Large servers: {large}\n"
                    "Unchunked servers: {chuncked}\n"
                    "Unavailable servers: {unavaliable}\n"
                ).format(
                    lat=bold(humanize_number(getattr(self.bot.stats.bot, "Discord Latency", 0))),
                    shards=bold(humanize_number(getattr(self.bot.stats.bot, "Shards", 0))),
                    total=bold(humanize_number(getattr(self.bot.stats.guilds, "Total", 0))),
                    large=bold(humanize_number(getattr(self.bot.stats.guilds, "Large", 0))),
                    chuncked=bold(humanize_number(getattr(self.bot.stats.guilds, "Unchunked", 0))),
                    unavaliable=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Unavailable", 0))
                    ),
                ),
            )
        verif_data = ""
        if not bot_has_stats:
            for r, value in sorted(verif_count.items(), reverse=False):
                if value:
                    verif_data += f"{bold(humanize_number(value))} - {verif.get(r)}\n"
        else:
            for k, value in sorted(
                self.bot.stats.guild_verification.__dict__.items(), reverse=False
            ):
                if value:
                    verif_data += f"{bold(humanize_number(value))} - {k}\n"
        if verif_data:
            data.add_field(name=_("Server Verification:"), value=verif_data)
        if not bot_has_stats:
            data.add_field(
                name=_("Nitro boosts:"),
                value=_(
                    "Total: {total}\n"
                    "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Level: {text}\n"
                    "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {voice}\n"
                    "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {users}"
                ).format(
                    total=bold(humanize_number(counter["boosted_servers"])),
                    text=bold(humanize_number(counter["tier_1_count"])),
                    voice=bold(humanize_number(counter["tier_2_count"])),
                    users=bold(humanize_number(counter["tier_3_count"])),
                ),
            )
        else:
            data.add_field(
                name=_("Nitro boosts:"),
                value=_(
                    "Total: {total}\n"
                    "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Level: {text}\n"
                    "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {voice}\n"
                    "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} Levels: {users}"
                ).format(
                    total=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Nitro Boosted", 0))
                    ),
                    text=bold(humanize_number(getattr(self.bot.stats.guilds, "Tier 1 Nitro", 0))),
                    voice=bold(humanize_number(getattr(self.bot.stats.guilds, "Tier 2 Nitro", 0))),
                    users=bold(humanize_number(getattr(self.bot.stats.guilds, "Tier 3 Nitro", 0))),
                ),
            )
        if not bot_has_stats:
            data.add_field(
                name=_("Channels:"),
                value=_(
                    "\N{SPEECH BALLOON} \N{SPEAKER WITH THREE SOUND WAVES} Total Channels: {total}\n"
                    "\N{BOOKMARK TABS} Categories: {categories}\n"
                    "\N{SPEECH BALLOON} Text Channels: {text}\n"
                    "\N{MONEY BAG} Store Channels: {store}\n"
                    "\N{NO ONE UNDER EIGHTEEN SYMBOL} NSFW Channels: {nsfw}\n"
                    "\N{NEWSPAPER} News Channels: {news}\n"
                    "\N{SPEAKER WITH THREE SOUND WAVES} Voice Channels: {voice}\n"
                    "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC: {users}\n"
                    "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16}\N{MOBILE PHONE} Users in VC on Mobile: {users_mobile}\n"
                    "\N{ROBOT FACE}\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC with me: {with_me}\n"
                ).format(
                    store=bold(humanize_number(counter["store_text_channel_count"])),
                    nsfw=bold(humanize_number(counter["nsfw_text_channel_count"])),
                    news=bold(humanize_number(counter["news_text_channel_count"])),
                    users_mobile=bold(humanize_number(counter["user_voice_channel_mobile_count"])),
                    total=bold(humanize_number(counter["guild_channel_count"])),
                    text=bold(humanize_number(counter["guild_text_channel_count"])),
                    voice=bold(humanize_number(counter["guild_voice_channel_count"])),
                    users=bold(humanize_number(counter["user_voice_channel_count"])),
                    with_me=bold(humanize_number(counter["user_voice_channel_with_me_count"])),
                    categories=bold(humanize_number(counter["channel_categories_count"])),
                ),
            )
        else:
            data.add_field(
                name=_("Channels:"),
                value=_(
                    "\N{SPEECH BALLOON} \N{SPEAKER WITH THREE SOUND WAVES} Total Channels: {total}\n"
                    "\N{BOOKMARK TABS} Categories: {categories}\n"
                    "\N{SPEECH BALLOON} Text Channels: {text}\n"
                    "\N{MONEY BAG} Store Channels: {store}\n"
                    "\N{NO ONE UNDER EIGHTEEN SYMBOL} NSFW Channels: {nsfw}\n"
                    "\N{NEWSPAPER} News Channels: {news}\n"
                    "\N{SPEAKER WITH THREE SOUND WAVES} Voice Channels: {voice}\n"
                    "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC: {users}\n"
                    "\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16}\N{MOBILE PHONE} Users in VC on Mobile: {users_mobile}\n"
                    "\N{ROBOT FACE}\N{STUDIO MICROPHONE}\N{VARIATION SELECTOR-16} Users in VC with me: {with_me}\n"
                ).format(
                    store=bold(
                        humanize_number(getattr(self.bot.stats.bot, "Store Text Channels", 0))
                    ),
                    nsfw=bold(
                        humanize_number(getattr(self.bot.stats.bot, "NSFW Text Channels", 0))
                    ),
                    news=bold(
                        humanize_number(getattr(self.bot.stats.bot, "News Text Channels", 0))
                    ),
                    users_mobile=bold(
                        humanize_number(getattr(self.bot.stats.bot, "Users in a VC on Mobile", 0))
                    ),
                    total=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Server Channels", 0))
                    ),
                    text=bold(humanize_number(getattr(self.bot.stats.guilds, "Text Channels", 0))),
                    voice=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Voice Channels", 0))
                    ),
                    users=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Users in a VC", 0))
                    ),
                    with_me=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Users in a VC with me", 0))
                    ),
                    categories=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Channel Categories", 0))
                    ),
                ),
            )

        region_data = ""
        if not bot_has_stats:
            for r, value in sorted(region_count.items(), reverse=False):
                if value:
                    region_data += f"{bold(humanize_number(value))} - {vc_regions.get(r)}\n"
        else:
            for r, value in sorted(self.bot.stats.guilds_regions.__dict__.items(), reverse=False):
                if value:
                    region_data += f"{bold(humanize_number(value))} - {vc_regions.get(r)}\n"
        if region_data:
            data.add_field(name=_("Regions:"), value=region_data)

        features_data = ""
        if not bot_has_stats:
            for r, value in sorted(features_count.items(), reverse=False):
                if value:
                    features_data += f"{bold(humanize_number(value))} - {features.get(r) or r}\n"
        else:
            for k, value in sorted(self.bot.stats.guild_features.__dict__.items(), reverse=False):
                if value:
                    features_data += f"{bold(humanize_number(value))} - {k}\n"
        if features_data:
            data.add_field(name=_("Features:"), value=features_data)
        if not bot_has_stats:
            data.add_field(
                name=_("Misc:"),
                value=_(
                    "Total Roles: {total}\n"
                    "Total Custom Emojis: {emoji_count}\n"
                    "Total Animated Emojis: {animated_emoji}\n"
                    "Total Static Emojis: {static_emojis}\n"
                ).format(
                    total=bold(humanize_number(counter["role_count"])),
                    emoji_count=bold(humanize_number(counter["emoji_count"])),
                    animated_emoji=bold(humanize_number(counter["animated_emojis"])),
                    static_emojis=bold(humanize_number(counter["static_emojis"])),
                ),
            )
        else:
            data.add_field(
                name=_("Misc:"),
                value=_(
                    "Total Roles: {total}\n"
                    "Total Custom Emojis: {emoji_count}\n"
                    "Total Animated Emojis: {animated_emoji}\n"
                    "Total Static Emojis: {static_emojis}\n"
                    "Total Currency: {currency}\n"
                ).format(
                    total=bold(humanize_number(getattr(self.bot.stats.guilds, "Roles", 0))),
                    emoji_count=bold(humanize_number(getattr(self.bot.stats.guilds, "Emojis", 0))),
                    animated_emoji=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Animated Emojis", 0))
                    ),
                    static_emojis=bold(
                        humanize_number(getattr(self.bot.stats.guilds, "Static Emojis", 0))
                    ),
                    currency=bold(
                        humanize_number(
                            getattr(self.bot.stats.currency, "Currency In Circulation", 0)
                        )
                    ),
                ),
            )
        if member_msg:
            data.add_field(name=_("Members:"), value=member_msg)

        member_msg_web = ""
        count = 1
        for emoji, value in online_stats_web.items():
            member_msg_web += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        member_msg_mobile = ""
        count = 1
        for emoji, value in online_stats_mobile.items():
            member_msg_mobile += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        member_msg_desktop = ""
        count = 1
        for emoji, value in online_stats_desktop.items():
            member_msg_desktop += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        member_msg_bots = ""
        count = 1
        for emoji, value in online_stats_bots.items():
            member_msg_bots += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        member_msg_humans = ""
        count = 1
        for emoji, value in online_stats_humans.items():
            member_msg_humans += f"{emoji} {bold(humanize_number(value))} " + (
                "\n" if count % 2 == 0 else ""
            )
            count += 1
        if member_msg_humans:
            data.add_field(name=_("Human Statuses:"), value=member_msg_humans)
        if member_msg_bots:
            data.add_field(name=_("Bot Statuses:"), value=member_msg_bots)
        if member_msg_desktop:
            data.add_field(name=_("Desktop Statuses:"), value=member_msg_desktop)
        if member_msg_web:
            data.add_field(name=_("Web Statuses:"), value=member_msg_web)
        if member_msg_mobile:
            data.add_field(name=_("Mobile Statuses:"), value=member_msg_mobile)
        shard_latencies = ""
        count = 1
        for shard_id, latency in self.bot.latencies:
            shard_latencies += (
                f"Shard {shard_id + 1} - {bold(humanize_number(int(latency*1000)))}ms\n"
            )
            count += 1
        loaded = set(ctx.bot.extensions.keys())
        all_cogs = set(await self.bot._cog_mgr.available_modules())
        unloaded = all_cogs - loaded
        commands = list(self.bot.walk_commands())
        data.add_field(
            name=_("Bot Extensions:"),
            value=_(
                "Available Cogs: {cogs}\n"
                "Loaded Cogs: {loaded}\n"
                "Unloaded Cogs: {unloaded}\nCommands: {commands}"
            ).format(
                cogs=bold(humanize_number(len(all_cogs))),
                loaded=bold(humanize_number(len(loaded))),
                unloaded=bold(humanize_number(len(unloaded))),
                commands=bold(humanize_number(len(commands))),
            ),
        )
        if audio_cog and not bot_has_stats:
            data.add_field(
                name=_("Audio Stats:"),
                value=_(
                    "Total Players: {total}\n"
                    "Active Players: {active}\n"
                    "Inactive Players: {inactive}"
                ).format(
                    total=bold(humanize_number(counter["total_music_players"])),
                    active=bold(humanize_number(counter["active_music_players"])),
                    inactive=bold(humanize_number(counter["inactive_music_players"])),
                ),
            )
        elif audio_cog and bot_has_stats:
            data.add_field(
                name=_("Audio Stats:"),
                value=_(
                    "Total Players: {total}\n"
                    "Active Players: {active}\n"
                    "Inactive Players: {inactive}"
                ).format(
                    total=bold(humanize_number(getattr(self.bot.stats.audio, "Music Players"))),
                    active=bold(
                        humanize_number(getattr(self.bot.stats.audio, "Active Music Players"))
                    ),
                    inactive=bold(
                        humanize_number(getattr(self.bot.stats.audio, "Inactive Music Players"))
                    ),
                ),
            )
        if shard_latencies:
            data.add_field(name=_("Shard Latencies:"), value=shard_latencies)
        await ctx.send(embed=data)
