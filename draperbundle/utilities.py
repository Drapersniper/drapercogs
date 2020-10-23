# -*- coding: utf-8 -*-
import ast
import asyncio
import contextlib
import logging
import operator as op
import random
from calendar import day_name
from collections import namedtuple
from copy import copy
from datetime import date, datetime, timedelta, timezone
from typing import List, Sequence, Union, Tuple, Any
from urllib.parse import quote_plus

import aiohttp
import dateutil.parser
import discord

from pytz import UTC
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.predicates import MessagePredicate

from .country import WorldData
from .config_holder import ConfigHolder
from .constants import CONTINENT_DATA

logger = logging.getLogger("red.drapercogs.draperbundle.utils")
_START = "#"


def fmt_join(words: Sequence, ending: str = "or"):
    if not words:
        return ""
    elif len(words) == 1:
        return words[0]
    else:
        return "{} {} {}".format(", ".join(map(str, words[:-1])), ending, words[-1])


class Colour:
    def __init__(self, value):
        value = list(value)
        if len(value) != 3:
            raise ValueError("value must have a length of three")
        self._values = value

    def __str__(self):
        return _START + "".join("{:02X}".format(v) for v in self)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def __setitem__(self, index):
        return self._values[index]

    @staticmethod
    def from_string(string):
        colour = iter(string)
        if string[0] == _START:
            next(colour, None)
        return Colour(int("".join(v), 16) for v in zip(colour, colour))

    @staticmethod
    def hex_to_rgb(string):
        colour = iter(string)
        if string[0] == _START:
            next(colour, None)
        return tuple(int("".join(v), 16) for v in zip(colour, colour))

    @staticmethod
    def rgb_to_hex(r, g, b):
        return "#%02x%02x%02x" % (r, g, b)

    @staticmethod
    def random():
        return Colour(random.randrange(256) for _ in range(3))

    def contrast(self):
        return Colour(255 - v for v in self)


def list_filter(_list: list, what_to_remove: Union[str, int, bool] = None):
    return [x for x in _list if x != what_to_remove]


async def has_a_profile(member: discord.Member):
    if not member:
        return False
    if await ConfigHolder.GamingProfile.user(member).country():
        return True
    return False


async def get_website_data(url, headers=None):
    if not headers:
        headers = _header
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.read()
            return data


async def get_member(guild: discord.Guild, member):
    if isinstance(member, discord.Member):
        return member
    elif isinstance(member, int):
        return guild.get_member(int)
    elif isinstance(member, str):
        return get_member_named(guild, member)
    return member


def count_members(roles: list):
    count = 0
    for role in roles:
        count += len(role.members)
    return count


def get_channel_named(guild, name):
    channels = guild.channels

    def pred(c):
        try:
            return str(c.name).lower().strip() == name.lower().strip()
        except Exception:
            return False

    return discord.utils.find(pred, channels)


def safe_add(first, second):
    """Safely add two numbers (check resulting length)"""
    if len(str(first)) + len(str(second)) > MAX_STRING_LENGTH:
        raise KeyError
    return first + second


def safe_mult(first, second):
    """Safely multiply two numbers (check resulting length)"""
    if second * len(str(first)) > MAX_STRING_LENGTH:
        raise KeyError
    if first * len(str(second)) > MAX_STRING_LENGTH:
        raise KeyError
    return first * second


def eval_expr(expr):
    """Evaluate math problems safely"""
    return eval_(ast.parse(expr, mode="eval").body)


