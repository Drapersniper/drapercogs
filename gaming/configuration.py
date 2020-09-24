# Cog Dependencies
from gaming.abc import GamingABC
from gaming.utils import CompositeMetaClass
from redbot.core import Config


class GamingConfig(GamingABC, metaclass=CompositeMetaClass):
    def init_config(self) -> None:
        self.config__account_manager = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="AccountManager"
        )
        self.config__gaming_profile = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="GamingProfile"
        )
        self.config__pc_specs = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="PCSpecs"
        )
        self.config__publisher_manager = Config.get_conf(
            None,
            identifier=208903205982044161,
            force_registration=True,
            cog_name="PublisherManager",
        )
        self.config__player_status = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="PlayerStatus"
        )
        self.config__logo_data = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="LogoData"
        )
        self.config__dynamic_channels = Config.get_conf(
            None,
            identifier=208903205982044161,
            force_registration=True,
            cog_name="DynamicChannels",
        )
        self.config__custom_channels = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="CustomChannels"
        )
        self.config__random_quotes = Config.get_conf(
            None, identifier=208903205982044161, force_registration=True, cog_name="RandomQuotes"
        )

        self.config__account_manager.register_user(account={"origin": None, "uplay": None})
        self.config__gaming_profile.register_user(
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
        self.config__gaming_profile.register_guild(
            no_profile_role=None, profile_role=None, role_management=True
        )

        self.config__pc_specs.register_user(
            rig={
                "CPU": None,
                "GPU": None,
                "RAM": None,
                "Motherboard": None,
                "Storage": None,
                "Monitor": None,
                "Mouse": None,
                "Keyboard": None,
                "Case": None,
            }
        )
        self.config__publisher_manager.register_global(
            services={
                "battlenet": {
                    "name": "Battle.net",
                    "games": ["Call of Duty: Modern Warfare"],
                },
                "epic": {"name": "Epic Games", "games": []},
                "gog": {"name": "GOG.com", "games": []},
                "mixer": {"name": "Mixer", "games": []},
                "psn": {"name": "PlayStation Network", "games": []},
                "reddit": {"name": "Reddit", "games": []},
                "riot": {
                    "name": "Riot Games",
                    "games": ["League of Legends"],
                },
                "spotify": {"name": "Spotify", "games": []},
                "steam": {"name": "Steam", "games": []},
                "twitch": {"name": "Twitch", "games": []},
                "twitter": {"name": "Twitter", "games": []},
                "uplay": {
                    "name": "Uplay",
                    "games": ["Tom Clancy's The Division 2"],
                },
                "xbox": {"name": "Xbox Live", "games": []},
                "youtube": {"name": "YouTube", "games": []},
                "origin": {
                    "name": "Origin",
                    "games": ["Apex Legends", "Battlefield\u2122 V", "Anthem\u2122"],
                },
                "facebook": {
                    "name": "Facebook",
                    "games": [],
                },
                "instagram": {
                    "name": "Instagram",
                    "games": [],
                },
                "snapchat": {
                    "name": "Snapchat",
                    "games": [],
                },
                "mojang": {"name": "Mojang", "games": []},
                "skype": {"name": "Skype", "games": []},
                "soundcloud": {
                    "name": "SoundCloud",
                    "games": [],
                },
                "nintendo": {"name": "Nintendo", "games": []},
                "runescape": {
                    "name": "Jagex",
                    "games": ["RuneLite", "OSBuddy", "Old School Runescape", "RuneScape"],
                },
            },
            publisher={
                "RuneLite": "runescape",
                "OSBuddy": "runescape",
                "Old School Runescape": "runescape",
                "RuneScape": "runescape",
            },
        )

        self.config__player_status.register_guild(channel_game_name={})
        self.config__logo_data.register_global(
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
        self.config__custom_channels.register_guild(
            mute_roles=[],
            category_with_button={},
            custom_channels={},
            user_created_voice_channels_bypass_roles=[],
            user_created_voice_channels={},
            blacklist=[],
        )
        self.config__custom_channels.register_user(currentRooms={})
        self.config__dynamic_channels.register_guild(
            dynamic_channels={}, custom_channels={}, user_created_voice_channels={}, blacklist=[]
        )
        self.config__random_quotes.register_guild(
            enabled=False, quotesToKeep=100, crossChannel=False, perma=1, channels={}
        )
        self.config__random_quotes.register_channel(quotes={}, permaQuotes={})
