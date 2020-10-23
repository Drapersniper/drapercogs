# -*- coding: utf-8 -*-
from redbot.core.config import Config

from .constants import (
    anthem_icon,
    apex_icon,
    bfv_icon,
    csgo_icon,
    division_2_icon,
    lol_icon,
    minecraft_icon,
    osrs_icon,
)


class ConfigHolderClass(object):
    AccountManager = Config.get_conf(
        None, identifier=1273062035, force_registration=True, cog_name="AccountManager"
    )
    GamingProfile = Config.get_conf(
        None, identifier=9420012589, force_registration=True, cog_name="GamingProfile"
    )
    PCSpecs = Config.get_conf(
        None, identifier=8205491788, force_registration=True, cog_name="PCSpecs"
    )
    PublisherManager = Config.get_conf(
        None,
        identifier=2064553666,
        force_registration=True,
        cog_name="PublisherManager",
    )
    PlayerStatus = Config.get_conf(
        None, identifier=3584065639, force_registration=True, cog_name="PlayerStatus"
    )
    LogoData = Config.get_conf(
        None, identifier=7056820599, force_registration=True, cog_name="LogoData"
    )
    DynamicChannels = Config.get_conf(
        None, identifier=3172784244, force_registration=True, cog_name="DynamicChannels"
    )
    CustomChannels = Config.get_conf(
        None, identifier=7861412794, force_registration=True, cog_name="CustomChannels"
    )
    RandomQuotes = Config.get_conf(
        None, identifier=8475527184, force_registration=True, cog_name="RandomQuotes"
    )


ConfigHolder = ConfigHolderClass()

default_member_AccountManager = dict(account=dict(origin=None, uplay=None))
default_member_GamingProfile = dict(
    discord_user_id=None,
    discord_user_name=None,
    discord_true_name=None,
    guild_display_name=None,
    is_bot=False,
    country=None,
    timezone=None,
    language=None,
    zone=None,
    subzone=None,
    seen=None,
    trial=None,
    nickname_extas=None,
)
default_member_PCSpecs = dict(
    rig=dict(
        CPU=None,
        GPU=None,
        RAM=None,
        Motherboard=None,
        Storage=None,
        Monitor=None,
        Mouse=None,
        Keyboard=None,
        Case=None,
    )
)
default_custom_PublisherManager = {
    "services": {
        "battlenet": {
            "name": "Battle.net",
            "identifier": "battlenet",
            "games": ["Call of Duty: Modern Warfare"],
        },
        "epic": {"name": "Epic Games", "identifier": "epic", "games": []},
        "gog": {"name": "GOG.com", "identifier": "gog", "games": []},
        "mixer": {"name": "Mixer", "identifier": "mixer", "games": []},
        "psn": {"name": "PlayStation Network", "identifier": "psn", "games": []},
        "reddit": {"name": "Reddit", "identifier": "reddit", "games": []},
        "riot": {
            "name": "Riot Games",
            "identifier": "riot",
            "games": ["League of Legends"],
        },
        "spotify": {"name": "Spotify", "identifier": "spotify", "games": []},
        "steam": {"name": "Steam", "identifier": "steam", "games": []},
        "twitch": {"name": "Twitch", "identifier": "twitch", "games": []},
        "twitter": {"name": "Twitter", "identifier": "twitter", "games": []},
        "uplay": {
            "name": "Uplay",
            "identifier": "uplay",
            "games": ["Tom Clancy's The Division 2"],
        },
        "xbox": {"name": "Xbox Live", "identifier": "xbox", "games": []},
        "youtube": {"name": "YouTube", "identifier": "youtube", "games": []},
        "origin": {
            "name": "Origin",
            "identifier": "origin",
            "games": ["Apex Legends", "Battlefield\u2122 V", "Anthem\u2122"],
        },
        "facebook": {
            "name": "Facebook",
            "identifier": "facebook",
            "games": [],
        },
        "instagram": {
            "name": "Instagram",
            "identifier": "instagram",
            "games": [],
        },
        "snapchat": {
            "name": "Snapchat",
            "identifier": "snapchat",
            "games": [],
        },
        "mojang": {"name": "Mojang", "identifier": "mojang", "games": []},
        "skype": {"name": "Skype", "identifier": "skype", "games": []},
        "soundcloud": {
            "name": "SoundCloud",
            "identifier": "soundcloud",
            "games": [],
        },
        "nintendo": {"name": "Nintendo", "identifier": "nintendo", "games": []},
        "runescape": {
            "name": "Jagex",
            "identifier": "runescape",
            "games": ["RuneLite", "OSBuddy", "Old School Runescape", "RuneScape"],
        },
    },
    "publisher": {
        "RuneLite": "runescape",
        "OSBuddy": "runescape",
        "Old School Runescape": "runescape",
        "RuneScape": "runescape",
    },
}

