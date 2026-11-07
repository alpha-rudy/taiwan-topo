#!/usr/bin/env python3
"""Build the MapLibre sprite for styles/pmtiles_style/style.json.

Usage: pmtiles-sprite.py <style.json> <icon_dir> <out_dir>

Every icon-image in the style is named "<file stem>-<px>": a file in
<icon_dir> (the Mapsforge theme's moiosm_res/, .svg or .png) drawn <px> pixels
high, which is the theme's symbol size times tiles.rudymap.tw's symbol-scale of
1.5. The icons are rendered with rsvg-convert (SVG) or Pillow (PNG) and packed
into <out_dir>/sprite.png + sprite.json, and twice the size into
sprite@2x.png + sprite@2x.json.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

NAME = re.compile(r"^(.+)-(\d+)$")
ROW_WIDTH = 512


def icon_names(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "icon-image" and isinstance(v, str):
                out.add(v)
            else:
                icon_names(v, out)
    elif isinstance(node, list):
        for v in node:
            icon_names(v, out)
    return out


def render(path, px, tmp):
    if path.endswith(".svg"):
        out = os.path.join(tmp, "icon.png")
        subprocess.run(["rsvg-convert", "--keep-aspect-ratio", "-h", str(px), "-o", out, path], check=True)
        return Image.open(out).convert("RGBA")
    im = Image.open(path).convert("RGBA")
    w = max(1, round(im.width * px / im.height))
    return im.resize((w, px), Image.LANCZOS)


def main():
    style_path, icon_dir, out_dir = sys.argv[1:4]
    names = sorted(icon_names(json.load(open(style_path)), set()))
    files = {}
    for n in names:
        m = NAME.match(n)
        if not m:
            sys.exit("icon-image %r is not <file stem>-<px>" % n)
        stem, px = m.group(1), int(m.group(2))
        for ext in (".svg", ".png"):
            p = os.path.join(icon_dir, stem + ext)
            if os.path.exists(p):
                files[n] = (p, px)
                break
        else:
            sys.exit("no %s.svg or .png in %s" % (stem, icon_dir))
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for ratio, suffix in ((1, ""), (2, "@2x")):
            images = {n: render(p, px * ratio, tmp) for n, (p, px) in files.items()}
            # shelf packing, tallest first; positions are computed per ratio
            order = sorted(images, key=lambda n: (-images[n].height, n))
            x = y = shelf = 0
            pos = {}
            width = ROW_WIDTH * ratio
            for n in order:
                im = images[n]
                if x + im.width > width:
                    x, y, shelf = 0, y + shelf, 0
                pos[n] = (x, y)
                x += im.width
                shelf = max(shelf, im.height)
            sheet = Image.new("RGBA", (width, max(1, y + shelf)), (0, 0, 0, 0))
            index = {}
            for n in order:
                im = images[n]
                sheet.paste(im, pos[n])
                index[n] = {"x": pos[n][0], "y": pos[n][1], "width": im.width,
                            "height": im.height, "pixelRatio": ratio}
            sheet.save(os.path.join(out_dir, "sprite%s.png" % suffix), optimize=True)
            with open(os.path.join(out_dir, "sprite%s.json" % suffix), "w") as f:
                json.dump(index, f, indent=1, sort_keys=True)
    print("sprite: %d icons -> %s" % (len(files), out_dir))


if __name__ == "__main__":
    main()
