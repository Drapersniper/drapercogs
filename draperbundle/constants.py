# -*- coding: utf-8 -*-
import regex


CONTINENT_DATA = {
    "1": "Europe",
    "2": "Africa",
    "3": "North America",
    "4": "Asia",
    "5": "Oceania",
    "6": "South America",
}
TIMEZONE_REGEX = regex.compile(r"UTC[+-]([01]\d|2[0-4])(:?[0-5]\d)?|UTC[+-]\d", regex.I)

UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
REPLACE_BRACKER = regex.compile(r"\((?:[^()]++|(?R))*+\)")
NAMEFIXER = regex.compile(
    r"^[\p{Punctuation}\p{Symbol}\p{Letter_Number}\p{Other_Number}\p{Punctuation}\p{Mark}\p{Separator}]*"
)
QUOTE_CLEANER = regex.compile(
    r"^(<+[\p{P}\p{Sm}\p{Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}]*>+)*$|"
    r"^(:+[\p{P}\p{Sm}\p{Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}\p{L}]*:+)*$|"
    r"^([:<]+[\p{L}\p{N}\p{P}]+[:>]+)+$",
    regex.I | regex.M,
)
URLMATCHER = regex.compile(
    r"(?:(?:https?|ftp)://|"
    r"\b(?:[a-z\d]+.))(?:(?:[^\s()<>]+|((?:[^\s()<>]+|"
    r"(?:([^\s()<>]+)))?))+(?:((?:[^\s()<>]+|(?:(?:[^\s()<>]+)))?)|"
    r"[^\s`!()[]{};:'\".,<>?«»“�?‘’]))?",
    regex.I,
)

bfv_icon = "https://cdn.discordapp.com/app-icons/512699108809637890/5f70bb592b9efbad9b5973404b9b7d01.png"
anthem_icon = "https://cdn.discordapp.com/app-icons/546175179542364160/4a0b14af7ed47532e7e4676b637bdf3f.png"
apex_icon = "https://cdn.discordapp.com/app-icons/542075586886107149/7564e6f23704870d70480f172f127677.png"
spotify_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Spotify_logo_with_text.svg/559px-Spotify_logo_with_text.svg.png"
division_2_icon = "https://cdn.discordapp.com/app-icons/554921822626381879/aadb17a9cb43c0d24bd270406fecb87d.png"
osrs_icon = "https://cdn.discordapp.com/app-icons/357606832899883008/337ce51307d4580001d1ab60706dda8a.png"
csgo_icon = "https://cdn.discordapp.com/app-icons/356875057940791296/782a3bb612c6f1b3f7deed554935f361.png"
lol_icon = (
    "https://cdn.discordapp.com/app-assets/401518684763586560/416719019576393738.png"
)
minecraft_icon = "https://cdn.discordapp.com/app-icons/356875570916753438/166fbad351ecdd02d11a3b464748f66b.png"
codmw_icon = "https://cdn.discordapp.com/attachments/557869681721999370/637186507475779585/communityIcon_8jyqgoe3xk131.png"
