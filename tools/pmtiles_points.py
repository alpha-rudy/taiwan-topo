"""Convert a Mapsforge theme's point rules (symbol, caption, circle on nodes)
into MapLibre layers on the PMTiles poi source-layer.

A node reaches the tiles only when tag-mapping.xml's <pois> keeps one of its
tags, and an area's label point when <ways> keeps it; the Lua writes the kept
tag as class / subclass plus the raw tags the theme's rules test. Layers follow
the conventions of styles/pmtiles_style/style.json: icon "<stem>-<px>" at 1.5x,
caption size x1.5, halo = stroke-width x 0.75, font by font-style,
symbol-sort-key = -priority, minzoom = theme zoom - 1, text-padding /
icon-padding 0, and a feature's own later zoom (minzoom attribute) respected.
"""
import re
from collections import OrderedDict, defaultdict

from pmtiles_theme import FACE, SCALE, icon_name, rgba

SPECIAL = {"name", "ele"}


def zoom_width(w):
    """A Mapsforge stroke width at MapLibre zoom: 1.5x per zoom from z11."""
    return ["interpolate", ["exponential", 1.5], ["zoom"], 11, w, 23, round(w * 1.5 ** 12, 4)]
NUMERIC = {"zl", "ele"}


def read_section(mapping_xml, name):
    body = mapping_xml[mapping_xml.find("<%s>" % name):mapping_xml.find("</%s>" % name)]
    keep = defaultdict(dict)  # key -> stored value -> raw values
    for tag in re.findall(r"<osm-tag\s[^>]*>", body):
        k = re.search(r"key=[\"']([^\"']*)[\"']", tag)
        v = re.search(r"value=[\"']([^\"']*)[\"']", tag)
        if not (k and v):
            continue
        k, v = k.group(1), v.group(1)
        raw = keep[k].setdefault(v, {v})
        eq = re.search(r"equivalent-values=[\"']([^\"']*)[\"']", tag)
        if eq:
            raw.update(e for e in eq.group(1).split(",") if e)
    return keep


