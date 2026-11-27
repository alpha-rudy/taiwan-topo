#!/usr/bin/env python3
"""Check a new PMTiles archive against the styles and against last release.

Every region's archive is drawn with one shared style, built with Taiwan's, and
archives are rebuilt at different times, so an app or a page pairs an archive
with a style of another week. They carry the same schema code
("taiwan-topo:schema", PMTILES_SCHEMA in the Makefile) while each can draw the
other; the code is raised with a change that breaks that (a layer or a field
the styles read renamed or removed, a value they match changed). This check
fails the build when the code says "compatible" and the archive says otherwise:

1. Every source-layer the styles name is in the new archive's vector_layers.
   tilemaker lists every layer in the config there, data or not.
2. The new archive carries SCHEMA.
3. Against last release (LAST_RELEASE, e.g. the balancer's https://rudymap.tw/v1/;
   only the archive's header and metadata are read, and the style zip): with
   the same code, a layer or a field last release's styles read that last
   release's archive had and the new one lacks is a break. A code lower than
   last release's is an error. A higher one is a declared break, not compared.

Fields come from the data: tilemaker lists a field only when a feature has it.
A field that vanished because no feature had it this week reads as a break;
raising the code is safe then too, downstream only pairs more cautiously.
What this cannot see: a value the styles match that changed.

Last release that cannot be read, or carries no code yet, is reported and not
compared. An empty LAST_RELEASE skips step 3 (an offline build).

Usage: pmtiles-schema-check.py ARCHIVE SCHEMA LAST_RELEASE STYLE.json...
"""
import gzip
import io
import json
import os
import re
import struct
import sys
import urllib.request
import zipfile

STYLE_ZIP = "rudymap_pmtiles_style.zip"
SCHEMA_KEY = "taiwan-topo:schema"
# a legacy filter names its field as the second element: ["==", "class", "path"]
LEGACY_OPS = {"==", "!=", "<", "<=", ">", ">=", "in", "!in", "has", "!has"}


def fetch(url, start=None, end=None):
    headers = {"User-Agent": "taiwan-topo-schema-check"}
    if start is not None:
        headers["Range"] = "bytes=%d-%d" % (start, end)
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        data = r.read()
    # a server that ignores Range (a file: URL) sends the whole file
    if start is not None and len(data) > end - start + 1:
        data = data[start:end + 1]
    return data


def metadata(read):
    """The archive's JSON metadata; read(start, end) returns those bytes."""
    header = read(0, 126)
    if header[:7] != b"PMTiles" or header[7] != 3:
        raise ValueError("not a PMTiles v3 archive")
    offset, length = struct.unpack("<QQ", header[24:40])
    raw = read(offset, offset + length - 1)
    if header[97] == 2:
        raw = gzip.decompress(raw)
    elif header[97] != 1:
        raise ValueError("metadata compression %d not supported" % header[97])
    return json.loads(raw)


def local_metadata(path):
    with open(path, "rb") as f:
        def read(start, end):
            f.seek(start)
            return f.read(end - start + 1)
        return metadata(read)


def fields(meta):
    return {layer["id"]: set(layer.get("fields", {})) for layer in meta.get("vector_layers", [])}


def _walk(e, out):
    if isinstance(e, list) and e:
        op = e[0]
        if op in ("get", "has", "!has") and len(e) == 2 and isinstance(e[1], str):
            out.add(e[1])
        elif isinstance(op, str) and op in LEGACY_OPS and len(e) >= 2 \
                and isinstance(e[1], str) and not e[1].startswith("$"):
            out.add(e[1])
        for x in e[1:]:
            _walk(x, out)
    elif isinstance(e, dict):
        for v in e.values():
            _walk(v, out)
    elif isinstance(e, str):
        out.update(re.findall(r"\{([^{}]+)\}", e))  # "{name}" in a text-field


def reads(styles):
    """source-layer -> the fields the styles read on it."""
    used = {}
    for style in styles:
        for layer in style.get("layers", []):
            name = layer.get("source-layer")
            if not name:
                continue
            got = used.setdefault(name, set())
            for part in ("filter", "layout", "paint"):
                if part in layer:
                    _walk(layer[part], got)
    return used


def last_styles(base):
    with zipfile.ZipFile(io.BytesIO(fetch(base + STYLE_ZIP))) as z:
        return [json.loads(z.read(n)) for n in ("style.json", "paper.json") if n in z.namelist()]


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    archive, schema, base, style_paths = argv[0], int(argv[1]), argv[2], argv[3:]
    styles = []
    for p in style_paths:
        with open(p) as f:
            styles.append(json.load(f))
    new = local_metadata(archive)
    new_fields = fields(new)
    errors = []

    for name in sorted(set(reads(styles)) - set(new_fields)):
        errors.append("the styles draw source-layer %r, which the archive does not have" % name)
    if new.get(SCHEMA_KEY) != schema:
        errors.append("the archive's %s is %r, not %d" % (SCHEMA_KEY, new.get(SCHEMA_KEY), schema))
    if errors:
        sys.exit("pmtiles schema check: " + "; ".join(errors))

    if not base:
        print("pmtiles schema check: no last release given, not compared", file=sys.stderr)
        return
    url = base + os.path.basename(archive)
    try:
        last = metadata(lambda s, e: fetch(url, s, e))
    except Exception as e:
        print("pmtiles schema check: last release %s not read (%s), not compared" % (url, e), file=sys.stderr)
        return
    last_schema = last.get(SCHEMA_KEY)
    if last_schema is None:
        print("pmtiles schema check: last release has no %s yet, not compared" % SCHEMA_KEY, file=sys.stderr)
        return
    if schema < last_schema:
        sys.exit("pmtiles schema check: %s %d is lower than last release's %d" % (SCHEMA_KEY, schema, last_schema))
    if schema > last_schema:
        print("pmtiles schema check: %s raised %d -> %d, not compared" % (SCHEMA_KEY, last_schema, schema),
              file=sys.stderr)
        return

    try:
        old_styles = last_styles(base)
    except Exception as e:
        print("pmtiles schema check: last release's %s not read (%s); comparing with these styles"
              % (STYLE_ZIP, e), file=sys.stderr)
        old_styles = []
    used = reads(old_styles + styles)
    last_fields = fields(last)
    dropped = []
    for name in sorted(set(used) & set(last_fields)):
        if name not in new_fields:
            dropped.append("layer %r" % name)
            continue
        for field in sorted((used[name] & last_fields[name]) - new_fields[name]):
            dropped.append("%s.%s" % (name, field))
    if dropped:
        sys.exit("pmtiles schema check: %s is still %d, but the archive no longer has what last release's "
                 "styles read and its archive had: %s. Raise PMTILES_SCHEMA in the Makefile if that is a change; "
                 "if it is only data (no feature had it this time), raising it is safe too."
                 % (SCHEMA_KEY, schema, ", ".join(dropped)))
    print("pmtiles schema check: %s %d, nothing last release's styles read is gone" % (SCHEMA_KEY, schema),
          file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
