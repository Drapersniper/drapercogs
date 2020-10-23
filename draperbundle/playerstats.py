import json
import logging
from collections import defaultdict
from copy import copy
from typing import Optional

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from .config_holder import ConfigHolder
from .converters import ConvertMember

log = logging.getLogger("cks.cogs.playerstats")

_header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}


class PlayerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.guild_only()
    async def gstats(self, ctx: commands.Context):
        """Shows users game stats"""

    @gstats.command(enabled=True, name="bfv")
    async def stats_bfv(
        self, ctx: commands.Context, *, member: Optional[ConvertMember] = None
    ):
        """Shows a users Battlefield V stats"""

        if member is None:
            target = ctx.author
        else:
            target = member

        if not target:
            return
        assert isinstance(target, discord.Member)

        origin = await ConfigHolder.AccountManager.user(target).account.origin()
        if origin:
            data = await _parse_stats_battlefield_v(origin)
            overview = data.get("overview", {})
            gamemode = data.get("gamemode")
            player_class = overview.get("Lifetime", {})
            classes = data.get("class")
            icon_url = data.get("display_url")
            rank_url = player_class.get("Rank", {}).get("meta", {}).get("rank_url")
            rank_name = player_class.get("Rank", {}).get("meta", {}).get("rank_name")

            embed_list = []
            if player_class:
                rank_number = player_class.get("Rank", {}).get("displayValue")
                score_min = player_class.get("Score/min").get("displayValue")
                k_d = player_class.get("K/D").get("displayValue")
                Accuracy = player_class.get("Shots Accuracy").get("displayValue")
                Kills = player_class.get("Kills").get("displayValue")
                Deaths = player_class.get("Deaths").get("displayValue")
                Damage = player_class.get("Damage").get("displayValue")
                Assists = player_class.get("Assists").get("displayValue")
                Shots_taken = player_class.get("Shots Taken").get("displayValue")
                Shots_hit = player_class.get("Shots Hit").get("displayValue")
                Kill_streak = player_class.get("Kill Streak").get("displayValue")
                Dogtags = player_class.get("Dogtags Taken").get("displayValue")
                Headshots = player_class.get("Headshots").get("displayValue")
                Longest_hs = player_class.get("Longest Headshot").get("displayValue")
                Kills_min = player_class.get("Kills/min").get("displayValue")
                Ace = player_class.get("Ace Squad").get("displayValue")
                Win_perc = player_class.get("Win %").get("displayValue")
                Wins = player_class.get("Wins").get("displayValue")
                Losses = player_class.get("Losses").get("displayValue")
                rounds_played = player_class.get("Rounds Played", {}).get(
                    "displayValue"
                )
                play_time = player_class.get("Time Played", {}).get("displayValue")

                overview_embed = discord.Embed(title=f"{target} Overview")
                overview_embed.set_author(name=target.display_name, icon_url=icon_url)
                overview_embed.set_thumbnail(url=rank_url)
                overview_embed.add_field(
                    name="Played For", value=play_time, inline=True
                )
                overview_embed.add_field(
                    name="Rounds Played", value=rounds_played, inline=True
                )
                overview_embed.add_field(
                    name="Rank", value=f"{rank_number} ({rank_name})", inline=True
                )
                overview_embed.add_field(
                    name="Score Per Min", value=score_min, inline=True
                )
                overview_embed.add_field(
                    name="Kill/Death Ratio", value=k_d, inline=True
                )
                overview_embed.add_field(
                    name="Win/Loss Ratio", value=Win_perc, inline=True
                )
                overview_embed.add_field(name="Wins", value=Wins, inline=True)
                overview_embed.add_field(name="Losses", value=Losses, inline=True)
                overview_embed.add_field(name="Accuracy", value=Accuracy, inline=True)
                overview_embed.add_field(name="Ace Squad", value=Ace, inline=True)
                overview_embed.add_field(name="Kills", value=Kills, inline=True)
                overview_embed.add_field(name="Deaths", value=Deaths, inline=True)
                overview_embed.add_field(name="Damage", value=Damage, inline=True)
                overview_embed.add_field(name="Assists", value=Assists, inline=True)
                overview_embed.add_field(name="Headshots", value=Headshots, inline=True)
                overview_embed.add_field(
                    name="Longest Headshot", value=Longest_hs, inline=True
                )
                overview_embed.add_field(name="Kills/min", value=Kills_min, inline=True)
                overview_embed.add_field(
                    name="Dogtags Taken", value=Dogtags, inline=True
                )
                overview_embed.add_field(
                    name="Shots Taken", value=Shots_taken, inline=True
                )
                overview_embed.add_field(name="Shots Hit", value=Shots_hit, inline=True)
                overview_embed.add_field(
                    name="Kill Streak", value=Kill_streak, inline=True
                )
                embed_list.append(overview_embed)

            if classes:
                for class_name, data in classes.items():
                    embed = None
                    Rank = data.get("Rank", {}).get("displayValue")
                    Kills = data.get("Kills", {}).get("displayValue")
                    Deaths = data.get("Deaths", {}).get("displayValue")
                    Kills_min = data.get("Kills/min", {}).get("displayValue")
                    K_D = data.get("K/D", {}).get("displayValue")

                    Time_Played = data.get("Time Played", {}).get("displayValue")
                    Shots_Fired = data.get("Shots Fired", {}).get("displayValue")
                    Shots_Hit = data.get("Shots Hit", {}).get("displayValue")
                    Shots_Accuracy = data.get("Shots Accuracy", {}).get("displayValue")
                    Score = data.get("Score", {}).get("displayValue")
                    Score_min = data.get("Score/min", {}).get("displayValue")
                    embed = discord.Embed(title=f"{class_name} Overview")
                    embed.set_author(name=target.display_name, icon_url=rank_url)
                    embed.set_thumbnail(url=icon_url)
                    embed.add_field(name="Rank", value=Rank, inline=True)
                    embed.add_field(name="Kills", value=Kills, inline=True)
                    embed.add_field(name="Deaths", value=Deaths, inline=True)
                    embed.add_field(name="Kills/min", value=Kills_min, inline=True)
                    embed.add_field(name="K/D", value=K_D, inline=True)
                    embed.add_field(name="Time Played", value=Time_Played, inline=True)
                    embed.add_field(name="Shots Fired", value=Shots_Fired, inline=True)
                    embed.add_field(name="Shots Hit", value=Shots_Hit, inline=True)
                    embed.add_field(
                        name="Shots Accuracy", value=Shots_Accuracy, inline=True
                    )
                    embed.add_field(name="Score", value=Score, inline=True)
                    embed.add_field(name="Score/min", value=Score_min, inline=True)
                    if embed:
                        embed_list.append(embed)

            if gamemode:
                for game_mode, data in gamemode.items():
                    if game_mode == "SquadConquest":
                        game_mode = "Squad Conquest"
                    elif game_mode == "FinalStand":
                        game_mode = "Final Stand"
                    elif game_mode == "Tdm":
                        game_mode = "Team Deathmatch"
                    embed = None
                    Wins = data.get("Wins", {}).get("displayValue")
                    Losses = data.get("Losses", {}).get("displayValue")
                    win_perc = data.get("Win %", {}).get("displayValue")
                    Score = data.get("Score", {}).get("displayValue")
                    flaf_def = data.get("Flag Defends", {}).get("displayValue")
                    flaf_cap = data.get("Flag Captures", {}).get("displayValue")
                    Artillery_kill_def = data.get("Artillery Defense Kills", {}).get(
                        "displayValue"
                    )
                    Bombs_Placed = data.get("Bombs Placed", {}).get("displayValue")
                    Bombs_Defused = data.get("Bombs Defused", {}).get("displayValue")
                    Carriers_Kills = data.get("Carriers Kills", {}).get("displayValue")
                    Carriers_Released = data.get("Carriers Released", {}).get(
                        "displayValue"
                    )
                    Messages_Written = data.get("Messages Written", {}).get(
                        "displayValue"
                    )
                    Messages_Delivered = data.get("Messages Delivered", {}).get(
                        "displayValue"
                    )
                    if Wins and Losses and win_perc and Score:
                        embed = discord.Embed(title=f"{game_mode} Overview")
                        embed.set_author(name=target.display_name, icon_url=rank_url)
                        embed.set_thumbnail(url=icon_url)
                        embed.add_field(
                            name="Win/Loss Ratio", value=win_perc, inline=True
                        )
                        embed.add_field(name="Wins", value=Wins, inline=True)
                        embed.add_field(name="Losses", value=Losses, inline=True)
                        embed.add_field(name="Score", value=Score, inline=True)
                        if flaf_def:
                            embed.add_field(
                                name="Flag Defends", value=flaf_def, inline=True
                            )
                        if flaf_cap:
                            embed.add_field(
                                name="Flag Captures", value=flaf_cap, inline=True
                            )
                        if Artillery_kill_def:
                            embed.add_field(
                                name="Artillery Defense Kills",
                                value=Artillery_kill_def,
                                inline=True,
                            )
                        if Bombs_Placed:
                            embed.add_field(
                                name="Bombs Placed", value=Bombs_Placed, inline=True
                            )
                        if Bombs_Defused:
                            embed.add_field(
                                name="Bombs Defused", value=Bombs_Defused, inline=True
                            )
                        if Carriers_Kills:
                            embed.add_field(
                                name="Carriers Kills", value=Carriers_Kills, inline=True
                            )
                        if Carriers_Released:
                            embed.add_field(
                                name="Carriers Released",
                                value=Carriers_Released,
                                inline=True,
                            )
                        if Messages_Written:
                            embed.add_field(
                                name="Messages Written",
                                value=Messages_Written,
                                inline=True,
                            )
                        if Messages_Delivered:
                            embed.add_field(
                                name="Messages Delivered",
                                value=Messages_Delivered,
                                inline=True,
                            )
                    if embed:
                        embed_list.append(embed)
            if embed_list:
                await menu(ctx, embed_list, controls=DEFAULT_CONTROLS)
                return

        await ctx.send(f"No data for {target}")


