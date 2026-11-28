#!/usr/bin/env python3
"""Write FOLDER/files.json: every file in a published folder, for mirrors.

A mirror copies a folder such as rudymap_pmtiles_style/ file by file, and the
sites it copies from list no directories (kcwu's server, R2 behind
data.rudymap.tw), so it cannot find the files otherwise. files.json names each
file under FOLDER (files.json itself excepted) with its size and MD5, sorted by
path; "version" is FOLDER/version.txt's first line when there is one. A mirror
can copy the files listed, check each against its size and MD5, and copy
files.json last, so that a complete folder is one whose files all match it.

Usage: folder-files.py FOLDER
"""
import hashlib
import json
import os
import sys

NAME = "files.json"


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    folder = argv[0]
    if not os.path.isdir(folder):
        sys.exit("not a folder: " + folder)
    files = []
    for root, dirs, names in os.walk(folder):
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, folder).replace(os.sep, "/")
            if rel == NAME:
                continue
            h = hashlib.md5()
            with open(path, "rb") as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            files.append({"path": rel, "size": os.path.getsize(path), "md5": h.hexdigest()})
    if not files:
        sys.exit("no files in " + folder)
    files.sort(key=lambda f: f["path"])
    doc = {"files": files}
    version = os.path.join(folder, "version.txt")
    if os.path.isfile(version):
        with open(version, encoding="utf-8") as f:
            doc["version"] = f.readline().strip()
    out = os.path.join(folder, NAME)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(out + ".tmp", out)
    print("%s: %d files" % (out, len(files)))


if __name__ == "__main__":
    main(sys.argv[1:])