def eval_(node):
    """Do the evaluation."""
    if isinstance(node, ast.Num):  # <number>
        return node.n
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return OPERATORS[type(node.op)](eval_(node.left), eval_(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return OPERATORS[type(node.op)](eval_(node.operand))
    raise TypeError(node)


async def get_supported_platforms(lists: bool = True, supported: bool = False):
    platforms = (await ConfigHolder.PublisherManager.get_raw()).get("services", {})
    if supported:
        platforms = [(value.get("identifier")) for _, value in platforms.items()]
    elif lists:
        platforms = [
            (value.get("identifier"), value.get("name"))
            for _, value in platforms.items()
        ]
    return platforms


async def account_adder(bot, author: discord.User):  # @UnusedVariable
    platforms = await get_supported_platforms()
    platform_prompt = [name for _, name in platforms]
    platform_prompt = {
        str(counter): name for counter, name in enumerate(platform_prompt, start=1)
    }
    accounts = await smart_prompt(bot, author, platform_prompt, platforms)
    return accounts


async def update_profile(bot, user_data: dict, author: discord.User):
    msg = await author.send(
        "What country are you from (Enter the number next to the country)?"
    )
    country_data = WorldData.get("country", {})
    validcountries = sorted(
        list(value.get("name") for _, value in country_data.items())
    )
    desc = ""
    valid_county_list = []
    for index, value in enumerate(validcountries, start=1):
        desc += f"{index}. {value}\n"
        valid_county_list.append(str(index))
    pages = [box(page, lang="md") for page in list(pagify(desc, shorten_by=20))]
    ctx = namedtuple("Context", "author me bot send channel")
    new_ctx = ctx(author, bot.user, bot, author.send, msg.channel)
    menu_task = asyncio.create_task(menu(new_ctx, pages, DEFAULT_CONTROLS, timeout=180))
    country = None
    pred_check = MessagePredicate.contained_in(valid_county_list, ctx=new_ctx)
    while not country:
        with contextlib.suppress(asyncio.TimeoutError):
            await bot.wait_for("message", timeout=30.0, check=pred_check)
        country = (
            valid_county_list[pred_check.result]
            if pred_check.result is not None
            else None
        )
    with contextlib.suppress(Exception):
        menu_task.cancel()
    user_data["country"] = validcountries[int(country) - 1]
    cached_country = user_data["country"].lower().strip()

    if cached_country:
        country_data = WorldData.get("country", {})
        region = country_data.get(cached_country, {}).get("region")
        country_timezones = country_data.get(cached_country, {}).get("timezones")
        user_data["subzone"] = country_data.get(cached_country, {}).get("subregion")
    else:
        region = None
        country_timezones = None

    continent_data = sorted(CONTINENT_DATA.values())

    if not region:
        await author.send("Which zone are you from?")
        embed = discord.Embed(title="Pick a number that matches your zone")
        desc = ""
        valid_continent_list = []
        for index, value in enumerate(continent_data, start=1):
            desc += f"{index}. {value.title()}\n"
            valid_continent_list.append(str(index))
        embed.description = box(desc, lang="md")
        await author.send(embed=embed)
        zone = None
        pred_check = MessagePredicate.contained_in(valid_continent_list, ctx=new_ctx)
        while not zone:
            with contextlib.suppress(asyncio.TimeoutError):
                await bot.wait_for("message", timeout=30.0, check=pred_check)
            zone = (
                valid_continent_list[pred_check.result]
                if pred_check.result is not None
                else None
            )
        user_data["zone"] = continent_data[int(zone) - 1]
    else:
        user_data["zone"] = country_data.get(cached_country, {}).get("region", None)

    user_data["language"] = None

    if country_timezones and len(country_timezones) > 1:
        country_timezones_dict = {
            str(i): key for i, key in enumerate(country_timezones, start=1)
        }
        country_timezones = sorted(country_timezones_dict.values())

        await author.send(
            "There are multiple timezone for your country, please pick the one that match yours?"
        )
        embed = discord.Embed(title="Pick a number that matches your timezone")
        desc = ""
        valid_timezone_list = []
        for index, value in enumerate(country_timezones, start=1):
            desc += f"{index}. {value.upper()}\n"
            valid_timezone_list.append(str(index))

        embed.description = box(desc, lang="md")
        await author.send(embed=embed)
        timezone = None
        pred_check = MessagePredicate.contained_in(valid_timezone_list, ctx=new_ctx)
        while not timezone:
            with contextlib.suppress(asyncio.TimeoutError):
                await bot.wait_for("message", timeout=30.0, check=pred_check)
            timezone = (
                valid_timezone_list[pred_check.result]
                if pred_check.result is not None
                else None
            )
        user_data["timezone"] = country_timezones[int(timezone) - 1]
    elif country_timezones and len(country_timezones) == 1:
        user_data["timezone"] = country_timezones[0]

    return user_data


def get_user_named(bot, name):
    result = None
    members = bot.get_all_members()
    if len(name) > 5 and name[-5] == "#":
        # The 5 length is checking to see if #0000 is in the string,
        # as a#0000 has a length of 6, the minimum for a potential
        # discriminator lookup.
        potential_discriminator = name[-4:]

        # do the actual lookup and return if found
        # if it isn't found then we'll do a full name lookup below.
        result = discord.utils.get(
            members, name=name[:-5], discriminator=potential_discriminator
        )
        if result is not None:
            return result

    def pred(m):
        try:
            return (
                str(m.nick).lower() == name.lower()
                or str(m.name).lower() == name.lower()
            )
        except Exception:
            return False

    return discord.utils.find(pred, members)


async def get_activity_list(ctx, data, game_name, activity):
    username = False
    if activity == discord.ActivityType.playing:
        activity_name = "playing "
        username = True
    elif activity == discord.ActivityType.streaming:
        activity_name = "streaming "
        username = True
    elif activity == discord.ActivityType.listening:
        activity_name = "listening to"
    else:
        activity_name = "watching "

    embed_list = []
    embed_colour = await ctx.embed_colour()
    for key, value in sorted(data.items()):
        player_data = sorted(value, key=op.itemgetter(2, 1))
        usernames = ""
        discord_names = ""
        for mention, display_name, black_hole, account in player_data:
            account = account or "Unknown"
            if (
                len(usernames + f"{account}\n") > 1000
                or len(discord_names + f"{display_name}\n") > 1000
            ):
                embed = discord.Embed(
                    title=("Who's {activity}{name}?").format(
                        name=key, activity=activity_name
                    ),
                    colour=embed_colour,
                )
                embed.add_field(name="Discord Member", value=discord_names, inline=True)
                if username:
                    embed.add_field(name="Username", value=usernames, inline=True)
                embed_list.append(embed)
                usernames = ""
                discord_names = ""
            usernames += f"{account}\n"
            discord_names += f"{display_name}\n"
        if usernames:
            embed = discord.Embed(
                title=("Who's {activity} {name}?").format(
                    name=key, activity=activity_name
                ),
                colour=embed_colour,
            )
            embed.add_field(name="Discord Member", value=discord_names, inline=True)
            if username:
                embed.add_field(name="Username", value=usernames, inline=True)
            embed_list.append(embed)

    return embed_list


def get_meta_data(date: datetime):
    _, wk, dy = date.isocalendar()
    day = day_name[dy - 1]
    return day, wk, dy


def is_yesterday(a_date: date):
    return date.today() + timedelta(days=-1) == a_date


def is_tomorrow(a_date: date):
    return date.today() + timedelta(days=1) == a_date


def add_username_hyperlink(platform, username, _id):
    platform = platform.lower()
    url = None
    if platform == "twitch":
        url = "https://www.twitch.tv/" + quote_plus(f"{username}")
    elif platform == "steam":
        if _id:
            url = "https://steamcommunity.com/profiles/" + quote_plus(f"{_id}")
        else:
            url = "https://steamcommunity.com/id/" + quote_plus(f"{username}")
    elif platform == "instagram":
        url = "https://www.instagram.com/" + quote_plus(f"{username}")
    elif platform == "mixer":
        url = "https://mixer.com/" + quote_plus(f"{username}")
    elif platform == "reddit":
        url = "https://www.reddit.com/user/" + quote_plus(f"{username}")
    elif platform == "twitter":
        url = "https://twitter.com/" + quote_plus(f"{username}")
    elif platform == "youtube":
        url = "https://www.youtube.com/user/" + quote_plus(f"{username}")
    elif platform == "facebook":
        url = "https://www.facebook.com/" + quote_plus(f"{username}")
    elif platform == "soundcloud":
        url = "https://www.soundcloud.com/" + quote_plus(f"{username}")
    elif platform == "spotify":
        username2 = username
        if _id:
            username2 = _id
        url = "https://open.spotify.com/user/" + quote_plus(f"{username2}")

    if url:
        username = f"[{username}]({url})"

    return username


def get_member_activity(member: discord.Member, database=False):
    activities = getattr(member, "activities", None)
    if not activities:
        return None
    activities_type = [activity.type for activity in activities]
    if not activities_type:
        return None
    if not database:
        stream = bool(discord.ActivityType.streaming in activities_type)
        game = bool(discord.ActivityType.playing in activities_type)
        music = bool(discord.ActivityType.listening in activities_type)
    else:
        stream = False
        music = False
        game = bool(discord.ActivityType.playing in activities_type)

    if stream:
        looking_for = discord.ActivityType.streaming
        name_property = "details"
        context = "Streaming {name}"
    elif game:
        looking_for = discord.ActivityType.playing
        name_property = "name"
        context = "Playing {name}"
    elif music:
        looking_for = discord.ActivityType.listening
        name_property = "title"
        context = "Listening to {name}"
    else:
        return None

    interested_in = [
        activity for activity in member.activities if activity.type == looking_for
    ]
    if interested_in:
        activity_name = getattr(interested_in[0], name_property, None)
        if not database:
            return context.format(name=activity_name)
        else:
            return activity_name
    return None


async def get_all_user_profiles(
    guild, pm=False, withprofile=True, inactivity=False, timespan=None
):
    data = await ConfigHolder.GamingProfile.all_users()
    data_list = []
    role_value = 0
    if inactivity and isinstance(timespan, int):
        time_now = datetime.now(tz=timezone.utc)
        time_now_sec = time_now.timestamp()
        time_allowed = time_now_sec - (604800 * timespan)
    for discord_id, value in data.items():
        is_bot = value.get("is_bot")
        member = guild.get_member(discord_id)
        if not member:
            continue
        has_profile = await has_a_profile(member)
        last_seen = None
        if inactivity and isinstance(timespan, int):
            if member:
                if member.status != discord.Status.offline:
                    last_seen = datetime.now(tz=timezone.utc)
                else:
                    last_seen = value.get("seen")
            if last_seen:
                last_seen_datetime = get_date_time(last_seen).timestamp()
            else:
                last_seen_datetime = None
            if inactivity and last_seen_datetime:
                if last_seen_datetime < time_allowed:
                    innactive = True

        if member and not pm:
            username_true = member.display_name
            mention = member.mention
            top_role = member.top_role
            role_value = top_role.position * -1
        elif not member or pm:
            username_true = None
            mention = username_true

        if not inactivity:
            if withprofile and has_profile and username_true and is_bot is not True:
                data_list.append((username_true, mention, role_value))
            elif (
                not withprofile
                and not has_profile
                and username_true
                and is_bot is not True
            ):
                data_list.append((username_true, mention, role_value))
        else:
            if innactive:
                data_list.append((username_true, mention, role_value))

    return data_list


async def get_user_inactivity(member, pm=False, inactivity=False, timespan=None):
    data = await ConfigHolder.GamingProfile.user(member).all()
    data_list = []
    role_value = 0
    time_now = datetime.now(tz=timezone.utc)
    time_now_sec = time_now.timestamp()
    time_allowed = time_now_sec - (604800 * timespan)
    innactive = False
    if inactivity and isinstance(timespan, int):
        if member:
            if member.status != discord.Status.offline:
                last_seen = datetime.now(tz=timezone.utc)
            else:
                last_seen = data.get("seen")
        if last_seen:
            last_seen_datetime = get_date_time(last_seen).timestamp()
        else:
            last_seen_datetime = None
        if last_seen_datetime:
            if last_seen_datetime < time_allowed:
                innactive = True
        else:
            innactive = True

    if member and not pm:
        username_true = member.display_name
        mention = member.mention
        top_role = member.top_role
        role_value = top_role.position * -1
    elif not member or pm:
        username_true = None
        mention = username_true

    if innactive:
        data_list.append((username_true, mention, role_value))

    return data_list


async def get_role_profiles(role, pm=False, inactivity=False, timespan=None):
    data = []
    for member in role.members:
        data += await get_user_inactivity(
            member, pm=pm, inactivity=inactivity, timespan=timespan
        )
    return data


def get_date_string(then: datetime, now: datetime = datetime.now(timezone.utc)):
    _, week_number_now, _ = get_meta_data(now)
    day_then, week_number_then, _ = get_meta_data(then)
    time = then.strftime("%I:%M %p")
    time_fallback = then.strftime("%b %d, %y at %I:%M %p")
    past = False
    future = False
    if then.date() == now.date():
        return f"Today at {time}"
    else:
        if then.date() > now.date():
            future = True
        elif then.date() < now.date():
            past = True
    if past:
        if is_yesterday(then.date()):
            return f"Yesterday at {time}"
        elif week_number_now == week_number_then:
            return f"{day_then} at {time}"
        elif week_number_then + 1 == week_number_now:
            return f"Last {day_then} at {time}"
    elif future:
        if is_tomorrow(then.date()):
            return f"Tomorrow at {time}"
        elif week_number_now == week_number_then:
            return f"{day_then} at {time}"
        elif week_number_then == week_number_now + 1:
            return f"Next {day_then} at {time}"
    return f"{time_fallback}"


async def get_all_user_rigs(guild, pm=False):
    data = await ConfigHolder.PCSpecs.all_users()
    data_list = []
    role_value = 0
    for discord_id, value in data.items():
        member = guild.get_member(discord_id)

        if member and not pm:
            username_true = member.display_name
            mention = member.mention
            top_role = member.top_role
            role_value = top_role.position * -1
        elif not member or pm:
            username_true = None
            mention = username_true
        else:
            continue

        rig_data = value.get("rig", {}).get("CPU")
        if rig_data and username_true and mention:
            data_list.append((rig_data, username_true, mention, role_value))
    return data_list


async def get_mention(ctx, args: list, bot, get_platform=True, stats=False):
    if get_platform:
        supported_platforms = await get_supported_platforms(supported=True)
    message = ctx.message
    author = ctx.message.author
    target_mention = None
    target_member = None
    target_user = None
    platform = None
    member_name = None

    if ctx.guild:
        guild = ctx.message.guild
    else:
        guild = None

    if message.mentions:
        target_member = message.mentions[0]
        if sum(1 for x in message.mentions) >= 2:
            target_member = [
                x for x in message.mentions if x != author or x != ctx.guild.me
            ][0]
        member_name = target_member.display_name
        if get_platform and len(args) > 1:
            platform = (
                args[1].lower() if args[1].lower() in supported_platforms else None
            )
        target_user = bot.get_user(target_member.id)
    else:
        if len(args) == 2:
            if get_platform:
                platform = (
                    args[1].lower() if args[1].lower() in supported_platforms else None
                )
            member_name = args[0]
            if guild:
                target_member = get_member_named(guild, member_name)
            else:
                target_member = get_user_named(bot, member_name)

            if not target_member:
                target_member = author
            target_user = bot.get_user(target_member.id)

        if len(args) == 1:
            member_name = args[0]
            if get_platform:
                platform = (
                    member_name.lower()
                    if member_name.lower() in supported_platforms
                    else None
                )
            if not platform and guild:
                target_member = get_member_named(guild, member_name)
            elif not platform:
                target_member = get_user_named(bot, member_name)
            if not platform and target_member:
                target_user = bot.get_user(target_member.id)

        if not args:
            target_mention = author
            target_user = bot.get_user(target_mention.id)
            member_name = author.display_name

        if stats:
            if len(args) == 1:
                member_name = args[0]
                if guild:
                    target_member = get_member_named(guild, member_name)
                target_member = get_user_named(bot, member_name)
                if target_member:
                    target_user = bot.get_user(target_member.id)

            if not target_user:
                target_mention = author
                target_user = bot.get_user(target_mention.id)
                member_name = author.display_name

    if guild and target_user:
        target_member = guild.get_member(target_user.id)
    target_user = target_member

    return target_user, target_member, platform, member_name


async def smart_prompt(bot, author: discord.User, prompt_data: dict, platforms: dict):
    def check(m):
        return (
            m.author == author
            and isinstance(m.channel, discord.DMChannel)
            and len(m.content) < 33
        )

    data = {}
    key = None
    original_len = len(prompt_data) + 1
    await author.send(f"Pick number {original_len} to finish this part.")
    while True:
        if (
            "finish" not in prompt_data.values()
            and "Finish" not in prompt_data.values()
        ):
            prompt_data.update({str(original_len): "finish"})
        embed = discord.Embed(
            title="Pick a number that matches the service you want to add"
        )
        valid_account_list = []
        desc = ""
        for index, value in enumerate(prompt_data.values(), start=1):
            desc += f"{index}. {value}\n"
            valid_account_list.append(str(index))
        embed.description = box(desc, lang="md")
        await author.send(embed=embed)

        if "finish" in prompt_data.values() or "Finish" in prompt_data.values():
            valid_keys = map(str, list(prompt_data.keys())[:-1])
        else:
            valid_keys = map(str, list(prompt_data.keys()))

        msg = await bot.wait_for("message", check=check)
        if msg and msg.content.lower() in valid_keys:
            key = msg.content
            name = prompt_data.get(msg.content, "")
            command = next(
                (
                    command_toget
                    for command_toget, name_toget in platforms
                    if name_toget == name
                ),
                None,
            )
            if name and command:
                await author.send(
                    f"What is your username for {name}? (32 characters or less)"
                )
                msg = await bot.wait_for("message", check=check)
                if msg and msg.content.lower() in ["stop", "finish"]:
                    await author.send(f"Thanks for adding your accounts.")
                    break
                elif msg and msg.content.lower() in ["skip", "cancel"]:
                    await author.send(f"Skipping {name} account.")
                    continue
                if msg and not len(msg.content.lower()) <= 3:
                    username = msg.content.strip()
                    data.update({command: username.strip()})
        elif msg and prompt_data.get(msg.content, "").lower() == "finish":
            await author.send(f"Thanks for adding your accounts.")
            break
        else:
            key = 999
    return data


def get_member_named(guild, name):
    result = None
    members = guild.members
    if len(name) > 5 and name[-5] == "#":
        potential_discriminator = name[-4:]
        result = discord.utils.get(
            members, name=name[:-5], discriminator=potential_discriminator
        )
        if result is not None:
            return result

    def pred(m):
        try:
            return (
                str(m.nick).lower().strip() == name.lower().strip()
                or str(m.name).lower().strip() == name.lower().strip()
            )
        except Exception:
            return False

    return discord.utils.find(pred, members)


async def get_all_by_platform(platform: str, guild: discord.Guild, pm: bool = False):
    platform = platform.lower().strip()
    data = await ConfigHolder.AccountManager.all_users()
    data_list = []
    role_value = 0

    for discord_id, value in data.items():
        steamid = None
        member = guild.get_member(int(discord_id))
        if member and not pm:
            username_true = member.display_name
            mention = member.mention
            top_role = member.top_role
            role_value = top_role.position * -1
        elif not member or pm:
            username_true = None
            mention = f"<@!{discord_id}>"
        else:
            continue

        account = value.get("account", {}).get(platform)
        if platform == "steam":
            steamid = value.get("account", {}).get("steamid")
        if platform == "spotify":
            steamid = value.get("account", {}).get("spotifyid")

        if account and username_true and mention:
            data_list.append((account, username_true, mention, role_value, steamid))
    return data_list


def get_date_time(s: Union[int, str, datetime] = None):
    if s is None:
        return datetime.now(tz=timezone.utc)
    if isinstance(s, int):
        return datetime.fromtimestamp(s, tz=timezone.utc)
    if isinstance(s, datetime):
        if not s.tzinfo:
            return UTC.localize(s)  # @UndefinedVariable
        return s
    d = dateutil.parser.parse(s)
    if not d.tzinfo:
        d = UTC.localize(d)  # @UndefinedVariable
    return d


async def update_member_atomically(
    ctx: Union[commands.Context, discord.Member],
    give: List[discord.Role] = None,
    remove: List[discord.Role] = None,
    nick: str = None,
    member: discord.Member = None,
    member_update=False,
):
    if not ctx.guild:
        return None
    me = ctx.guild.me
    if member_update:
        assert isinstance(ctx, discord.Member)
        member = member
        permissions = me.guild_permissions
    else:
        assert isinstance(ctx, commands.Context)
        member = member or ctx.author
        permissions = me.permissions_in(ctx.channel)
    if member == me:
        return
    can_modify_nick = permissions.manage_nicknames
    can_modify_role = permissions.manage_roles
    if can_modify_role:
        give = give or []
        remove = remove or []
        roles = [r for r in member.roles if r and r not in remove]
        roles.extend([r for r in give if r and r not in roles])
        roles = list(set(roles))
        low_roles_add = [r for r in roles if r < me.top_role if r not in member.roles]
        low_roles_remove = [r for r in remove if r < me.top_role if r in member.roles]
        high_roles = [r for r in roles if r >= me.top_role]
        roles_changed = sorted(roles) != sorted(member.roles)
    else:
        roles = []
        high_roles = []
        low_roles_add = []
        low_roles_remove = []
        roles_changed = False

    if me.top_role < member.top_role and nick:
        return
    if not roles_changed and not nick:
        return
    if member.guild.owner == member:
        return
    if can_modify_nick and nick and not roles_changed:
        return await member.edit(nick=nick)
    if can_modify_role and roles_changed and not nick:
        if not high_roles:
            return await member.edit(roles=roles)
        if low_roles_add:
            await member.add_roles(*low_roles_add)
        if low_roles_remove:
            await member.remove_roles(*low_roles_remove)
        return
    if roles_changed and nick:
        if can_modify_role and can_modify_nick:
            if not high_roles:
                return await member.edit(roles=roles, nick=nick)
            if low_roles_add:
                await member.add_roles(*low_roles_add)
            if low_roles_remove:
                await member.remove_roles(*low_roles_remove)
            await member.edit(nick=nick)
            return
        elif can_modify_role:
            if not high_roles:
                return await member.edit(roles=roles)
            if low_roles_add:
                await member.add_roles(*low_roles_add)
            if low_roles_remove:
                await member.remove_roles(*low_roles_remove)
            return
        else:
            return await member.edit(nick=nick)


_header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
MAX_STRING_LENGTH = 100000

OPERATORS = {
    ast.Add: safe_add,
    ast.Sub: op.sub,
    ast.Mult: safe_mult,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}


def get_role_named(guild, name):
    if not guild:
        return None

    roles = guild.roles

    def pred(c):
        try:
            return str(c.name).strip() == name.strip()
        except Exception as e:
            logger.error(f"Error when trying to find role: {name}: E: {e}")
            return False

    return discord.utils.find(pred, roles)
