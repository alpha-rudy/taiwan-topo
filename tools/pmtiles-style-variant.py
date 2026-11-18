#!/usr/bin/env python3
"""Derive the PMTiles style of another Mapsforge theme from the main one.

styles/pmtiles_style/style.json draws the main theme (MOI_OSM.xml) with
MapLibre: each layer <kind>-<n> (or <kind>-x<m>) draws theme instruction n
(m). A sibling theme such as the paper style (MOI_OSM_twmap.xml) keeps most
of the main theme's rules and changes how they are drawn. This tool:

1. pairs the two themes' instructions by rule path (element, closed, every
   test, instruction type), first with the zoom range, then without it;
2. keeps each paired layer's source, filter and layout, and redraws it with
   the sibling's colours, widths, dashes, offsets, font sizes and faces,
   icons, priorities and zoom range, by the conversions the main style uses;
   a main layer whose rule the sibling does not have is left out;
3. adds layers for sibling rules the main style has no layer for: more zoom
   steps of a paired rule; point rules (with --mapping, by the conversion in
   pmtiles_points.py); and way rules one simple test away from a main layer
   (a route line without the tunnel test, a trail with access=no);
4. puts the line and fill layers in the sibling's rule order, rebuilds the
   contour layers when the sibling draws contours differently, and records
   each layer's overlay cats and the overlay menu from the sibling's stylemenu.

An attribute change it cannot carry over stops the run, listing every one.
--report lists the sibling's rules that are on by default and still have no
layer. Run with the main theme as the sibling, it must give style.json back
unchanged (make paper_style checks this first).

Usage: pmtiles-style-variant.py <main theme> <main style.json> <sibling theme>
           <out style.json> [--mapping tag-mapping.xml] [--sprite URL]
           [--hide LAYER]... [--lua-needs OUT.json] [--report]
"""
import argparse
import copy
import json
import os
import re
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, sys.path[0])
from pmtiles_points import Points  # noqa: E402
from pmtiles_theme import FACE, SCALE, all_rows, icon_name, rgba  # noqa: E402

SKIP_CATS = {"waypoint", "waypoint-label"}  # the app's own GPX waypoints
# peaks and summit boards are the ele_point layers, paired above like any other
ELE_POINT = {("man_made", "summit_board"), ("natural", "peak"), ("natural", "volcano")}

WIDTH_K = 1.5 ** 12  # line widths grow 1.5x per zoom from z11 to z23
MAXZ = 22


def sig(r, zoom):
    s = (r["instr"], tuple(r["tests"]), r["e"], r["closed"])
    return s + (r["zmin"], r["zmax"]) if zoom else s


def pair(A, B):
    """Map index in A -> index in B for instructions with the same rule path.
    The k-th instruction of A with a given path and zoom range pairs with the
    k-th of B; those left over pair the same way by path alone (a sibling may
    draw a rule from another zoom). A sibling may also move rules around (the
    paper theme draws trails before roads), so this pairs by identity, not by
    position; layer order is settled afterwards."""
    out = {}
    for zoom in (True, False):
        pool = {}
        for j, r in enumerate(B):
            if j not in out.values():
                pool.setdefault(sig(r, zoom), []).append(j)
        for i, r in enumerate(A):
            if i in out:
                continue
            js = pool.get(sig(r, zoom))
            if js:
                out[i] = js.pop(0)
    return out


def scale_expr(e, f):
    """Every output number of a zoom expression multiplied by f."""
    if isinstance(e, (int, float)):
        return round(e * f, 4)
    assert e[0] == "interpolate" and e[2] == ["zoom"], e
    out = e[:3]
    for z, v in zip(e[3::2], e[4::2]):
        out += [z, scale_expr(v, f)]
    return out


