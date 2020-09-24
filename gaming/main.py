from __future__ import annotations

# Standard Library
from pathlib import Path

# Cog Dependencies
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n

# Cog Relative Imports
from .configuration import GamingConfig
from .utils import CompositeMetaClass

_ = Translator("Gaming", Path(__file__).parent)


@cog_i18n(_)
class Gaming(
    GamingConfig,
    commands.Cog,
    metaclass=CompositeMetaClass,
):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config__account_manager: Config
        self.config__gaming_profile: Config
        self.config__pc_specs: Config
        self.config__publisher_manager: Config
        self.config__player_status: Config
        self.config__logo_data: Config
        self.config__dynamic_channels: Config
        self.config__custom_channels: Config
        self.config__random_quotes: Config
        self.init_config()
