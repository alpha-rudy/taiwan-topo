#!/usr/bin/env python3
"""Prefetch Wikidata labels for the QIDs in an OSM extract into a local SQLite cache.

This is the ONLINE step, run separately from (and before) the offline map build.
complete_name.py then opens the resulting SQLite read-only via the WIKIDATA_CACHE
environment variable and does fast O(1), fully offline label lookups.

Usage:
    python3 build_wikidata_cache.py <input.osm|.pbf|.o5m> <out.sqlite>

The run is incremental: QIDs already present in <out.sqlite> are skipped, so it is
cheap to re-run when the extract gains new wikidata-tagged objects.
"""
import sys
import os
import re
import time
import sqlite3

import osmium
import requests

# Simplified -> Traditional (Taiwan) conversion, so the cached 'zh' column is
# always Traditional regardless of which Chinese variant Wikidata returns.
try:
    import opencc
    _s2twp = opencc.OpenCC('s2twp')
except Exception:
    _s2twp = None

QID_RE = re.compile(r'^Q\d+$')
API = 'https://www.wikidata.org/w/api.php'
# Traditional variants are preferred; generic/Simplified are converted with OpenCC.
LANGS = 'en|zh|zh-tw|zh-hant|zh-hk|zh-hans|ja'
BATCH = 50  # wbgetentities accepts up to 50 ids per request
USER_AGENT = ('taiwan-topo name-completion cache '
              '(https://github.com/rudism/taiwan-topo; rudyboy.tw@gmail.com)')


# Tag keys whose QIDs are cached. brand:wikidata is used by complete_name.py to
# name chain-store POIs; values may be ';'-separated lists of QIDs.
QID_KEYS = ('wikidata', 'brand:wikidata')


class QidCollector(osmium.SimpleHandler):
    """Collect the distinct, well-formed wikidata QIDs in an OSM file."""

    def __init__(self):
        super().__init__()
        self.qids = set()

    def _collect(self, o):
        for key in QID_KEYS:
            v = o.tags.get(key)
            if v:
                for part in v.split(';'):
                    part = part.strip()
                    if QID_RE.match(part):
                        self.qids.add(part)

    def node(self, n):
        self._collect(n)

    def way(self, w):
        self._collect(w)

    def relation(self, r):
        self._collect(r)


def to_traditional(text):
    if text and _s2twp:
        try:
            return _s2twp.convert(text)
        except Exception:
            return text
    return text


# Trailing parenthetical disambiguation in Wikipedia titles: "玉山 (臺灣)" -> "玉山"
PAREN_RE = re.compile(r'\s*[(（][^()（）]*[)）]\s*$')


def sitelink_title(sitelinks, site):
    """Return a sitelink's article title with disambiguation suffix stripped."""
    title = (sitelinks.get(site) or {}).get('title', '').strip()
    if not title:
        return None
    return PAREN_RE.sub('', title).strip() or None


def pick_zh(labels, sitelinks):
    """Pick the best Traditional-Chinese (Taiwan) label from a labels dict,
    falling back to the zhwiki article title (many items have a Chinese
    Wikipedia article but no zh label). Every result goes through
    to_traditional: upstream zh-tw/zh-hant labels occasionally contain
    Simplified characters (curation errors), and the conversion is idempotent
    on genuine Traditional text."""
    for k in ('zh-tw', 'zh-hant', 'zh-hk'):
        if k in labels:
            return to_traditional(labels[k]['value'])
    for k in ('zh', 'zh-hans'):
        if k in labels:
            return to_traditional(labels[k]['value'])
    title = sitelink_title(sitelinks, 'zhwiki')
    if title:
        return to_traditional(title)
    return None


def pick_en(labels, sitelinks):
    """Pick the English label, falling back to the enwiki article title."""
    if 'en' in labels:
        return labels['en']['value']
    return sitelink_title(sitelinks, 'enwiki')


def fetch(ids, session):
    """Fetch labels for up to BATCH ids with simple exponential-backoff retries."""
    params = {
        'action': 'wbgetentities',
        'ids': '|'.join(ids),
        'props': 'labels|sitelinks',
        'sitefilter': 'zhwiki|enwiki',
        'languages': LANGS,
        'format': 'json',
    }
    for attempt in range(5):
        try:
            r = session.get(API, params=params, timeout=30)
            r.raise_for_status()
            return r.json().get('entities', {})
        except Exception as e:
            wait = 2 ** attempt
            sys.stderr.write(
                f"  retry {attempt + 1}/5 after error: {e} (sleep {wait}s)\n")
            time.sleep(wait)
    sys.stderr.write(f"  giving up on batch of {len(ids)} ids\n")
    return {}


def main():
    if len(sys.argv) != 3:
        sys.stderr.write(__doc__)
        sys.exit(2)
    infile, outdb = sys.argv[1], sys.argv[2]

    if not os.path.exists(infile):
        sys.stderr.write(f"input not found: {infile}\n")
        sys.exit(1)

    conn = sqlite3.connect(outdb)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS labels "
        "(qid TEXT PRIMARY KEY, en TEXT, zh TEXT, ja TEXT)")
    conn.commit()
    cached = {row[0] for row in conn.execute("SELECT qid FROM labels")}

    sys.stderr.write(f"scanning {infile} for wikidata QIDs...\n")
    collector = QidCollector()
    collector.apply_file(infile)
    todo = sorted(collector.qids - cached)
    sys.stderr.write(
        f"{len(collector.qids)} QIDs found, {len(cached)} already cached, "
        f"{len(todo)} to fetch\n")

    if not todo:
        conn.close()
        return

    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        entities = fetch(batch, session)
        rows = []
        for qid in batch:
            ent = entities.get(qid) or {}
            labels = ent.get('labels', {})
            sitelinks = ent.get('sitelinks', {})
            en = pick_en(labels, sitelinks)
            zh = pick_zh(labels, sitelinks)
            ja = labels.get('ja', {}).get('value')
            rows.append((qid, en, zh, ja))
        conn.executemany(
            "INSERT OR REPLACE INTO labels (qid, en, zh, ja) VALUES (?, ?, ?, ?)",
            rows)
        conn.commit()
        sys.stderr.write(f"  fetched {min(i + BATCH, len(todo))}/{len(todo)}\n")
        time.sleep(0.2)  # be polite to the API

    conn.close()
    sys.stderr.write("done\n")


if __name__ == '__main__':
    main()
