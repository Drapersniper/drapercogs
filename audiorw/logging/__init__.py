# -*- coding: utf-8 -*-
# Standard Library
import logging
import sys

from typing import Final

__all__ = {"is_debug", "debug_exc_log"}

_IS_DEBUG: Final[bool] = "--debug" in sys.argv


def is_debug() -> bool:
    return _IS_DEBUG


def debug_exc_log(lg: logging.Logger, exc: Exception, msg: str = None) -> None:
    """Logs an exception if logging is set to DEBUG level."""
    if _IS_DEBUG and lg.getEffectiveLevel() <= logging.DEBUG:
        if msg is None:
            msg = f"{exc}"
        lg.exception(msg, exc_info=exc)