def _url_maker(game, username, platform="origin"):
    if game == "bfv":
        return (
            f"https://api.tracker.gg/api/v2/bfv/standard/profile/{platform}/{username}"
        )
    elif game == "apex":
        baseurl = "https://public-api.tracker.gg/apex/v1/standard/profile"
        return f"{baseurl}/5/{username}"
    elif game == "dv2":
        baseurl = "https://division.tracker.gg/division-2/profile"
        extra = "overview"
        return f"{baseurl}/{platform}/{username}/{extra}"


async def _parse_stats_apex_legends(player):
    url = _url_maker(game="apex", username=player)
    data = await _get_website_data(url)
    data = data["data"]
    hero = data["children"][0]
    playerstats = data["stats"]
    herostats = hero["stats"]
    heroname = hero["metadata"]["legend_name"]
    icon = hero["metadata"]["icon"]
    herostats = {
        stat["metadata"]["key"]: {
            "value": stat["displayValue"],
            "rank": stat["displayRank"],
        }
        for stat in herostats
    }
    playerstats = {
        stat["metadata"]["key"]: {
            "value": stat["displayValue"],
            "rank": stat["displayRank"],
        }
        for stat in playerstats
    }
    playerdata = {
        "player": playerstats,
        "hero": herostats,
        "metadata": {"heroname": heroname, "heroicon": icon},
    }
    return playerdata