default_guild_StatusManager = dict(
    channel_icon={
        "lfg-apex": apex_icon,
        "lfg-bfv": bfv_icon,
        "lfg-anthem": anthem_icon,
        "lfg-division-2": division_2_icon,
        "battlefield-v": bfv_icon,
        "apex-legends": apex_icon,
        "anthem": anthem_icon,
        "division-2": division_2_icon,
        "lfg-counter-strike": csgo_icon,
        "lfg-lol": lol_icon,
        "lfg-apex-legends": apex_icon,
        "runescape": osrs_icon,
        "counter-strike": csgo_icon,
        "league-of-legends": lol_icon,
        "minecraft": minecraft_icon,
        "modern-warfare": "https://cdn.discordapp.com/attachments/557869681721999370/637186507475779585/communityIcon_8jyqgoe3xk131.png",
        "lfg-mw": "https://cdn.discordapp.com/attachments/557869681721999370/637186507475779585/communityIcon_8jyqgoe3xk131.png",
    },
    channel_game_name={
        "lfg-apex": ("Apex Legends", ["Apex Legends"]),
        "lfg-bfv": ("Battlefield\u2122 V", ["Battlefield\u2122 V"]),
        "lfg-anthem": ("Anthem\u2122", ["Anthem\u2122"]),
        "lfg-division-2": ("The Division 2", ["Tom Clancy's The Division 2"]),
        "battlefield-v": ("Battlefield\u2122 V", ["Battlefield\u2122 V"]),
        "anthem": ("Anthem\u2122", ["Anthem\u2122"]),
        "division-2": ("The Division 2", ["Tom Clancy's The Division 2"]),
        "lfg-counter-strike": (
            "Counter-Strike: Global Offensive",
            ["Counter-Strike: Global Offensive"],
        ),
        "lfg-lol": ("League of Legends", ["League of Legends"]),
        "lfg-apex-legends": ("Apex Legends", ["Apex Legends"]),
        "runescape": (
            "Old School Runescape",
            ["RuneLite", "OSBuddy", "Old School Runescape", "RuneScape"],
        ),
        "counter-strike": ("CS:GO", ["Counter-Strike: Global Offensive"]),
        "league-of-legends": ("League of Legends", ["League of Legends"]),
        "apex-legends": ("Apex Legends", ["Apex Legends"]),
        "minecraft": ("Minecraft", ["Minecraft"]),
        "lfg-r6": (
            "Rainbow Six Siege",
            ["Tom Clancy's Rainbow Six Siege", "Rainbow Six Siege"],
        ),
        "rainbow-six-siege": (
            "Rainbow Six Siege",
            ["Tom Clancy's Rainbow Six Siege", "Rainbow Six Siege"],
        ),
        "modern-warfare": (
            "Modern Warfare",
            ["Call of Duty: Modern Warfare", "Modern Warfare"],
        ),
        "lfg-mw": (
            "Modern Warfare",
            ["Call of Duty: Modern Warfare", "Modern Warfare"],
        ),
    },
)
default_custom_Logos = dict(
    battlenet="https://upload.wikimedia.org/wikipedia/en/2/23/Blizzard_Battle.net_logo.png",
    epic="https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/516px-Epic_Games_logo.svg.png",
    gog="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/GOG.com_logo.svg/1024px-GOG.com_logo.svg.png",
    mixer="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Mixer_%28website%29_logo.svg/200px-Mixer_%28website%29_logo.svg.png",
    psn="https://upload.wikimedia.org/wikipedia/commons/f/f2/PlayStation_Network_logo.png",
    reddit="https://upload.wikimedia.org/wikipedia/en/thumb/5/58/Reddit_logo_new.svg/640px-Reddit_logo_new.svg.png",
    riot="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Riot_Games.svg/1920px-Riot_Games.svg.png",
    spotify="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Spotify_logo_with_text.svg/559px-Spotify_logo_with_text.svg.png",
    steam="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/480px-Steam_icon_logo.svg.png",
    twitch="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Twitch_logo_%28wordmark_only%29.svg/640px-Twitch_logo_%28wordmark_only%29.svg.png",
    twitter="https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Twitter_bird_logo_2012.svg/590px-Twitter_bird_logo_2012.svg.png",
    uplay="https://upload.wikimedia.org/wikipedia/commons/1/1c/Uplay_Logo.png",
    xbox="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/XBOX_logo_2012.svg/800px-XBOX_logo_2012.svg.png",
    youtube="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/YouTube_Logo_2017.svg/640px-YouTube_Logo_2017.svg.png",
    origin="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Origin.svg/640px-Origin.svg.png",
    facebook="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Facebook_Logo_%282015%29_light.svg/640px-Facebook_Logo_%282015%29_light.svg.png",
    instagram="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Instagram_logo_2016.svg/480px-Instagram_logo_2016.svg.png",
    snapchat="https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Snapchat_logo.svg/480px-Snapchat_logo.svg.png",
)
default_guild_CustomChannels = dict(
    mute_roles=[],
    category_with_button={},
    custom_channels={},
    user_created_voice_channels_bypass_roles=[],
    user_created_voice_channels={},
    blacklist=[],
)
default_member_CustomChannels = dict(currentRooms={})

