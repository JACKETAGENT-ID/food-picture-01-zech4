#!/usr/bin/env python3
"""food-picture-01 entry (round 4): sliced wagyu steak delivery.

The artwork ships inside the repository as ``image.png`` next to this
file: an editorial close-up of a thick wagyu ribeye sliced open --
fanned medium-rare slices with heavy marbling, butter melting over the
seared crust, juices pooling and steam rising.  Running the program
checks the payload against the competition limits (PNG or JPEG, at
most 1 MiB, at most 1024x1024) and then copies it unchanged to
``$MAKEFUN_OUTPUT_DIR/entry.png`` so repeated runs produce identical
bytes.

Standard library only.
"""

from __future__ import annotations

import hashlib
import os
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_SIDE = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"

# JPEG start-of-frame markers that carry the frame dimensions.
_JPEG_SOF = frozenset(
    (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
)


class EntryError(RuntimeError):
    """Raised when the bundled steak image fails validation."""


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) parsed from the PNG IHDR chunk."""
    if len(data) < 24:
        raise EntryError("PNG payload too short to contain an IHDR chunk")
    chunk_len = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR" or chunk_len != 13:
        raise EntryError("first PNG chunk is not a 13-byte IHDR")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) by walking JPEG segments to a SOF marker."""
    pos = 2  # skip SOI
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise EntryError("malformed JPEG: expected 0xFF segment marker")
        marker = data[pos + 1]
        if marker in _JPEG_SOF:
            if pos + 9 > len(data):
                raise EntryError("truncated JPEG SOF segment")
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if seg_len < 2:
            raise EntryError("malformed JPEG: bad segment length")
        pos += 2 + seg_len
    raise EntryError("no SOF marker found in JPEG payload")


def validate(payload: bytes) -> tuple[int, int]:
    """Validate size, magic bytes and dimensions; return (width, height)."""
    if not payload:
        raise EntryError("image.png is empty")
    if len(payload) > MAX_BYTES:
        raise EntryError(
            f"image is {len(payload)} bytes, over the {MAX_BYTES}-byte limit"
        )
    if payload.startswith(PNG_MAGIC):
        width, height = png_dimensions(payload)
    elif payload.startswith(JPEG_MAGIC):
        width, height = jpeg_dimensions(payload)
    else:
        raise EntryError("image.png is neither PNG nor JPEG (bad magic bytes)")
    if width < 1 or height < 1:
        raise EntryError(f"implausible image dimensions {width}x{height}")
    if width > MAX_SIDE or height > MAX_SIDE:
        raise EntryError(
            f"image is {width}x{height}, over the {MAX_SIDE}x{MAX_SIDE} limit"
        )
    return width, height


def main() -> int:
    out_dir_raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if not out_dir_raw:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    source = Path(__file__).resolve().parent / "image.png"
    if not source.is_file():
        print(f"error: bundled image not found at {source}", file=sys.stderr)
        return 2
    try:
        payload = source.read_bytes()
        width, height = validate(payload)
    except (OSError, EntryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out_dir = Path(out_dir_raw)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / "entry.png"
        dest.write_bytes(payload)
        written = dest.read_bytes()
    except OSError as exc:
        print(f"error: could not write output: {exc}", file=sys.stderr)
        return 1
    # Determinism guard: the delivered file must be the validated steak
    # payload, byte for byte, so two runs always yield identical output.
    if written != payload:
        print("error: written output differs from the bundled image",
              file=sys.stderr)
        return 1
    digest = hashlib.sha256(payload).hexdigest()[:16]
    print(f"wrote {dest} ({len(payload)} bytes, {width}x{height}, "
          f"sha256:{digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
