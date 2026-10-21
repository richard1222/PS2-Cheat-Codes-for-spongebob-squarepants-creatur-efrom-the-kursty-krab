"""Read-only NDS ARM9 header validation and debug-reference analysis."""
import hashlib
import struct
from arm9_call_context import context

MAX_NDS = 256 * 1024 * 1024
MAX_ARM9 = 32 * 1024 * 1024

def inspect_nds(data, terms, radius=12, max_hits=100):
    if not 0x200 <= len(data) <= MAX_NDS:
        raise ValueError('NDS input must be between 512 bytes and 256 MiB')
    offset, entry, base, size = struct.unpack_from('<4I', data, 0x20)
    if offset < 0x200 or not 0 < size <= MAX_ARM9 or offset + size > len(data):
        raise ValueError('invalid ARM9 extent')
    if base + size > 0x100000000 or not base <= entry < base + size:
        raise ValueError('invalid ARM9 load address or entrypoint')
    arm9 = data[offset:offset + size]
    result = context(arm9, base, terms, radius, max_hits)
    return {'platform': 'Nintendo DS', 'sha256': hashlib.sha256(data).hexdigest(),
            'game_code': data[12:16].decode('ascii', errors='replace'),
            'arm9': {'rom_offset': offset, 'entrypoint': entry, 'load_address': base,
                     'size': size, 'sha256': hashlib.sha256(arm9).hexdigest()},
            'arm9_debug_analysis': result,
            'note': 'Static candidates only; DS code cannot be patched directly into a PS2 ISO.'}