class Points:
    def __init__(self, mapping_path):
        x = open(mapping_path).read()
        self.keep_p, self.keep_w = read_section(x, "pois"), read_section(x, "ways")
        self.keep = defaultdict(dict)
        for src in (self.keep_p, self.keep_w):
            for k, vals in src.items():
                for v, raw in vals.items():
                    self.keep[k].setdefault(v, set()).update(raw)

    def primary(self, tests, keep=None):
        """The first test naming a (key, value) the tag mapping keeps, as every
        (key, kept values) pair of its key alternatives."""
        for k, v in tests:
            if not k or k == "*":
                continue
            pairs = []
            for key in k.split("|"):
                if key == "bBoxWeight":
                    continue  # an area-size class, not what the POI is
                hit = set(v.split("|")) & set((keep if keep is not None else self.keep).get(key, {}))
                if hit:
                    pairs.append((key, sorted(hit)))
            if pairs:
                return pairs
        return None

    def test_expr(self, k, v):
        """None: always true; False: never true; else a MapLibre expression.
        With "~" among the values a rule matches when none of the keys is
        present or one has a listed value; "*" matches any value. Keys the
        tiles do not carry on points are never present."""
        vals = v.split("|")
        absent_ok, any_ok = "~" in vals, "*" in vals
        vals = [x for x in vals if x not in ("~", "*")]
        pos, stored = [], []
        for key in k.split("|"):
            if key in SPECIAL:
                raw = set(vals)
            elif key in self.keep:
                raw = set()
                for val in vals:
                    raw |= self.keep[key].get(val, set())
            else:
                continue
            stored.append(key)
            if any_ok:
                pos.append(["has", key])
            elif raw:
                lits = sorted(int(float(r)) for r in raw) if key in NUMERIC else sorted(raw)
                pos.append(["in", ["get", key], ["literal", lits]])
        if absent_ok:
            if not stored:
                return None
            none = [["!", ["has", key]] for key in stored]
            alts = [none[0] if len(none) == 1 else ["all"] + none] + pos
        else:
            alts = pos
        if not alts:
            return False
        return alts[0] if len(alts) == 1 else ["any"] + alts

    def layer(self, r, lid, symbols, cats):
        """The layer drawing point rule r, or None when no feature the tiles
        carry can match it."""
        flt = ["all"]
        for k, v in r["tests"]:
            if not k or k == "*":
                continue
            e = self.test_expr(k, v)
            if e is False:
                return None
            if e is not None:
                flt.append(e)
        # an area's label point (is_area) is a way to the theme
        if r["e"] == "node" or r["closed"] == "no":
            flt.append(["!", ["has", "is_area"]])
        flt.append(["any", ["!", ["has", "minzoom"]], [">=", ["zoom"], ["get", "minzoom"]]])
        a = r["attrs"]
        prio = float(a.get("priority", 0))
        always = a.get("display") == "always"
        lay = OrderedDict([("source", "topo"), ("source-layer", "poi"), ("filter", flt), ("minzoom", r["zmin"] - 1)])
        if r["zmax"] < 99:
            lay["maxzoom"] = r["zmax"]
        lay["id"] = lid
        if r["instr"] == "symbol":
            lay["type"] = "symbol"
            lay["layout"] = {"icon-image": icon_name(a), "icon-allow-overlap": always,
                             "icon-padding": 0, "symbol-sort-key": -prio}
            lay["paint"] = {}
        elif r["instr"] == "circle":
            lay["type"] = "circle"
            # scale-radius: the radius grows with zoom as stroke widths do;
            # otherwise it is fixed pixels, as are its stroke widths
            radius = float(a.get("radius", 1))
            grow = a.get("scale-radius") == "true"
            lay["paint"] = {"circle-radius": zoom_width(radius) if grow else radius,
                            "circle-color": rgba(a.get("fill", "#00000000"))}
            if a.get("stroke"):
                sw = float(a.get("stroke-width", 1))
                lay["paint"]["circle-stroke-color"] = rgba(a["stroke"])
                lay["paint"]["circle-stroke-width"] = zoom_width(sw) if grow else sw
            lay["layout"] = {}
        else:
            size = float(a["font-size"]) * SCALE
            layout = {"text-field": ["to-string", ["get", a["k"]]], "text-font": [FACE[a.get("font-style", "normal")]],
                      "text-size": size, "text-allow-overlap": always, "symbol-sort-key": -prio}
            h = symbols.get(a.get("symbol-id"))
            if h is not None and a.get("position") in ("above", "below"):
                up = a["position"] == "above"
                layout["text-anchor"] = "bottom" if up else "top"
                layout["text-offset"] = [0, round((-1 if up else 1) * (h / 2 + 2) / size, 3)]
            elif a.get("dy"):
                dy = float(a["dy"]) * SCALE
                layout["text-anchor"] = "bottom" if dy < 0 else "top"
                layout["text-offset"] = [0, round(dy / size, 3)]
            layout["text-padding"] = 0
            paint = {"text-color": rgba(a.get("fill", "#000000"))}
            if "stroke" in a:
                paint["text-halo-color"] = rgba(a["stroke"])
                paint["text-halo-width"] = float(a.get("stroke-width", 1)) * SCALE / 2
            lay["type"] = "symbol"
            lay["layout"] = layout
            lay["paint"] = paint
        if cats:
            lay["metadata"] = {"taiwan-topo:cats": cats}
        if r["n"] is None:
            lay["layout"]["visibility"] = "none"
        if not lay["layout"]:
            del lay["layout"]
        return lay

    def zoom_needs(self, r):
        """(pois {key: {value: zoom}}, ways {...}) the tiles must carry for r."""
        zp, zw = {}, {}
        for k, vs in self.primary(r["tests"], self.keep_p) or []:
            for v in vs:
                zp.setdefault(k, {})[v] = r["zmin"]
        if r["e"] != "node" and r["closed"] != "no":
            for k, vs in self.primary(r["tests"], self.keep_w) or []:
                for v in vs:
                    zw.setdefault(k, {})[v] = r["zmin"]
        return zp, zw
