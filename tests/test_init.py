import zlib as zlib_original
from unittest.mock import patch

import aiohttp.compression_utils
import aiohttp.http_websocket
import pytest

import aiohttp_fast_zlib

try:
    from isal import (
        isal_zlib as expected_zlib,
    )
except ImportError:
    from zlib_ng import zlib_ng as expected_zlib

if (3, 11) <= aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 12):
    from aiohttp._websocket import writer
if aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 12):
    from aiohttp.compression_utils import ZLibBackend


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 11),
    reason="Only works with aiohttp less than 3.11+",
)
def test_enable_disable_pre_311():
    """Test enable/disable."""
    assert aiohttp.http_websocket.zlib is zlib_original
    aiohttp_fast_zlib.enable()
    assert aiohttp.http_websocket.zlib is expected_zlib
    aiohttp_fast_zlib.disable()
    assert aiohttp.http_websocket.zlib is zlib_original
    aiohttp_fast_zlib.enable()
    assert aiohttp.http_websocket.zlib is expected_zlib
    aiohttp_fast_zlib.disable()


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 11)
    or aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 12),
    reason="Only works with aiohttp 3.11.x",
)
def test_enable_disable_311():
    """Test enable/disable for aiohttp 3.11.x."""
    assert writer.zlib is zlib_original
    aiohttp_fast_zlib.enable()
    assert writer.zlib is expected_zlib
    aiohttp_fast_zlib.disable()
    assert writer.zlib is zlib_original
    aiohttp_fast_zlib.enable()
    assert writer.zlib is expected_zlib
    aiohttp_fast_zlib.disable()


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 11)
    or aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 12),
    reason="Only works with aiohttp 3.11.x",
)
def test_enable_disable_when_all_missing_311():
    """Test enable/disable for aiohttp 3.11.x when all fast libs are missing."""
    with patch.object(aiohttp_fast_zlib, "best_zlib", zlib_original):
        assert writer.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert writer.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert writer.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert writer.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert writer.zlib is zlib_original


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 11),
    reason="Only works with aiohttp less than 3.11+",
)
def test_enable_disable_when_all_missing_pre_311():
    """Test enable/disable."""
    with patch.object(aiohttp_fast_zlib, "best_zlib", zlib_original):
        assert aiohttp.http_websocket.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert aiohttp.http_websocket.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert aiohttp.http_websocket.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert aiohttp.http_websocket.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert aiohttp.http_websocket.zlib is zlib_original


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 12),
    reason="Only works with aiohttp < 3.12",
)
def test_enable_disable_when_all_missing():
    """Test enable/disable when all fast libs are missing."""
    with patch.object(aiohttp_fast_zlib, "best_zlib", zlib_original):
        assert aiohttp.compression_utils.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert aiohttp.compression_utils.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert aiohttp.compression_utils.zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert aiohttp.compression_utils.zlib is zlib_original
        aiohttp_fast_zlib.disable()
        assert aiohttp.compression_utils.zlib is zlib_original


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 12),
    reason="Only works with aiohttp >= 3.12",
)
def test_enable_disable_312_plus():
    """Test enable/disable for aiohttp 3.12+ with native set_zlib_backend."""
    # Test enable
    aiohttp_fast_zlib.enable()
    assert ZLibBackend._zlib_backend is expected_zlib

    # Test disable
    aiohttp_fast_zlib.disable()
    assert ZLibBackend._zlib_backend is zlib_original

    # Test enable again
    aiohttp_fast_zlib.enable()
    assert ZLibBackend._zlib_backend is expected_zlib

    # Clean up
    aiohttp_fast_zlib.disable()
    assert ZLibBackend._zlib_backend is zlib_original


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 12),
    reason="Only works with aiohttp >= 3.12",
)
def test_enable_disable_when_all_missing_312_plus():
    """Test enable/disable for aiohttp 3.12+ when all fast libs are missing."""
    # Store the original backend
    original_backend = ZLibBackend._zlib_backend

    with patch.object(aiohttp_fast_zlib, "best_zlib", zlib_original):
        # Test enable - should not change backend when best_zlib is zlib_original
        aiohttp_fast_zlib.enable()
        assert ZLibBackend._zlib_backend is original_backend

        # Test disable - should not change backend either
        aiohttp_fast_zlib.disable()
        assert ZLibBackend._zlib_backend is original_backend


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION < (3, 12),
    reason="Only works with aiohttp >= 3.12",
)
def test_compression_roundtrip_312_plus():
    """Fast backend output must be zlib-compatible on the 3.12+ native path."""
    # Asserting on the private ``_zlib_backend`` attribute only proves the
    # object was installed, not that it actually works. The library promises a
    # *drop-in* replacement, so verify output from the fast backend round trips
    # through the stdlib zlib (and vice versa).
    data = b"the quick brown fox jumps over the lazy dog " * 256

    try:
        aiohttp_fast_zlib.enable()
        # Fast backend is selected and reports itself via the public name.
        assert ZLibBackend._zlib_backend is expected_zlib
        assert ZLibBackend.name == expected_zlib.__name__

        # Compress with the fast backend, decompress with stdlib zlib.
        compressor = ZLibBackend.compressobj(wbits=15)
        compressed = compressor.compress(data) + compressor.flush()
        assert zlib_original.decompress(compressed) == data

        # Reverse direction: stdlib output decompresses through the backend.
        stdlib_compressed = zlib_original.compress(data)
        decompressor = ZLibBackend.decompressobj(wbits=15)
        restored = decompressor.decompress(stdlib_compressed) + decompressor.flush()
        assert restored == data
    finally:
        aiohttp_fast_zlib.disable()

    # After disable the stdlib backend is restored and still round trips.
    assert ZLibBackend._zlib_backend is zlib_original
    compressor = ZLibBackend.compressobj(wbits=15)
    compressed = compressor.compress(data) + compressor.flush()
    assert zlib_original.decompress(compressed) == data


@pytest.mark.skipif(
    aiohttp_fast_zlib._AIOHTTP_VERSION >= (3, 12),
    reason="Only the module-patching path applies below aiohttp 3.12",
)
def test_compression_roundtrip_pre_312():
    """Patched backend output must be zlib-compatible on the <3.12 patching path."""
    # On older aiohttp the library swaps the ``zlib`` reference on each target
    # module instead of using a native backend hook. The existing tests only
    # assert object identity; this proves the patched backend actually produces
    # zlib-compatible output. ``compression_utils`` is patched on every <3.12
    # path, so it is the common surface to exercise.
    data = b"the quick brown fox jumps over the lazy dog " * 256

    try:
        aiohttp_fast_zlib.enable()
        assert aiohttp.compression_utils.zlib is expected_zlib

        # Compress with the fast backend, decompress with stdlib zlib.
        compressed = aiohttp.compression_utils.zlib.compress(data)
        assert zlib_original.decompress(compressed) == data

        # Reverse direction: stdlib output decompresses through the backend.
        stdlib_compressed = zlib_original.compress(data)
        assert aiohttp.compression_utils.zlib.decompress(stdlib_compressed) == data
    finally:
        aiohttp_fast_zlib.disable()

    # After disable the stdlib backend is restored and still round trips.
    assert aiohttp.compression_utils.zlib is zlib_original
    compressed = aiohttp.compression_utils.zlib.compress(data)
    assert zlib_original.decompress(compressed) == data
