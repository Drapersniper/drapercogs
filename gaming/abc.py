from __future__ import annotations

# Standard Library
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core import Config
    from redbot.core.bot import Red


class GamingABC(ABC):
    """Base class for well behaved type hint detection with composite class.

    Basically, to keep developers sane when not all attributes are defined in each mixin.
    """

    bot: Red
    config__account_manager: Config
    config__gaming_profile: Config
    config__pc_specs: Config
    config__publisher_manager: Config
    config__player_status: Config
    config__logo_data: Config
    config__dynamic_channels: Config
    config__custom_channels: Config
    config__random_quotes: Config

    @abstractmethod
    def init_config(self) -> None:
        raise NotImplementedError
