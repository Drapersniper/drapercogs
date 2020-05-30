# -*- coding: utf-8 -*-
# Cog Dependencies
from redbot.core import Config
from redbot.core.bot import Red

# Cog Relative Imports
from .autodc import AutoDCManager
from .autoplay import AutoPlayManager
from .blacklist_whitelist import WhitelistBlacklistManager
from .caching_level import CachingLevelManager
from .country_code import CountryCodeManager
from .daily_global_playlist import DailyGlobalPlaylistManager
from .daily_playlist import DailyPlaylistManager
from .dj_roles import DJRoleManager
from .dj_status import DJStatusManager
from .emptydc import EmptyDCManager
from .emptydc_timer import EmptyDCTimerManager
from .emptypause import EmptyPauseManager
from .emptypause_timer import EmptyPauseTimerManager
from .globaldb import GlobalDBManager
from .globaldb_timeout import GlobalDBTimeoutManager
from .localpath import LocalPathManager
from .persist_queue import PersistentQueueManager
from .shuffle import ShuffleManager
from .shuffle_bumped import ShuffleBumpedManager
from .thumbnail import ThumbnailManager
from .votes_percentage import VotesPercentageManager
from .voting import VotingManager

__all__ = {"SettingCacheManager"}


class SettingCacheManager:
    def __init__(self, bot: Red, config: Config, enable_cache: bool = True) -> None:
        self._config: Config = config
        self.bot: Red = bot
        self.enabled = enable_cache

        self.blacklist_whitelist = WhitelistBlacklistManager(bot, config, self.enabled)
        self.dj_roles = DJRoleManager(bot, config, self.enabled)
        self.dj_status = DJStatusManager(bot, config, self.enabled)
        self.daily_playlist = DailyPlaylistManager(bot, config, self.enabled)
        self.daily_global_playlist = DailyGlobalPlaylistManager(bot, config, self.enabled)
        self.persistent_queue = PersistentQueueManager(bot, config, self.enabled)
        self.votes = VotingManager(bot, config, self.enabled)
        self.votes_percentage = VotesPercentageManager(bot, config, self.enabled)
        self.shuffle = ShuffleManager(bot, config, self.enabled)
        self.shuffle_bumped = ShuffleBumpedManager(bot, config, self.enabled)
        self.autoplay = AutoPlayManager(bot, config, self.enabled)
        self.thumbnail = ThumbnailManager(bot, config, self.enabled)
        self.localpath = LocalPathManager(bot, config, self.enabled)
        self.auto_dc = AutoDCManager(bot, config, self.enabled)
        self.empty_dc = EmptyDCManager(bot, config, self.enabled)
        self.empty_dc_timer = EmptyDCTimerManager(bot, config, self.enabled)
        self.empty_pause = EmptyPauseManager(bot, config, self.enabled)
        self.empty_pause_timer = EmptyPauseTimerManager(bot, config, self.enabled)
        self.globaldb = GlobalDBManager(bot, config, self.enabled)
        self.globaldb_timeout = GlobalDBTimeoutManager(bot, config, self.enabled)
        self.caching_level = CachingLevelManager(bot, config, self.enabled)
        self.country_code = CountryCodeManager(bot, config, self.enabled)
