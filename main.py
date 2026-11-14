#!/usr/bin/env python3
"""food-picture-01 delivery runner: wagyu steak, butter still melting.

``image.png`` next to this script is the finished photograph.  The
script's single job is to prove the file obeys the contest limits and
then to copy it, untouched, into ``$MAKEFUN_OUTPUT_DIR`` as
``entry.png``.  Validation covers the byte ceiling (1 MiB), the format
(PNG or JPEG, sniffed from the leading bytes) and the pixel ceiling
(1024 on either side, read from the PNG IHDR or the first JPEG
start-of-frame segment).

Standard library only; the copy is a plain byte transfer, so two runs
always agree.
"""

import hashlib
import os
import struct
import sys
from pathlib import Path

LIMIT_BYTES = 1024 * 1024
LIMIT_SIDE = 1024

SIGNATURE_PNG = b"\x89PNG\r\n\x1a\n"
SIGNATURE_JPEG = b"\xff\xd8\xff"
SOF_CODES = (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
             0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)


def complain(message):
    """Print a diagnostic to stderr; callers turn it into an exit code."""
    print("error: " + message, file=sys.stderr)


def png_frame(blob):
    """Extract width and height from the IHDR chunk of a PNG."""
    if len(blob) < 24:
        raise ValueError("PNG is too short for an IHDR chunk")
    size = struct.unpack(">I", blob[8:12])[0]
    kind = blob[12:16]
    if kind != b"IHDR" or size != 13:
        raise ValueError("first PNG chunk is not the 13-byte IHDR")
    w, h = struct.unpack(">II", blob[16:24])
    return w, h


def jpeg_frame(blob):
    """Scan JPEG segments for a start-of-frame marker and read its size."""
    at = 2
    end = len(blob)
    while at + 4 <= end:
        if blob[at] != 0xFF:
            raise ValueError("JPEG marker prefix missing at %d" % at)
        code = blob[at + 1]
        if code in SOF_CODES:
            if at + 9 > end:
                raise ValueError("JPEG frame segment is cut short")
            h, w = struct.unpack(">HH", blob[at + 5:at + 9])
            return w, h
        length = struct.unpack(">H", blob[at + 2:at + 4])[0]
        if length < 2:
            raise ValueError("JPEG segment length underflows")
        at += length + 2
    raise ValueError("JPEG carries no start-of-frame segment")


def examine(blob):
    """Return a report dict for a payload, or raise ValueError."""
    report = {"bytes": len(blob), "format": None, "width": 0, "height": 0}
    if report["bytes"] == 0:
        raise ValueError("image.png is an empty file")
    if report["bytes"] > LIMIT_BYTES:
        raise ValueError(
            "image weighs %d bytes, above the %d cap"
            % (report["bytes"], LIMIT_BYTES)
        )
    if blob.startswith(SIGNATURE_PNG):
        report["format"] = "png"
        report["width"], report["height"] = png_frame(blob)
    elif blob.startswith(SIGNATURE_JPEG):
        report["format"] = "jpeg"
        report["width"], report["height"] = jpeg_frame(blob)
    else:
        raise ValueError("leading bytes match neither PNG nor JPEG")
    if report["width"] < 1 or report["height"] < 1:
        raise ValueError(
            "frame of %dx%d is not plausible"
            % (report["width"], report["height"])
        )
    if report["width"] > LIMIT_SIDE or report["height"] > LIMIT_SIDE:
        raise ValueError(
            "frame of %dx%d breaks the %d-pixel cap"
            % (report["width"], report["height"], LIMIT_SIDE)
        )
    return report


def run():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if not out:
        complain("MAKEFUN_OUTPUT_DIR is not set")
        return 2
    here = Path(__file__).resolve().parent
    source = here / "image.png"
    if not source.is_file():
        complain("bundled image not found at %s" % source)
        return 2
    try:
        blob = source.read_bytes()
        report = examine(blob)
    except (OSError, ValueError) as problem:
        complain(str(problem))
        return 1
    dest_dir = Path(out)
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "entry.png"
        dest.write_bytes(blob)
        if dest.stat().st_size != report["bytes"]:
            complain("output size drifted from the source image")
            return 1
        check = dest.read_bytes()
    except OSError as problem:
        complain("could not write the output: %s" % problem)
        return 1
    if check != blob:
        complain("output bytes drifted from the source image")
        return 1
    tag = hashlib.sha256(blob).hexdigest()[:16]
    print("wrote %s (%d bytes, %s %dx%d, sha256:%s)"
          % (dest, report["bytes"], report["format"],
             report["width"], report["height"], tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
