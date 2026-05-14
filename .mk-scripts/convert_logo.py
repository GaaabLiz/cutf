#!/usr/bin/env python
"""
convert_logo.py – Convert a .svg logo to all standard icon/image formats.

Usage:
    uv run python .mk-scripts/convert_logo.py <path/to/logo.svg>

Generates in the SAME directory as the source SVG:
  • PNG  – 16, 32, 48, 64, 128, 256, 512, 1024 px
  • JPG  – 64, 128, 256, 512, 1024 px  (white background, 95 % quality)
  • ICO  – multi-size  (16, 24, 32, 48, 64, 128, 256 px)
  • ICNS – macOS icon  (16, 32, 64, 128, 256, 512, 1024 px)

Renderer: skia-python  – ships pre-compiled Skia wheels on PyPI,
          zero system-library dependencies (no cairo, no ImageMagick).
"""

from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

# ── Sizes ─────────────────────────────────────────────────────────────────────

PNG_SIZES  = [16, 32, 48, 64, 128, 256, 512, 1024]
JPG_SIZES  = [64, 128, 256, 512, 1024]
ICO_SIZES  = [16, 24, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]

# Apple ICNS OSType codes per pixel size (1x variants – PNG-compressed entries)
ICNS_TYPES: dict[int, bytes] = {
    16:   b"icp4",
    32:   b"icp5",
    64:   b"icp6",
    128:  b"ic07",
    256:  b"ic08",
    512:  b"ic09",
    1024: b"ic10",
}

# ── SVG renderer (skia-python) ────────────────────────────────────────────────

def _render_svg(svg_path: Path, size: int) -> bytes:
    """
    Render *svg_path* at *size* × *size* pixels using Skia.
    Returns raw PNG bytes (RGBA).
    """
    import skia  # type: ignore[import-untyped]

    svg_bytes = svg_path.read_bytes()
    stream    = skia.MemoryStream(svg_bytes)
    svg_dom   = skia.SVGDOM.MakeFromStream(stream)
    if svg_dom is None:
        raise RuntimeError(f"Skia could not parse SVG: {svg_path}")

    surface = skia.Surface(size, size)
    with surface as canvas:
        canvas.clear(skia.ColorTRANSPARENT)
        svg_dom.setContainerSize(skia.Size.Make(size, size))
        svg_dom.render(canvas)

    image   = surface.makeImageSnapshot()
    png_data = image.encodeToData()
    return bytes(png_data)


# ── Image helpers ─────────────────────────────────────────────────────────────

def _open_rgba(png_bytes: bytes):
    """Open raw PNG bytes as a PIL RGBA Image."""
    from PIL import Image  # type: ignore[import-untyped]
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _resize(base_img, size: int):
    from PIL import Image  # type: ignore[import-untyped]
    return base_img.resize((size, size), Image.LANCZOS)


def _to_png_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ── ICNS builder ──────────────────────────────────────────────────────────────

def _build_icns(png_map: dict[int, bytes]) -> bytes:
    """
    Hand-craft an ICNS binary from {size: png_bytes}.

    ICNS layout:
        magic   4 bytes  b"icns"
        length  4 bytes  total file length (big-endian uint32)
        entries …
            type    4 bytes
            length  4 bytes  (type + length + data)
            data    N bytes  PNG bytes (ic07 … ic10 / icp4 … icp6)
    """
    body = b""
    for size in sorted(png_map):
        ostype = ICNS_TYPES.get(size)
        if ostype is None:
            continue
        data  = png_map[size]
        body += ostype + struct.pack(">I", 8 + len(data)) + data
    return b"icns" + struct.pack(">I", 8 + len(body)) + body


# ── Main conversion ───────────────────────────────────────────────────────────

def convert(svg_path: Path) -> None:
    if not svg_path.exists():
        print(f"ERROR: file not found: {svg_path}", file=sys.stderr)
        sys.exit(1)
    if svg_path.suffix.lower() != ".svg":
        print(f"ERROR: expected a .svg file, got: {svg_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = svg_path.parent
    stem    = svg_path.stem

    print(f"Source : {svg_path}")
    print(f"Output : {out_dir}/")
    print()

    # Render at the largest size once; downscale from that master image.
    max_size = max(PNG_SIZES + ICNS_SIZES)
    print(f"Rendering SVG at {max_size}×{max_size} px (skia-python) …")
    base_img = _open_rgba(_render_svg(svg_path, max_size))
    print()

    from PIL import Image as _Image  # type: ignore[import-untyped]

    # ── PNG ──────────────────────────────────────────────────────────────────
    print("PNG files:")
    for size in PNG_SIZES:
        img      = _resize(base_img, size)
        out_path = out_dir / f"{stem}-{size}x{size}.png"
        img.save(out_path, format="PNG", optimize=True)
        print(f"  {out_path}")
    print()

    # ── JPG ──────────────────────────────────────────────────────────────────
    print("JPG files:")
    for size in JPG_SIZES:
        rgba = _resize(base_img, size)
        bg   = _Image.new("RGB", (size, size), (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[3])        # composite over white bg
        out_path = out_dir / f"{stem}-{size}x{size}.jpg"
        bg.save(out_path, format="JPEG", quality=95, optimize=True)
        print(f"  {out_path}")
    print()

    # ── ICO ───────────────────────────────────────────────────────────────────
    print("ICO file:")
    ico_images = [_resize(base_img, s) for s in ICO_SIZES]
    ico_path   = out_dir / f"{stem}.ico"
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path}")
    print()

    # ── ICNS ─────────────────────────────────────────────────────────────────
    print("ICNS file:")
    icns_png_map = {s: _to_png_bytes(_resize(base_img, s)) for s in ICNS_SIZES}
    icns_path    = out_dir / f"{stem}.icns"
    icns_path.write_bytes(_build_icns(icns_png_map))
    print(f"  {icns_path}")
    print()

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_logo.py <path/to/logo.svg>", file=sys.stderr)
        sys.exit(1)
    convert(Path(sys.argv[1]))