default_guild_DynamicChannels = dict(
    dynamic_channels={},
    custom_channels={},
    user_created_voice_channels={},
    blacklist=[],
)
default_guild_RandomQuotes = {
    "enabled": False,
    "quotesToKeep": 100,
    "crossChannel": False,
    "perma": 1,
    "botPrefixes": [],
    "channels": {},
}
default_channel_RandomQuotes = {"quotes": {}, "permaQuotes": {}}
default_guild_GamingProfile = {
    "no_profile_role": None,
    "profile_role": None,
    "role_management": True,
}
default_channel_status = {"game": None}

ConfigHolder.AccountManager.register_user(**default_member_AccountManager)
ConfigHolder.GamingProfile.register_user(**default_member_GamingProfile)
ConfigHolder.GamingProfile.register_guild(**default_guild_GamingProfile)
ConfigHolder.PCSpecs.register_user(**default_member_PCSpecs)
ConfigHolder.PublisherManager.register_global(**default_custom_PublisherManager)
ConfigHolder.PlayerStatus.register_guild(**default_guild_StatusManager)
ConfigHolder.PlayerStatus.register_channel(**default_channel_status)
ConfigHolder.LogoData.register_global(**default_custom_Logos)
ConfigHolder.CustomChannels.register_guild(**default_guild_CustomChannels)
ConfigHolder.CustomChannels.register_member(**default_member_CustomChannels)
ConfigHolder.DynamicChannels.register_guild(**default_guild_DynamicChannels)
ConfigHolder.RandomQuotes.register_guild(**default_guild_RandomQuotes)
ConfigHolder.RandomQuotes.register_channel(**default_channel_RandomQuotes)