async def _get_website_data(url):
    headers = copy(_header)
    if "https://public-api.tracker.gg/apex" in url:
        headers.update({"TRN-Api-Key": "7080bd67-b7a1-4229-9cad-0d0cdccf1c31"})

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()


def parse_bfv_segments(segment, data):
    segment_type = segment.get("type")
    if not segment_type:
        return data
    name = segment.get("metadata", {}).get("name")
    if not name:
        return data
    stats = segment.get("stats", {})
    if not stats:
        return
    whitelist = ["displayValue"]
    if segment_type not in data:
        data[segment_type] = {}
    if name not in data[segment_type]:
        data[segment_type][name] = {}

    for item in stats.values():
        for k, v in item.items():
            if k in whitelist:
                if item.get("displayName") not in data[segment_type][name]:
                    data[segment_type][name][item.get("displayName")] = {}
                data[segment_type][name][item.get("displayName")][k] = v
            if v == "Rank":
                meta = item.get("metadata")
                label = meta.get("label")
                image = meta.get("imageUrl")
                if item.get("displayName") not in data[segment_type][name]:
                    data[segment_type][name][item.get("displayName")] = {}
                data[segment_type][name][item.get("displayName")]["meta"] = {
                    "rank_name": label,
                    "rank_url": image,
                }
    return data