def width_at(expr, z):
    if isinstance(expr, (int, float)):
        return float(expr)
    kind, stops = expr[1], list(zip(expr[3::2], expr[4::2]))
    if z <= stops[0][0]:
        return stops[0][1]
    if z >= stops[-1][0]:
        return stops[-1][1]
    for (z0, v0), (z1, v1) in zip(stops, stops[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            if kind[0] == "exponential" and kind[1] != 1:
                t = (kind[1] ** (z - z0) - 1) / (kind[1] ** (z1 - z0) - 1)
            return v0 + t * (v1 - v0)


def dasharray(dash, wexpr, lo):
    """A Mapsforge dash of d px is d / width(floor z) in MapLibre line-width units."""
    vals = [[round(d / width_at(wexpr, z), 3) for d in dash] for z in range(lo, MAXZ)]
    if len(vals) == 1:
        return vals[0]
    e = ["step", ["zoom"], ["literal", vals[0]]]
    for z, v in zip(range(lo + 1, MAXZ), vals[1:]):
        e += [z, ["literal", v]]
    return e


def line_expr(v):
    return ["interpolate", ["exponential", 1.5], ["zoom"], 11, v, 23, round(v * WIDTH_K, 4)]


def text_offset(a, size, symbols):
    """[dx, dy] in ems for a caption at size px, as the main style places it."""
    h = symbols.get(a.get("symbol-id"))
    if h is not None and a.get("position") in ("above", "below"):
        up = a["position"] == "above"
        return ("bottom" if up else "top"), [0, round((-1 if up else 1) * (h / 2 + 2) / size, 3)]
    if a.get("dy"):
        dy = float(a["dy"]) * SCALE
        return ("bottom" if dy < 0 else "top"), [0, round(dy / size, 3)]
    return None, None


def restyle(lay, a, b, symA, symB, problems):
    """lay drew instruction a of the main theme; redraw it as instruction b."""
    lay = copy.deepcopy(lay)
    had = {k for k in ("layout", "paint") if k in lay}
    A, B = a["attrs"], b["attrs"]
    lo, pa = lay.setdefault("layout", {}), lay.setdefault("paint", {})
    changed = {k for k in set(A) | set(B) if A.get(k) != B.get(k)}
    done = set()

    # zoom range: the main style draws from theme zoom - 1, never below the
    # source layer's own floor, which shows as a minzoom above zmin - 1
    if a["zmin"] != b["zmin"]:
        floor = lay.get("minzoom", 0) if lay.get("minzoom", 0) > a["zmin"] - 1 else 0
        lay["minzoom"] = max(b["zmin"] - 1, floor)
    if a["zmax"] != b["zmax"]:
        if b["zmax"] < 99:
            lay["maxzoom"] = b["zmax"]
        else:
            lay.pop("maxzoom", None)

    t, ins = lay["type"], b["instr"]
    if t == "line":
        if "stroke" in changed:
            pa["line-color"] = rgba(B.get("stroke", "#000000"))
            done.add("stroke")
        if "stroke-width" in changed:
            pa["line-width"] = scale_expr(pa["line-width"], float(B["stroke-width"]) / float(A["stroke-width"]))
            done.add("stroke-width")
        if "dy" in changed:
            if B.get("dy"):
                pa["line-offset"] = line_expr(float(B["dy"]))
            else:
                pa.pop("line-offset", None)
            done.add("dy")
        if "stroke-linecap" in changed:
            lo["line-cap"] = B.get("stroke-linecap", "round")
            done.add("stroke-linecap")
        if "stroke-linejoin" in changed:
            lo["line-join"] = B.get("stroke-linejoin", "round")
            done.add("stroke-linejoin")
        if B.get("stroke-dasharray") and ({"stroke-dasharray", "stroke-width"} & changed or a["zmin"] != b["zmin"]):
            pa["line-dasharray"] = dasharray([float(d) for d in B["stroke-dasharray"].split(",")],
                                             pa["line-width"], lay.get("minzoom", 0))
            done.add("stroke-dasharray")
        elif "stroke-dasharray" in changed:
            pa.pop("line-dasharray", None)
            done.add("stroke-dasharray")
        if ins == "area":
            done |= {"fill", "src"} & changed  # the area's outline layer
    elif t == "fill":
        if "fill" in changed:
            pa["fill-color"] = rgba(B.get("fill", "#00000000"))
            done.add("fill")
        if "stroke" in changed and "fill-outline-color" in pa:
            pa["fill-outline-color"] = rgba(B["stroke"])
            done.add("stroke")
        done |= {"src", "stroke-width"} & changed  # patterns and outline widths are not drawn
    elif t == "symbol" and ins in ("symbol", "lineSymbol"):
        if {"src", "symbol-width", "symbol-height"} & changed:
            lo["icon-image"] = icon_name(B)
            done |= {"src", "symbol-width", "symbol-height"} & changed
        if "id" in changed:
            done.add("id")
    elif t == "symbol":
        if "fill" in changed:
            pa["text-color"] = rgba(B.get("fill", "#000000"))
            done.add("fill")
        if "stroke" in changed and B.get("stroke"):
            pa["text-halo-color"] = rgba(B["stroke"])
            done.add("stroke")
        if "stroke-width" in changed:
            pa["text-halo-width"] = float(B.get("stroke-width", 1)) * SCALE / 2
            done.add("stroke-width")
        if "font-size" in changed:
            lo["text-size"] = float(B["font-size"]) * SCALE
            done.add("font-size")
        if "font-style" in changed:
            lo["text-font"] = [FACE[B.get("font-style", "normal")]]
            done.add("font-style")
        if "k" in changed and lo.get("text-field") in (["get", A["k"]], ["to-string", ["get", A["k"]]]):
            # the tiles carry name and ele on every feature these layers read
            lo["text-field"] = json.loads(json.dumps(lo["text-field"]).replace('"%s"' % A["k"], '"%s"' % B["k"]))
            done.add("k")
        if "font-family" in changed:
            done.add("font-family")  # one family for every face
        if {"font-size", "position", "dy", "symbol-id"} & changed or symA.get(A.get("symbol-id")) != symB.get(B.get("symbol-id")):
            if "text-offset" in lo or "text-anchor" in lo or B.get("position") in ("above", "below") or B.get("dy"):
                anchor, off = text_offset(B, lo["text-size"], symB)
                if off is None:
                    lo.pop("text-anchor", None)
                    lo.pop("text-offset", None)
                else:
                    lo["text-anchor"], lo["text-offset"] = anchor, off
            done |= {"position", "dy", "symbol-id"} & changed
    if "priority" in changed and "symbol-sort-key" in lo:
        lo["symbol-sort-key"] = -float(B.get("priority", 0))
        done.add("priority")
    if "display" in changed:
        allow = B.get("display") == "always"
        for k in ("icon-allow-overlap", "text-allow-overlap"):
            if k in lo:
                lo[k] = allow
        done.add("display")
    left = changed - done
    if left:
        problems.append((lay["id"], b["m"], {k: (A.get(k), B.get(k)) for k in sorted(left)}))
    for k, v in (("layout", lo), ("paint", pa)):
        if not v and k not in had:
            lay.pop(k)
    return lay


def contour_layers(rows):
    """One layer per contour instruction of a theme: source-layer contour
    carries interval (the contour_* key), class (elevation_*) and ele."""
    lines, labels = [], []
    for r in rows:
        flt = ["all"]
        for k, v in r["tests"]:
            if k.startswith("contour_"):
                if v == "*":
                    flt.append(["==", ["get", "interval"], k])
                else:
                    vs = v.split("|")
                    flt.append(["==", ["get", "class"], vs[0]] if len(vs) == 1 else ["in", ["get", "class"], ["literal", vs]])
            elif k == "ele":
                flt.append(["in", ["get", "ele"], ["literal", sorted(int(x) for x in v.split("|"))]])
            else:
                sys.exit("contour rule %d tests %s=%s, which the contour layer does not carry" % (r["m"], k, v))
        if not any(c[0] == "==" and c[1] == ["get", "interval"] for c in flt[1:]):
            key = next(k for k, _ in r["tests"] if k.startswith("contour_"))
            flt.insert(1, ["==", ["get", "interval"], key])
        a = r["attrs"]
        lay = OrderedDict([("id", "contour-%s" % (r["n"] if r["n"] is not None else "x%d" % r["m"])), ("source", "topo"),
                           ("source-layer", "contour"), ("filter", flt), ("minzoom", r["zmin"] - 1)])
        if r["zmax"] < 99:
            lay["maxzoom"] = r["zmax"]
        if r["instr"] == "line":
            lay["type"] = "line"
            lay["layout"] = {"line-join": "round"}
            lay["paint"] = {"line-color": rgba(a["stroke"]), "line-width": line_expr(float(a["stroke-width"]))}
            lines.append(lay)
        elif r["instr"] == "pathText":
            lay["type"] = "symbol"
            lay["layout"] = {"symbol-placement": "line", "text-field": ["to-string", ["get", a["k"]]],
                             "text-font": [FACE[a.get("font-style", "normal")]], "text-size": float(a["font-size"]) * SCALE}
            lay["paint"] = {"text-color": rgba(a.get("fill", "#000000")), "text-halo-color": rgba(a.get("stroke", "#FFFFFF")),
                            "text-halo-width": float(a.get("stroke-width", 1)) * SCALE / 2}
            labels.append(lay)
        else:
            sys.exit("contour rule %d draws %s" % (r["m"], r["instr"]))
        lay["metadata"] = {"taiwan-topo:cats": ["contour"]}
        if r["n"] is None:
            lay["layout"]["visibility"] = "none"
    return lines, labels


def clause(k, v, keep):
    """The filter clause the main style writes for test k=v on a line source,
    for the tests whose clause is simple: tunnel / bridge presence and the raw
    trail tags. None for a test that adds no clause (area), KeyError otherwise."""
    vs = v.split("|")
    if k == "area" and set(vs) <= {"~", "no"}:
        return None
    if k in ("tunnel", "bridge"):
        return ["!", ["has", k]] if set(vs) <= {"~", "no"} else ["has", k]
    if k not in ("access", "sac_scale", "trail_visibility", "tracktype"):
        raise KeyError(k)
    raw = set()
    for x in vs:
        if x not in ("~", "*"):
            raw |= keep.get(k, {}).get(x, {x})
    raw = sorted(raw)
    pos = (["==", ["get", k], raw[0]] if len(raw) == 1 else ["in", ["get", k], ["literal", raw]]) if raw else None
    if "~" in vs:
        return ["any", pos, ["!", ["has", k]]] if pos else ["!", ["has", k]]
    return pos


def refs(c):
    """The feature attributes a filter clause reads."""
    out = set()
    if isinstance(c, list):
        if len(c) == 2 and c[0] in ("get", "has") and isinstance(c[1], str):
            out.add(c[1])
        for x in c[1:]:
            out |= refs(x)
    return out


def derive_filter(flt, old_tests, new_tests, keep):
    """flt drew old_tests; the filter for new_tests when they differ from them
    only in simple tests (added, dropped or changed), else None."""
    old, new = dict(), dict()
    for k, v in old_tests:
        old.setdefault(k, v)
    for k, v in new_tests:
        new.setdefault(k, v)
    if len(old) != len(old_tests) or len(new) != len(new_tests):
        return None
    out = list(flt)
    try:
        for k in set(old) | set(new):
            if old.get(k) == new.get(k):
                continue
            c_old = clause(k, old[k], keep) if k in old else None
            c_new = clause(k, new[k], keep) if k in new else None
            if c_old is not None:
                if c_old in out:
                    at = out.index(c_old)
                else:
                    # the main style may list the values differently (only those
                    # the tiles carry); the one clause reading just this key
                    hits = [n for n, c in enumerate(out[1:], 1) if refs(c) == {k}]
                    if len(hits) != 1:
                        return None
                    at = hits[0]
                if c_new is None:
                    del out[at]
                else:
                    out[at] = c_new
            elif c_new is not None:
                out.append(c_new)
    except KeyError:
        return None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("main_theme")
    ap.add_argument("main_style")
    ap.add_argument("theme")
    ap.add_argument("out")
    ap.add_argument("--sprite")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--mapping", help="tag-mapping.xml: convert the sibling's point rules that have no layer yet")
    ap.add_argument("--lua-needs", help="write the (key, value) -> zoom the tiles must carry for the sibling's points")
    ap.add_argument("--hide", action="append", default=[],
                    help="layer id to hide by default (e.g. hillshade, which the sibling theme does not draw)")
    o = ap.parse_args()

    _, _, A = all_rows(o.main_theme)
    rootB, activeB, B = all_rows(o.theme)
    ab = pair(A, B)
    idx_n = {r["n"]: i for i, r in enumerate(A) if r["n"]}
    idx_m = {r["m"]: i for i, r in enumerate(A)}

    def symbols(rows):
        return {r["attrs"].get("id"): round(float(r["attrs"].get("symbol-height", r["attrs"].get("symbol-width", 20))) * SCALE)
                for r in rows if r["instr"] == "symbol" and r["attrs"].get("id")}

    symA, symB = symbols(A), symbols(B)
    s = json.load(open(o.main_style), object_pairs_hook=OrderedDict)
    out, problems, dropped = [], [], Counter()
    made = {}  # sibling index -> [(main layer, main row)] it was drawn from
    m_of = {}  # output layer id -> sibling m, for ordering
    main_m = {}  # output layer id -> the main theme's m it was drawn from

    def emit(lay, a, j, prefix):
        b = B[j]
        nl = restyle(lay, a, b, symA, symB, problems)
        nl["id"] = "%s-%s" % (prefix, b["n"] if b["n"] is not None else "x%d" % b["m"])
        if b["n"] is None:
            nl.setdefault("layout", {})["visibility"] = "none"
        elif (nl.get("layout") or {}).get("visibility") == "none":
            del nl["layout"]["visibility"]
            if not nl["layout"]:
                del nl["layout"]
        m_of[nl["id"]] = b["m"]
        main_m[nl["id"]] = a["m"]
        return nl

    templates = OrderedDict()  # main m -> [(layer, main row, prefix)]
    for lay in s["layers"]:
        mm = re.fullmatch(r"([a-z]+)-(x?)(\d+)", lay["id"])
        if not mm or mm.group(1) == "contour":
            out.append(lay)
            continue
        i = idx_m[int(mm.group(3))] if mm.group(2) else idx_n[int(mm.group(3))]
        templates.setdefault(A[i]["m"], []).append((lay, A[i], mm.group(1)))
        if i not in ab:
            dropped[mm.group(1)] += 1
            continue
        out.append(emit(lay, A[i], ab[i], mm.group(1)))
        made.setdefault(ab[i], []).append((lay, A[i], mm.group(1)))

    # A sibling rule with no counterpart but the same rule path as one that
    # has a layer (the same rule split into more zoom steps) is drawn like it.
    paired = set(ab.values())
    by_path = {}
    for j in made:
        by_path.setdefault(sig(B[j], False), j)
    cloned = 0
    for j, r in enumerate(B):
        if j in paired:
            continue
        t = by_path.get(sig(r, False))
        if t is None:
            continue
        for lay, a, prefix in made[t]:
            nl = emit(lay, a, j, prefix)
            # sits next to its template; the ordering pass below sorts it in
            at = next(k for k, x in enumerate(out) if m_of.get(x["id"]) == B[t]["m"])
            out.insert(at + 1, nl)
            cloned += 1
        made[j] = made[t]

    # The sibling's point rules with no layer yet (new ones, or ones the main
    # theme leaves off by default and so never converted) become poi layers,
    # placed in the poi / place run by (priority, -n) as that run is ordered.
    styleB = {c.get("id") for c in rootB.find("stylemenu").find("layer[@id='elmt-hiking']").findall("cat")}
    pts = Points(o.mapping) if o.mapping else None
    needs_p, needs_w, added_pts, skipped = {}, {}, 0, Counter()

    def need(j):
        zp, zw = pts.zoom_needs(B[j])
        for src, dst in ((zp, needs_p), (zw, needs_w)):
            for k, vs in src.items():
                for v, z in vs.items():
                    dst.setdefault(k, {})[v] = min(dst.get(k, {}).get(v, 99), z)

    def order_key(lid):
        r = B[next(j for j, x in enumerate(B) if x["m"] == m_of[lid])]
        return (float(r["attrs"].get("priority", 0)), -(r["n"] if r["n"] is not None else 10000 + r["m"]))

    if pts:
        for j, r in enumerate(B):
            if j in made and any(lay.get("source-layer") == "poi" for lay, _, _ in made[j]):
                need(j)
        ba = {jj: ii for ii, jj in ab.items()}
        for j, r in enumerate(B):
            if j in made or r["n"] is None or r["instr"] not in ("symbol", "caption", "circle") or r["e"] == "way":
                continue
            if j in ba and A[ba[j]]["n"] is not None:
                continue  # the main style leaves this rule undrawn too (turning circles)
            if set(r["cats"]) & SKIP_CATS:
                continue
            p = pts.primary(r["tests"])
            if p is None or p[0][0] == "meta" or any((k, v) in ELE_POINT for k, vs in p for v in vs):
                skipped[(r["instr"],) + tuple("%s=%s" % t for t in r["tests"][:1])] += 1
                continue
            lid = "poi-%d" % r["n"]
            lay = pts.layer(r, lid, symB, [c for c in dict.fromkeys(r["cats"]) if c not in styleB])
            if lay is None:
                skipped[(r["instr"],) + tuple("%s=%s" % t for t in r["tests"][:1])] += 1
                continue
            m_of[lid] = r["m"]
            run = [k for k, x in enumerate(out) if re.fullmatch(r"(poi|place)-x?\d+", x["id"]) and x["id"] in m_of
                   and x.get("source-layer") == "poi"]
            if lay["type"] == "circle":
                # circles are shapes, drawn in rule order under the run's labels:
                # a spring's ring comes before the dot that marks drinking_water
                circles = [k for k in run if out[k]["type"] == "circle"]
                at = next((k for k in circles if m_of[out[k]["id"]] > r["m"]),
                          circles[-1] + 1 if circles else run[0])
            else:
                key = order_key(lid)
                at = next((k for k in run if out[k]["type"] != "circle" and order_key(out[k]["id"]) > key), run[-1] + 1)
            out.insert(at, lay)
            made[j] = [(lay, None, "poi")]
            need(j)
            added_pts += 1
        print("point layers added: %d; point rules the tiles cannot match: %s" % (added_pts, dict(skipped)), file=sys.stderr)
        if o.lua_needs:
            json.dump({"pois": needs_p, "ways": needs_w}, open(o.lua_needs, "w"), ensure_ascii=False, indent=1, sort_keys=True)

    # The sibling's other way rules with no layer: drawn like a rule that has
    # one and differs from it only in simple tests (a route line without the
    # tunnel test, a trail with access=no instead of destination|private).
    derived = 0
    if pts:
        ba = {jj: ii for ii, jj in ab.items()}
        for j, r in enumerate(B):
            if j in made or r["n"] is None or r["e"] == "node" or r["instr"] not in ("line", "pathText", "caption", "lineSymbol"):
                continue
            if "contour" in r["cats"] or (j in ba and A[ba[j]]["n"] is not None):
                continue
            # templates: every layer of the main style with the rule it draws
            for tpl in templates.values():
                a0 = tpl[0][1]
                if a0["instr"] != r["instr"] or (a0["e"], a0["closed"]) != (r["e"], r["closed"]):
                    continue
                flts = [derive_filter(lay["filter"], a["tests"], r["tests"], pts.keep) for lay, a, _ in tpl]
                if any(f is None for f in flts):
                    continue
                for (lay, a, prefix), f in zip(tpl, flts):
                    base = dict(lay)
                    base["filter"] = f
                    nl = emit(base, a, j, prefix)
                    # next to the sibling rule drawn just before it
                    prev = max((x for x in m_of.values() if x < r["m"] and any(m_of.get(y["id"]) == x for y in out)), default=None)
                    at = max(k for k, x in enumerate(out) if m_of.get(x["id"]) == prev) if prev is not None else len(out) - 1
                    out.insert(at + 1, nl)
                    derived += 1
                made[j] = tpl
                break
        print("layers derived from a rule one simple test away: %d" % derived, file=sys.stderr)

    # Mapsforge draws lines and areas in rule order. Inside each run of
    # numbered line / fill layers that the main style keeps in its theme's
    # order, put them in the sibling's order instead; the main style's own
    # breaks (hillshade, water, contours, boundaries above land use) stay.
    def geo(x):
        return x["type"] in ("line", "fill") and x["id"] in m_of

    k = 0
    while k < len(out):
        if not geo(out[k]):
            k += 1
            continue
        e = k + 1
        while e < len(out) and geo(out[e]) and main_m[out[e]["id"]] >= main_m[out[e - 1]["id"]]:
            e += 1
        out[k:e] = sorted(out[k:e], key=lambda x: m_of[x["id"]])
        k = e
    used = {B[j]["m"] for j in made}
    # The land / sea mask and the water areas are one layer each, not one per
    # rule: they take the fill of the rules they stand for, when the main
    # style's colour is that of the main theme's rule (so a hand-picked colour
    # stays) and the sibling's rules agree on one colour.
    def area_fill(rows, tests):
        fills = []
        for r in sorted((r for r in rows if r["instr"] == "area" and r["n"] is not None
                         and r["tests"] and r["tests"][-1] in tests), key=lambda r: r["zmin"]):
            if r["attrs"].get("fill") and rgba(r["attrs"]["fill"]) not in fills:
                fills.append(rgba(r["attrs"]["fill"]))
        return fills

    def same_colour(a, b):
        if a.startswith("#"):
            a = rgba(a)
        return a.replace(" ", "") == b.replace(" ", "")

    for lid, tests in (("sea", [("natural", "sea")]), ("land", [("natural", "nosea")]),
                       ("water", [("natural", "water"), ("waterway", "riverbank"), ("landuse", "reservoir|basin")])):
        lay = next((x for x in out if x["id"] == lid), None)
        fa, fb = area_fill(A, tests), area_fill(B, tests)
        if lay is None or not fa or not fb or not same_colour(lay["paint"]["fill-color"], fa[0]):
            continue
        if not same_colour(fb[0], fa[0]):
            lay["paint"] = dict(lay["paint"], **{"fill-color": fb[0]})
        if len(fb) > 1:
            print("note: %s takes %s; the sibling's rules also use %s" % (lid, fb[0], fb[1:]), file=sys.stderr)

    # contours: the main style's own block stays when the sibling draws them
    # the same; otherwise both runs (lines, then labels) are rebuilt from it
    def contour_sig(rows):
        return [(r["instr"], r["tests"], r["zmin"], r["zmax"], r["attrs"]) for r in rows if "contour" in r["cats"]]

    if contour_sig(A) != contour_sig(B):
        lines, labels = contour_layers([r for r in B if "contour" in r["cats"]])
        pos = [k for k, x in enumerate(out) if x.get("source-layer") == "contour"]
        lpos = [k for k in pos if out[k]["type"] == "line"]
        tpos = [k for k in pos if out[k]["type"] == "symbol"]
        assert lpos == list(range(lpos[0], lpos[-1] + 1)) and tpos == list(range(tpos[0], tpos[-1] + 1)), "contour runs split"
        first, second = (lpos, lines), (tpos, labels)
        for run, new in sorted((first, second), key=lambda t: -t[0][0]):
            out[run[0]:run[-1] + 1] = new
    # poi-other draws the names no theme caption draws: it must also leave out
    # what the point layers added above now draw
    other = next((x for x in out if x["id"] == "poi-other"), None)
    if other is not None and added_pts:
        excl = other["filter"][1][-1]
        assert excl[0] == "!" and excl[1][0] == "any", "poi-other filter shape changed"
        for x in out:
            if x["id"] in m_of and x.get("source-layer") == "poi" and x["type"] == "symbol" \
                    and (x.get("layout") or {}).get("text-field") == ["to-string", ["get", "name"]] \
                    and not any(x is lay for j in made for lay, a, _ in made[j] if a is not None):
                excl[1].append(["all"] + [c for c in x["filter"][1:] if refs(c) != {"minzoom"}])

    # each layer's overlay cats and the style's overlay list, from the sibling's
    # stylemenu: a layer is drawn when every cat on its rule path is active
    menu = rootB.find("stylemenu")
    mlayers = {x.get("id"): x for x in menu.findall("layer")}
    hiking = mlayers["elmt-hiking"]
    style_cats = [c.get("id") for c in hiking.findall("cat")]
    ovs = []
    for ov in hiking.findall("overlay"):
        x = mlayers[ov.get("id")]
        names = {nm.get("lang"): nm.get("value") for nm in x.findall("name")}
        ovs.append({"id": x.get("id"), "name": {"zh": names.get("zh"), "en": names.get("en")},
                    "enabled": x.get("enabled") == "true", "cats": [c.get("id") for c in x.findall("cat")]})
    row_of_m = {r["m"]: r for r in B}
    lcats = {}
    for x in out:
        if x.get("source-layer") == "contour":
            cs = ["contour"]
        elif x["id"] in m_of:
            cs = list(dict.fromkeys(c for c in row_of_m[m_of[x["id"]]]["cats"] if c not in style_cats))
        else:
            cs = list((x.get("metadata") or {}).get("taiwan-topo:cats", []))
        md = dict(x.get("metadata") or {})
        md.pop("taiwan-topo:cats", None)
        if cs:
            md["taiwan-topo:cats"] = cs
            lcats[x["id"]] = cs
        if md:
            x["metadata"] = md
        else:
            x.pop("metadata", None)

    def drawn(on):
        act = set(style_cats)
        for ov in ovs:
            if on[ov["id"]]:
                act.update(ov["cats"])
        return {lid for lid, cs in lcats.items() if all(c in act for c in cs)}

    default = {ov["id"]: ov["enabled"] for ov in ovs}
    base_on = drawn(default)
    keep_ovs = [ov for ov in ovs if drawn(dict(default, **{ov["id"]: not ov["enabled"]})) != base_on]
    hidden = {x["id"] for x in out if (x.get("layout") or {}).get("visibility") == "none"}
    off = set(lcats) - base_on
    if off != (hidden & set(lcats)):
        sys.exit("default visibility mismatch: off by default %s, hidden %s"
                 % (sorted(off - hidden)[:5], sorted((hidden & set(lcats)) - off)[:5]))
    if contour_sig(A) != contour_sig(B) or ab != {i: i for i in range(len(A))}:
        s["metadata"]["comment"] = ("MapLibre GL style for the Taiwan-TOPO PMTiles schema in the %s theme, derived from "
                                    "style.json by tools/pmtiles-style-variant.py (make paper_style); regenerate it "
                                    "rather than editing it." % os.path.basename(o.theme))
    s["metadata"]["taiwan-topo:style-cats"] = style_cats
    s["metadata"]["taiwan-topo:overlays"] = keep_ovs
    for lid in o.hide:
        lay = next(x for x in out if x["id"] == lid)
        lay.setdefault("layout", {})["visibility"] = "none"
    s["layers"] = out
    if o.sprite:
        s["sprite"] = o.sprite
    if problems:
        for p in problems:
            print("UNHANDLED", p, file=sys.stderr)
        sys.exit("%d layers have attribute changes this tool cannot carry over" % len(problems))
    print("layers: %d out, %d dropped %s, %d added for zoom steps" % (len(out), sum(dropped.values()), dict(dropped), cloned),
          file=sys.stderr)
    if o.report:
        # what the sibling draws by default that this run has no layer for, in two
        # groups: rules the main theme does not have, and rules it has but leaves
        # off by default (so the main style never converted them). Rules the main
        # theme draws by default without a layer are drawn some other way (water,
        # contours) or deliberately not (GPX waypoints) and are not listed.
        ba = {j: i for i, j in ab.items()}
        groups = {"new": Counter(), "off in main": Counter()}
        for j, r in enumerate(B):
            if r["n"] is None or r["m"] in used or "contour" in r["cats"]:
                continue
            if j not in ba:
                g = "new"
            elif A[ba[j]]["n"] is None:
                g = "off in main"
            else:
                continue
            groups[g][(r["instr"],) + tuple("%s=%s" % t for t in r["tests"][:2])] += 1
        for g, c in groups.items():
            print("sibling rules on by default with no layer, %s: %d" % (g, sum(c.values())), file=sys.stderr)
            for k, v in c.most_common():
                print("  %3d %s" % (v, k), file=sys.stderr)
    with open(o.out, "w") as f:
        f.write("{\n")
        items = list(s.items())
        for j, (k, v) in enumerate(items):
            if k == "layers":
                f.write('  "layers": [\n')
                f.write(",\n".join("    " + json.dumps(lay, ensure_ascii=False) for lay in v))
                f.write("\n  ]")
            else:
                f.write("  %s: %s" % (json.dumps(k), json.dumps(v, ensure_ascii=False)))
            f.write(",\n" if j < len(items) - 1 else "\n")
        f.write("}\n")


if __name__ == "__main__":
    main()
