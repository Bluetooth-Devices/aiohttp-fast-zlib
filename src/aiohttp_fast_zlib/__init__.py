"""Fast zlib module for aiohttp."""

__version__ = "0.3.0"

import contextlib
import importlib
import logging
import zlib as zlib_original
from typing import TYPE_CHECKING

import aiohttp

_LOGGER = logging.getLogger(__name__)

_AIOHTTP_SPLIT_VERSION = aiohttp.__version__.split(".")
_AIOHTTP_VERSION = (int(_AIOHTTP_SPLIT_VERSION[0]), int(_AIOHTTP_SPLIT_VERSION[1]))

if TYPE_CHECKING:
    best_zlib = zlib_original

try:
    from isal import isal_zlib as best_zlib  # type: ignore
except ImportError:
    try:
        from zlib_ng import zlib_ng as best_zlib  # type: ignore
    except ImportError:
        best_zlib = zlib_original

TARGETS = [
    "compression_utils",
    "http_writer",
    "http_writer",
    "http_parser",
    "multipart",
    "web_response",
]

_PATCH_WEBSOCKET_WRITER = False
_USE_NATIVE_ZLIB_BACKEND = False

# Check if aiohttp has native set_zlib_backend support (3.12+)
if _AIOHTTP_VERSION >= (3, 12):
    from aiohttp import set_zlib_backend

    _USE_NATIVE_ZLIB_BACKEND = True
elif _AIOHTTP_VERSION >= (3, 11):
    _PATCH_WEBSOCKET_WRITER = True
else:
    TARGETS.append("http_websocket")


def enable() -> None:
    """Enable fast zlib."""
    if best_zlib is zlib_original:
        _LOGGER.warning(
            "zlib_ng and isal are not available, falling back to zlib"
            ", performance will be degraded."
        )
        return

    if _USE_NATIVE_ZLIB_BACKEND:
        set_zlib_backend(best_zlib)
        return
    # Use patching for older versions
    _patch_modules()


def disable() -> None:
    """Disable fast zlib and restore the original zlib."""
    if _USE_NATIVE_ZLIB_BACKEND:
        # Use native aiohttp 3.12+ API
        set_zlib_backend(zlib_original)
        return
    # Use patching for older versions
    _unpatch_modules()


def _patch_modules() -> None:
    """Patch aiohttp modules to use best_zlib."""
    for location in TARGETS:
        try:
            importlib.import_module(f"aiohttp.{location}")
        except ImportError:
            continue
        if module := getattr(aiohttp, location, None):
            module.zlib = best_zlib
    if _PATCH_WEBSOCKET_WRITER:
        with contextlib.suppress(ImportError):
            mod = importlib.import_module("aiohttp._websocket.writer")
            mod.zlib = best_zlib  # type: ignore[attr-defined]


def _unpatch_modules() -> None:
    """Unpatch aiohttp modules to use original zlib."""
    for location in TARGETS:
        if module := getattr(aiohttp, location, None):
            module.zlib = zlib_original
    if _PATCH_WEBSOCKET_WRITER:
        with contextlib.suppress(ImportError):
            mod = importlib.import_module("aiohttp._websocket.writer")
            mod.zlib = zlib_original  # type: ignore[attr-defined]