async def _parse_stats_battlefield_v(player):
    formatted_data = defaultdict(dict)
    player_url = f"https://api.tracker.gg/api/v2/bfv/standard/profile/origin/{player}"
    weapons_url = f"https://api.tracker.gg/api/v2/bfv/profile/origin/{player}/weapons"
    vehicles_url = f"https://api.tracker.gg/api/v2/bfv/profile/origin/{player}/vehicles"
    report_url = f"https://api.tracker.gg/api/v2/bfv/gamereports/origin/latest/{player}"
    wanted_player_segments = ["overview", "firestorm", "class", "gamemode"]
    player_data = await _get_website_data(player_url)
    player_data = player_data.get("data", {})
    player_url = player_data.get("platformInfo", {}).get("avatarUrl")
    formatted_data["display_url"] = player_url
    player_segments = player_data.get("segments", [])
    player_segments = [
        s for s in player_segments if s.get("type") in wanted_player_segments
    ]
    for segment in player_segments:
        formatted_data = parse_bfv_segments(segment, formatted_data)

    # weapons_data = await _get_website_data(weapons_url)
    # vehicles_data = await _get_website_data(vehicles_url)
    # report_data = await _get_website_data(report_url)

    return formatted_data


async def _parse_stats_division_2(player):
    url = _url_maker(game="dv2", platform="uplay", username=player)
    data = await _get_website_data(url)
    script = data.find_all("script")
    scriptscript = str(script[3])
    jsonstring = scriptscript[33:-131]
    data = json.loads(jsonstring)
    playername = "division-2|uplay|" + player.lower()
    try:
        data = data["stats"]["standardPlayers"][playername]["stats"]
    except KeyError:
        return dict(general={}, pvp={})
    else:
        playerdata = dict(general={}, pvp={})
        general = playerdata["general"]
        pvp = playerdata["pvp"]

        general["timePlayed"] = {
            "name": "Time Played",
            "value": data["timePlayed"]["value"],
            "displayValue": data["timePlayed"]["displayValue"],
        }
        general["itemsLooted"] = {
            "name": "Items Looted",
            "value": data["itemsLooted"]["value"],
            "displayValue": data["itemsLooted"]["displayValue"],
        }
        general["xPClan"] = {
            "name": "Clan XP",
            "value": data["xPClan"]["value"],
            "displayValue": data["xPClan"]["displayValue"],
        }
        general["latestGearScore"] = {
            "name": "Gear Score",
            "value": data["latestGearScore"]["value"],
            "displayValue": data["latestGearScore"]["displayValue"],
        }
        general["latestGearScore"] = {
            "name": "Player Level",
            "value": data["latestGearScore"]["value"],
            "displayValue": data["latestGearScore"]["displayValue"],
        }
        general["highestPlayerLevel"] = {
            "name": "Gear Score",
            "value": data["highestPlayerLevel"]["value"],
            "displayValue": data["highestPlayerLevel"]["displayValue"],
        }

        pvp["rankDZ"] = {
            "name": "DZ Level",
            "value": data["rankDZ"]["value"],
            "displayValue": data["rankDZ"]["displayValue"],
        }
        pvp["killsPvP"] = {
            "name": "PvP Kills",
            "value": data["killsPvP"]["value"],
            "displayValue": data["killsPvP"]["displayValue"],
        }
        pvp["roguesKilled"] = {
            "name": "Rogues Killed",
            "value": data["roguesKilled"]["value"],
            "displayValue": data["roguesKilled"]["displayValue"],
        }
        pvp["timePlayedRogue"] = {
            "name": "Rogue Time Played",
            "value": data["timePlayedRogue"]["value"],
            "displayValue": data["timePlayedRogue"]["displayValue"],
        }
        pvp["timePlayedRogueLongest"] = {
            "name": "Rogue Longest Time Played",
            "value": data["timePlayedRogueLongest"]["value"],
            "displayValue": data["timePlayedRogueLongest"]["displayValue"],
        }
        pvp["killsPvP"] = {
            "name": "PvP Kills",
            "value": data["killsPvP"]["value"],
            "displayValue": data["killsPvP"]["displayValue"],
        }
        return playerdata
