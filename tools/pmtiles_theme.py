"""Read a Mapsforge render theme the way the PMTiles style is built from it.

all_rows() lists every render instruction with the conditions on the path to
it. Two numberings identify an instruction:

- m counts every instruction in document order;
- n counts only those whose rule path is active in the stylemenu style
  (default elmt-hiking with its overlays at their defaults), as Mapsforge
  draws them. Layer ids <kind>-<n> in style.json use n; an instruction that
  is off by default has n None and its layers use <kind>-x<m>.

A rule's cat is active when the style lists it or an overlay holding it is
enabled by default; a rule is drawn when every cat on its path is active.
"""
import xml.etree.ElementTree as ET

INSTR = {"line", "area", "pathText", "caption", "symbol", "lineSymbol", "circle"}
SCALE = 1.5  # labels and symbols are drawn at 1.5x the theme size
FACE = {"normal": "Noto Sans Regular", "bold": "Noto Sans Bold", "italic": "Noto Sans Italic",
        "bold_italic": "Noto Sans Bold"}


def load(theme, style_id="elmt-hiking"):
    root = ET.parse(theme).getroot()
    for e in root.iter():
        if "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]
    menu = root.find("stylemenu")
    layers = {lay.get("id"): lay for lay in menu.findall("layer")}
    cats = set()

    def add_layer(lid, as_overlay):
        lay = layers[lid]
        if as_overlay and lay.get("enabled") != "true":
            return
        for c in lay.findall("cat"):
            cats.add(c.get("id"))
        for p in lay.findall("parent"):
            add_layer(p.get("id"), False)

    style = layers[style_id]
    add_layer(style_id, False)
    for o in style.findall("overlay"):
        add_layer(o.get("id"), True)
    return root, cats


def all_rows(theme, style_id="elmt-hiking"):
    """(root, active cats, rows); each row has m, n, instr, attrs, e, closed,
    zmin, zmax, tests [(k, v)] and cats (on the rule path, outermost first)."""
    root, active = load(theme, style_id)
    out = []
    n, m = [0], [0]

    def walk(node, cond, cats, live):
        for r in node:
            if r.tag == "rule":
                c = r.get("cat")
                nl = live and not (c and c not in active)
                cc = dict(cond)
                cc["tests"] = cond["tests"] + [(r.get("k"), r.get("v"))]
                if r.get("e") and r.get("e") != "any":
                    cc["e"] = r.get("e")
                if r.get("closed") and r.get("closed") != "any":
                    cc["closed"] = r.get("closed")
                if r.get("zoom-min"):
                    cc["zmin"] = max(cc["zmin"], int(r.get("zoom-min")))
                if r.get("zoom-max"):
                    cc["zmax"] = min(cc["zmax"], int(r.get("zoom-max")))
                if cc["zmin"] > cc["zmax"]:
                    continue
                walk(r, cc, cats + ([c] if c else []), nl)
            elif r.tag in INSTR:
                m[0] += 1
                if live:
                    n[0] += 1
                tests = [(k, v) for k, v in cond["tests"] if not (k == "*" and v == "*")]
                out.append({"m": m[0], "n": n[0] if live else None, "instr": r.tag, "attrs": dict(r.attrib),
                            "e": cond["e"], "closed": cond["closed"], "zmin": cond["zmin"], "zmax": cond["zmax"],
                            "tests": tests, "cats": cats})

    walk(root, {"tests": [], "e": "any", "closed": "any", "zmin": 0, "zmax": 99}, [], True)
    return root, active, out


def rgba(c):
    """Mapsforge #RRGGBB / #AARRGGBB as a MapLibre rgba() string."""
    c = c.lstrip("#")
    if len(c) == 6:
        c = "FF" + c
    a, r, g, b = (int(c[i:i + 2], 16) for i in range(0, 8, 2))
    return "rgba(%d,%d,%d,%s)" % (r, g, b, round(a / 255, 3))


def icon_name(attrs):
    """Sprite image of a symbol / lineSymbol: <file stem>-<height in px at SCALE>."""
    stem = attrs["src"].split("/")[-1].rsplit(".", 1)[0]
    return "%s-%d" % (stem, round(float(attrs.get("symbol-height", attrs.get("symbol-width", 20))) * SCALE))
