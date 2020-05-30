# -*- coding: utf-8 -*-
# Standard Library
from typing import Final, Mapping

# Cog Dependencies
from redbot.core.data_manager import cog_data_path

__all__ = {
    "SCHEMA_VERSION",
    "ARG_PARSER_SCOPE_HELP",
    "ARG_PARSER_USER_HELP",
    "ARG_PARSER_GUILD_HELP",
    "HUMANIZED_PERMS_MAPPING",
    "DEFAULT_COG_SETTINGS_PERMISSIONS",
    "DEFAULT_COG_SETTINGS_LAVALINK",
    "DEFAULT_COG_SETTINGS_GUILD",
    "DEFAULT_COG_SETTINGS_GLOBAL",
    "DEFAULT_COG_SETTINGS_PLAYLISTS",
    "DEFAULT_COG_SETTINGS_USER",
    "DEFAULT_COG_SETTINGS_EQUALIZER",
}

SCHEMA_VERSION: Final[int] = 3

ARG_PARSER_SCOPE_HELP: Final[
    str
] = """
Scope must be a valid version of one of the following:
​ ​ ​ ​ Global
​ ​ ​ ​ Guild
​ ​ ​ ​ User
"""
ARG_PARSER_USER_HELP: Final[
    str
] = """
Author must be a valid version of one of the following:
​ ​ ​ ​ User ID
​ ​ ​ ​ User Mention
​ ​ ​ ​ User Name#123
"""
ARG_PARSER_GUILD_HELP: Final[
    str
] = """
Guild must be a valid version of one of the following:
​ ​ ​ ​ Guild ID
​ ​ ​ ​ Exact guild name
"""


HUMANIZED_PERMS_MAPPING: Final[Mapping[str, str]] = {
    "create_instant_invite": "Create Instant Invite",
    "kick_members": "Kick Members",
    "ban_members": "Ban Members",
    "administrator": "Administrator",
    "manage_channels": "Manage Channels",
    "manage_guild": "Manage Server",
    "add_reactions": "Add Reactions",
    "view_audit_log": "View Audit Log",
    "priority_speaker": "Priority Speaker",
    "stream": "Go Live",
    "read_messages": "Read Text Channels & See Voice Channels",
    "send_messages": "Send Messages",
    "send_tts_messages": "Send TTS Messages",
    "manage_messages": "Manage Messages",
    "embed_links": "Embed Links",
    "attach_files": "Attach Files",
    "read_message_history": "Read Message History",
    "mention_everyone": "Mention @everyone, @here, and All Roles",
    "external_emojis": "Use External Emojis",
    "view_guild_insights": "View Server Insights",
    "connect": "Connect",
    "speak": "Speak",
    "mute_members": "Mute Members",
    "deafen_members": "Deafen Members",
    "move_members": "Move Members",
    "use_voice_activation": "Use Voice Activity",
    "change_nickname": "Change Nickname",
    "manage_nicknames": "Manage Nicknames",
    "manage_roles": "Manage Roles",
    "manage_webhooks": "Manage Webhooks",
    "manage_emojis": "Manage Emojis",
}

DEFAULT_COG_SETTINGS_PERMISSIONS = {
    "embed_links": True,
    "read_messages": True,
    "send_messages": True,
    "read_message_history": True,
    "add_reactions": True,
}

DEFAULT_COG_SETTINGS_LAVALINK = {
    "host": "localhost",
    "rest_port": 2333,
    "password": "youshallnotpass",
    "region": "",
    "identifier": "Local",
}
DEFAULT_COG_SETTINGS_GUILD = {
    "auto_play": False,
    "autoplaylist": {"enabled": False, "id": None, "name": None, "scope": None},
    "persist_queue": True,
    "disconnect": False,
    "dj_enabled": False,
    "dj_role": None,
    "daily_playlists": False,
    "emptydc_enabled": False,
    "emptydc_timer": 0,
    "emptypause_enabled": False,
    "emptypause_timer": 0,
    "jukebox": False,
    "jukebox_price": 0,
    "maxlength": 0,
    "notify": False,
    "prefer_lyrics": False,
    "repeat": False,
    "shuffle": False,
    "shuffle_bumped": True,
    "thumbnail": False,
    "volume": 100,
    "vote_enabled": False,
    "vote_percent": 0,
    "room_lock": None,
    "url_keyword_blacklist": [],
    "url_keyword_whitelist": [],
    "country_code": "US",
}

DEFAULT_COG_SETTINGS_GLOBAL = {
    "schema_version": 1,
    "cache_level": 0,
    "cache_age": 365,
    "daily_playlists": False,
    "global_db_enabled": True,
    "global_db_get_timeout": 5,
    "status": False,
    "use_external_lavalink": False,
    "restrict": True,
    "localpath": str(cog_data_path(raw_name="Audio")),
    "url_keyword_blacklist": [],
    "url_keyword_whitelist": [],
    "nodes": {"0": DEFAULT_COG_SETTINGS_LAVALINK},
}

DEFAULT_COG_SETTINGS_GLOBAL.update(DEFAULT_COG_SETTINGS_LAVALINK)

DEFAULT_COG_SETTINGS_PLAYLISTS = {
    "id": None,
    "author": None,
    "name": None,
    "playlist_url": None,
    "tracks": [],
}

DEFAULT_COG_SETTINGS_EQUALIZER = {"eq_bands": [], "eq_presets": {}}
DEFAULT_COG_SETTINGS_USER = {"country_code": None}
