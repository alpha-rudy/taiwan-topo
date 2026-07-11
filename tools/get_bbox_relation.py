#!/usr/bin/env python3
"""Fetch the bounding box of an OSM relation via Overpass API,
pad it outward by MARGIN degrees, and print it as:

    LEFT := <min lon>
    RIGHT := <max lon>
    BOTTOM := <min lat>
    TOP := <max lat>

Usage:
    python get_bbox_relation.py RELATION_ID [--margin MARGIN] [--decimals DECIMALS]
"""

import json
import math
import urllib.parse
import urllib.request

import click

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def fetch_bounds(relation_id: int) -> dict:
    query = f"[out:json];rel({relation_id});out bb;"
    data = urllib.parse.urlencode({"data": query}).encode()
    last_err = None
    for endpoint in ENDPOINTS:
        req = urllib.request.Request(
            endpoint,
            data=data,  # POST, avoids URL-escaping issues
            headers={"User-Agent": "get_bbox_relation.py"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
            elements = payload.get("elements", [])
            if not elements:
                raise ValueError(f"Relation {relation_id} not found")
            return elements[0]["bounds"]
        except Exception as err:  # try the next mirror
            last_err = err
    raise SystemExit(f"All Overpass endpoints failed: {last_err}")


def round_outward(value: float, direction: str, decimals: int) -> float:
    """Round so the box never shrinks: floor for min sides, ceil for max sides."""
    factor = 10 ** decimals
    fn = math.floor if direction == "down" else math.ceil
    return fn(value * factor) / factor


@click.command()
@click.argument("relation_id", type=int)
@click.option("--margin", type=float, default=0.05, show_default=True,
              help="Degrees to expand outward on every side.")
@click.option("--decimals", type=int, default=2, show_default=True,
              help="Decimal places in the output.")
def main(relation_id: int, margin: float, decimals: int) -> None:
    b = fetch_bounds(relation_id)

    left = round_outward(b["minlon"] - margin, "down", decimals)
    right = round_outward(b["maxlon"] + margin, "up", decimals)
    bottom = round_outward(b["minlat"] - margin, "down", decimals)
    top = round_outward(b["maxlat"] + margin, "up", decimals)

    print(f"LEFT := {left:.{decimals}f}")
    print(f"RIGHT := {right:.{decimals}f}")
    print(f"BOTTOM := {bottom:.{decimals}f}")
    print(f"TOP := {top:.{decimals}f}")


if __name__ == "__main__":
    main()
