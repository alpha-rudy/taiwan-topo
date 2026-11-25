#!/usr/bin/env python3
"""Capture verified real Taiwan map context screenshots for legend entries.

Uses PMTiles + MapLibre GL JS + headless Chrome. For each catalog entry with an
`example` location, maps the item's MOI_OSM.xml rules to the exact style.json
layer IDs, snaps onto a real rendered feature via `map.queryRenderedFeatures()`,
and verifies that the target feature is actually drawn inside the center locator
ring before saving the PNG. Unverifiable entries are skipped so screenshots never
show an empty circle.
"""

from __future__ import annotations

import argparse
import http.server
import json
import mimetypes
import re
import shutil
import subprocess
import sys
import threading
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import unquote

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import build_legend as bl
import pmtiles_theme as pt

DEFAULT_REMOTE_PMTILES = "https://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"
DEFAULT_REMOTE_GLYPHS = "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf"

# Explicit style.json layer IDs for items whose style.json layer naming doesn't follow <kind>-<n>
# or where shared base layers (like generic forest/track/landuse) would cause false matches.
EXPLICIT_STYLE_LAYERS: dict[str, list[str]] = {
    "contour_major": [
        "contour-ext-major-z14-14",
        "contour-ext-major-z15-15",
        "contour-ext-major-z16+",
    ],
    "contour_medium": [
        "contour-ext-medium-z14-14",
        "contour-ext-medium-z15-15",
        "contour-ext-medium-z16+",
    ],
    "contour_minor": [
        "contour-ext-sub-z14-14",
        "contour-ext-sub-z15-15",
        "contour-ext-sub-z16+",
    ],
    "area_water": ["water"],
    "area_forest_coniferous": ["area-16", "area-19"],
    "area_forest_deciduous": ["area-17", "area-20"],
    "area_forest_mixed": ["area-18", "area-21"],
    "area_residential": ["area-8"],
    "area_commercial": ["area-10"],
    "area_attraction": ["area-263", "area-264"],
    "water_weir_line": ["line-333", "line-334"],
    "track_grade1": ["trail-399"],
    "track_grade2": ["trail-399"],
    "track_grade3": ["trail-400"],
    "track_grade4": ["trail-401"],
    "track_grade5": ["trail-402"],
    "route_mtb": [],  # mtb_routes overlay is not present in PMTiles style.json
    "poi_peak_small": ["poi-799"],
    "poi_saddle": ["legend-poi-saddle-circle"],
    "trail_closed": ["legend-trail-closed-dash"],
    "border_county": ["legend-border-county-band"],
    "poi_giant_tree": ["legend-poi-giant-tree"],
    "poi_alpine_hut_private": ["poi-823"],
    "poi_comm_tower": ["poi-1069", "poi-1071"],
    "poi_emergency_access": ["poi-898", "poi-900", "poi-902"],
    "poi_sp_trig_c": ["poi-x1052", "poi-x1054", "poi-x1056"],
    "poi_sp_forest": ["poi-x1064", "poi-x1066"],
    "poi_sp_navy_water": ["poi-x1072"],
    "route_hiking_network": [
        "trail-593",
        "trail-594",
        "trail-595",
        "trail-596",
        "trail-597",
        "trail-598",
        "trail-599",
    ],
}

# Optional exact feature property filters when multiple catalog entries share a style.json layer
EXPLICIT_PROP_FILTERS: dict[str, dict[str, str]] = {
    "track_grade1": {"tracktype": "grade1"},
    "track_grade2": {"tracktype": "grade2"},
}

# Representative Taiwan zones ordered by greedy maximum set-cover coverage:
# every subsequent zone strictly contributes additional legend items not covered
# by earlier zones (zones with 0 marginal gain were removed).
FALLBACK_ZONES: list[tuple[str, float, float]] = [
    ("象山／貓空／木柵", 25.0278, 121.5718),
    ("淡水／八里／關渡", 25.1680, 121.4400),
    ("福隆／草嶺古道", 25.0195, 121.9465),
    ("高鐵桃園／青埔", 25.0135, 121.2148),
    ("七星山／小油坑／擎天崗", 25.1707, 121.5535),
    ("桃園虎頭山／桃園神社", 25.0040, 121.3260),
    ("台南安平／億載金城", 22.9990, 120.1610),
    ("新店十四張／碧潭", 24.9830, 121.5280),
    ("松山機場／圓山", 25.0695, 121.5450),
    ("臺中市政府／大坑", 24.1621, 120.6496),
    ("合歡山／武嶺", 24.1370, 121.2756),
    ("彰化大村／員林", 23.9920, 120.5580),
    ("台北車站／中正大安", 25.0478, 121.5170),
    ("太魯閣／錐麓／天祥", 24.1754, 121.5628),
    ("五寮尖／滿月圓", 24.8720, 121.3750),
    ("塔塔加／東埔", 23.4875, 120.8880),
    ("玉山主峰／排雲山莊", 23.4680, 120.9520),
    ("高雄哈瑪星／旗津", 22.6216, 120.2758),
]

_CAPTURE_HTML = r"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <script src="https://unpkg.com/pmtiles@3.2.1/dist/pmtiles.js"></script>
  <style>
    html, body { margin: 0; padding: 0; background: #f7f6f1; }
    #map { width: 512px; height: 384px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    async function log(msg) {
      try { await fetch("/log", { method: "POST", body: String(msg) }); } catch (e) {}
    }

    function collectStyleImages(style) {
      const names = new Set();
      function scan(v) {
        if (typeof v === "string") {
          if (/^[a-z0-9_.-]+-\d+$/i.test(v)) names.add(v);
        } else if (Array.isArray(v)) {
          for (const x of v) scan(x);
        } else if (v && typeof v === "object") {
          for (const k of Object.keys(v)) scan(v[k]);
        }
      }
      for (const l of (style.layers || [])) {
        if (l.layout && l.layout["icon-image"]) scan(l.layout["icon-image"]);
        if (l.paint && l.paint["fill-pattern"]) scan(l.paint["fill-pattern"]);
        if (l.paint && l.paint["line-pattern"]) scan(l.paint["line-pattern"]);
      }
      return Array.from(names);
    }

    function loadResImage(name, pixelRatio) {
      const m = name.match(/^(.+)-(\d+)$/);
      if (!m) return Promise.resolve(null);
      const stem = m[1];
      const h = Math.max(8, parseInt(m[2], 10));
      const pr = pixelRatio || 1;
      const tryUrl = (url) => new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => {
          const ratio = img.naturalWidth && img.naturalHeight ? (img.naturalWidth / img.naturalHeight) : 1;
          const w = Math.max(8, Math.round(h * ratio * pr));
          const hh = Math.max(8, Math.round(h * pr));
          const c = document.createElement("canvas");
          c.width = w;
          c.height = hh;
          const ctx = c.getContext("2d");
          ctx.drawImage(img, 0, 0, w, hh);
          resolve(ctx.getImageData(0, 0, w, hh));
        };
        img.onerror = () => resolve(null);
        img.src = url;
      });
      return tryUrl("/res/" + encodeURIComponent(stem) + ".svg")
        .then((d) => d || tryUrl("/res/" + encodeURIComponent(stem) + ".png"));
    }

    function applyOverlays(map, style, extraCats) {
      const md = style.metadata || {};
      const active = new Set(md["taiwan-topo:style-cats"] || []);
      for (const o of (md["taiwan-topo:overlays"] || [])) {
        if (o.enabled) for (const c of (o.cats || [])) active.add(c);
      }
      for (const c of (extraCats || [])) active.add(c);
      for (const l of (style.layers || [])) {
        const cats = l.metadata && l.metadata["taiwan-topo:cats"];
        if (!cats) continue;
        const want = cats.every((c) => active.has(c)) ? "visible" : "none";
        try {
          const cur = map.getLayoutProperty(l.id, "visibility") || "visible";
          if (cur !== want) map.setLayoutProperty(l.id, "visibility", want);
        } catch (e) {}
      }
    }

    function waitIdle(map, timeoutMs) {
      return new Promise((resolve) => {
        let done = false;
        const finish = (timedOut) => {
          if (!done) {
            done = true;
            resolve(!timedOut);
          }
        };
        map.once("idle", () => finish(false));
        setTimeout(() => finish(true), timeoutMs || 25000);
      });
    }

    function dist2(a, b) {
      const dx = a[0] - b[0];
      const dy = a[1] - b[1];
      return dx * dx + dy * dy;
    }

    function lineMidpoint(coords) {
      if (!coords || !coords.length) return null;
      if (coords.length === 1) return coords[0];
      // Walk to half total length so the snapped point sits right on the line
      let total = 0;
      const lens = [];
      for (let i = 0; i < coords.length - 1; i++) {
        const d = Math.hypot(coords[i + 1][0] - coords[i][0], coords[i + 1][1] - coords[i][1]);
        lens.push(d);
        total += d;
      }
      let target = total * 0.5;
      for (let i = 0; i < lens.length; i++) {
        if (target <= lens[i] && lens[i] > 0) {
          const r = target / lens[i];
          return [
            coords[i][0] + (coords[i + 1][0] - coords[i][0]) * r,
            coords[i][1] + (coords[i + 1][1] - coords[i][1]) * r
          ];
        }
        target -= lens[i];
      }
      return coords[Math.floor(coords.length / 2)];
    }

    function polygonCentroid(ring) {
      if (!ring || !ring.length) return null;
      let sx = 0, sy = 0;
      const n = ring.length;
      for (let i = 0; i < n; i++) { sx += ring[i][0]; sy += ring[i][1]; }
      return [sx / n, sy / n];
    }

    function featureAnchor(feat, seedLngLat) {
      const g = feat.geometry;
      if (!g) return null;
      if (g.type === "Point") return g.coordinates;
      if (g.type === "MultiPoint" && g.coordinates.length) {
        let best = g.coordinates[0], bestD = dist2(best, seedLngLat);
        for (const p of g.coordinates) {
          const d = dist2(p, seedLngLat);
          if (d < bestD) { best = p; bestD = d; }
        }
        return best;
      }
      if (g.type === "LineString") {
        // Pick midpoint of segment closest to seed, or overall midpoint
        let best = lineMidpoint(g.coordinates);
        let bestD = Infinity;
        for (let i = 0; i < g.coordinates.length - 1; i++) {
          const mid = [
            (g.coordinates[i][0] + g.coordinates[i + 1][0]) / 2,
            (g.coordinates[i][1] + g.coordinates[i + 1][1]) / 2
          ];
          const d = dist2(mid, seedLngLat);
          if (d < bestD) { bestD = d; best = mid; }
        }
        return best;
      }
      if (g.type === "MultiLineString" && g.coordinates.length) {
        let best = null, bestD = Infinity;
        for (const line of g.coordinates) {
          const mid = lineMidpoint(line);
          if (!mid) continue;
          const d = dist2(mid, seedLngLat);
          if (d < bestD) { bestD = d; best = mid; }
        }
        return best;
      }
      if (g.type === "Polygon" && g.coordinates.length) {
        return polygonCentroid(g.coordinates[0]);
      }
      if (g.type === "MultiPolygon" && g.coordinates.length && g.coordinates[0].length) {
        return polygonCentroid(g.coordinates[0][0]);
      }
      return null;
    }

    function matchesPropFilter(feat, propFilter) {
      if (!propFilter) return true;
      const props = feat.properties || {};
      for (const [k, v] of Object.entries(propFilter)) {
        if (String(props[k] ?? "") !== String(v)) return false;
      }
      return true;
    }

    async function findRenderedMatch(map, seed, zoom, layers, propFilter) {
      const validLayers = layers.filter((id) => !!map.getLayer(id));
      if (!validLayers.length) return null;

      // Search around seed first at target zoom, then slightly zoomed out for wider coverage
      const searchZooms = [zoom, Math.max(13, zoom - 1.5)];
      for (const sz of searchZooms) {
        map.jumpTo({ center: seed, zoom: sz, bearing: 0, pitch: 0 });
        await waitIdle(map, 9000);
        // Query inside central 412x294 area (avoid clipped edge geometries)
        const feats = map.queryRenderedFeatures([[50, 45], [462, 339]], { layers: validLayers });
        if (!feats.length) continue;

        let bestAnchor = null;
        let bestScore = Infinity;
        let bestName = "";
        for (const f of feats) {
          if (!matchesPropFilter(f, propFilter)) continue;
          const anc = featureAnchor(f, seed);
          if (!anc) continue;
          const d = dist2(anc, seed);
          // Slight preference for named features when distance is similar
          const props = f.properties || {};
          const fname = props["name:zh"] || props.name || props.ref || "";
          const score = fname ? d * 0.65 : d;
          if (score < bestScore) {
            bestScore = score;
            bestAnchor = anc;
            bestName = String(fname);
          }
        }
        if (bestAnchor) return { anchor: bestAnchor, name: bestName, validLayers };
      }
      return null;
    }

    async function scanFallbackZones(map, style, tasks, fallbacks) {
      // Enable union of all task extra_cats so every target layer is visible during the 20-zone scan.
      const allExtra = new Set();
      for (const t of tasks) {
        for (const c of (t.extra_cats || [])) allExtra.add(c);
      }
      applyOverlays(map, style, Array.from(allExtra));

      // Map layerId -> list of tasks interested in that layer
      const layerToTasks = new Map();
      const candidates = new Map(); // taskId -> [{ anchor, name, zoneName, score }]
      for (const t of tasks) {
        candidates.set(t.id, []);
        for (const lid of t.style_layers) {
          if (!map.getLayer(lid)) continue;
          if (!layerToTasks.has(lid)) layerToTasks.set(lid, []);
          layerToTasks.get(lid).push(t);
        }
      }

      const addCandidate = (t, feat, zone) => {
        if (!matchesPropFilter(feat, t.prop_filter)) return;
        const anc = featureAnchor(feat, [zone.lon, zone.lat]);
        if (!anc) return;
        const arr = candidates.get(t.id);
        // Deduplicate candidates that are within ~30m of an existing one
        for (const ex of arr) {
          if (dist2(ex.anchor, anc) < 1e-7) return;
        }
        const props = feat.properties || {};
        const fname = String(props["name:zh"] || props.name || props.ref || "").trim();
        const d = dist2(anc, [zone.lon, zone.lat]);
        // Strongly prefer named features, then closer to zone center
        const score = (fname ? 0 : 10) + Math.min(9, d * 5000);
        arr.push({ anchor: anc, name: fname, zoneName: zone.name, score });
        arr.sort((a, b) => a.score - b.score);
        if (arr.length > 5) arr.length = 5;
      };

      const scanZooms = [15, 17];
      for (const sz of scanZooms) {
        // Only query layers belonging to tasks that still have fewer than 3 candidates
        const neededLayers = [];
        for (const [lid, tlist] of layerToTasks.entries()) {
          if (tlist.some((t) => candidates.get(t.id).length < 3)) {
            neededLayers.push(lid);
          }
        }
        if (!neededLayers.length) break;

        await log("Zone scan z=" + sz + " across " + fallbacks.length + " Taiwan zones (" + neededLayers.length + " layers)...");
        for (let zi = 0; zi < fallbacks.length; zi++) {
          const z = fallbacks[zi];
          map.jumpTo({ center: [z.lon, z.lat], zoom: sz, bearing: 0, pitch: 0 });
          await waitIdle(map, 9000);
          const feats = map.queryRenderedFeatures([[40, 35], [472, 349]], { layers: neededLayers });
          for (const f of feats) {
            const lid = f.layer && f.layer.id;
            const tlist = lid ? layerToTasks.get(lid) : null;
            if (!tlist) continue;
            for (const t of tlist) {
              addCandidate(t, f, z);
            }
          }
        }
      }

      let foundCount = 0;
      for (const arr of candidates.values()) {
        if (arr.length > 0) foundCount++;
      }
      await log("Zone scan complete: found candidates for " + foundCount + "/" + tasks.length + " tasks");
      return candidates;
    }

    async function verifyAndCapture(map, t, anchor, validLayers, outCanvas, outCtx) {
      const [exactLon, exactLat] = anchor;
      map.jumpTo({ center: [exactLon, exactLat], zoom: t.zoom, bearing: 0, pitch: 0 });
      map.triggerRepaint();
      let ok = await waitIdle(map, 25000);
      if (!ok || !map.areTilesLoaded() || !map.isStyleLoaded()) {
        map.triggerRepaint();
        ok = await waitIdle(map, 25000);
      }
      if (!ok) {
        await log("WARN waitIdle timed out for " + t.id);
      }
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

      const cssW = 512, cssH = 384;
      const cx = cssW / 2, cy = cssH / 2;
      const hits = map.queryRenderedFeatures(
        [[cx - 14, cy - 14], [cx + 14, cy + 14]],
        { layers: validLayers }
      ).filter((f) => matchesPropFilter(f, t.prop_filter));

      if (!hits.length) return null;

      // 200x125 CSS crop at dpr=4 -> crisp native 800x500 PNG with 2x magnified map content
      const outCssW = 200, outCssH = 125;
      const srcCanvas = map.getCanvas();
      const dprX = srcCanvas.width / cssW;
      const dprY = srcCanvas.height / cssH;
      const outW = Math.round(outCssW * dprX);
      const outH = Math.round(outCssH * dprY);
      if (outCanvas.width !== outW || outCanvas.height !== outH) {
        outCanvas.width = outW;
        outCanvas.height = outH;
      }
      const sx = (cx - outCssW / 2) * dprX;
      const sy = (cy - outCssH / 2) * dprY;
      outCtx.clearRect(0, 0, outW, outH);
      outCtx.drawImage(srcCanvas, sx, sy, outW, outH, 0, 0, outW, outH);

      // Draw subtle locator ring for points & lines (omit on large area fills)
      if (t.geom !== "area") {
        outCtx.save();
        outCtx.beginPath();
        outCtx.arc(outW / 2, outH / 2, 16 * dprX, 0, Math.PI * 2);
        outCtx.strokeStyle = "rgba(214, 48, 49, 0.80)";
        outCtx.lineWidth = 1.4 * dprX;
        outCtx.setLineDash([3.2 * dprX, 2.4 * dprX]);
        outCtx.stroke();
        outCtx.restore();
      }

      const blob = await new Promise((r) => outCanvas.toBlob(r, "image/png"));
      return { blob, exactLon, exactLat };
    }

    async function run() {
      try {
        const cfg = await (await fetch("/config.json")).json();
        const style = cfg.style;
        const tasks = cfg.tasks;
        const fallbacks = cfg.fallbacks || [];
        const imgPR = Math.max(1, Math.round(window.devicePixelRatio || 1));
        await log("Loaded config: " + tasks.length + " tasks, " + fallbacks.length + " zones, dpr=" + imgPR + ", pmtiles=" + style.sources.topo.url);

        const imgNames = collectStyleImages(style);
        const loadedImages = new Map();
        await Promise.all(imgNames.map(async (name) => {
          const data = await loadResImage(name, imgPR);
          if (data) loadedImages.set(name, data);
        }));
        await log("Preloaded " + loadedImages.size + " / " + imgNames.length + " SVG/PNG icons @" + imgPR + "x");

        const protocol = new pmtiles.Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        const first = tasks[0];
        const initLon = first.has_seed ? first.lon : fallbacks[0].lon;
        const initLat = first.has_seed ? first.lat : fallbacks[0].lat;
        const map = new maplibregl.Map({
          container: "map",
          style: style,
          center: [initLon, initLat],
          zoom: first.zoom || 15,
          interactive: false,
          fadeDuration: 0,
          preserveDrawingBuffer: true,
          localIdeographFontFamily: "'Noto Sans CJK TC', 'Noto Sans TC', 'PingFang TC', sans-serif",
          attributionControl: false
        });

        map.on("error", (e) => {
          const msg = (e && e.error && e.error.message) || String(e);
          log("MAP ERROR: " + msg);
        });

        map.on("styleimagemissing", async (e) => {
          if (map.hasImage(e.id)) return;
          const cached = loadedImages.get(e.id) || await loadResImage(e.id, imgPR);
          if (cached && !map.hasImage(e.id)) {
            map.addImage(e.id, cached, { pixelRatio: imgPR });
          }
        });

        await new Promise((resolve) => {
          if (map.loaded()) resolve();
          else map.once("load", resolve);
        });
        for (const [name, data] of loadedImages.entries()) {
          if (!map.hasImage(name)) map.addImage(name, data, { pixelRatio: imgPR });
        }

        // Pre-scan the 20 Taiwan zones upfront only when auto-discovering unseeded items;
        // for seeded tasks, fall back lazily only if a seed misses.
        let zoneCandidates = null;
        if (tasks.some((t) => !t.has_seed)) {
          zoneCandidates = await scanFallbackZones(map, style, tasks, fallbacks);
        }

        const outCanvas = document.createElement("canvas");
        outCanvas.width = 400 * imgPR;
        outCanvas.height = 250 * imgPR;
        const outCtx = outCanvas.getContext("2d");

        for (let i = 0; i < tasks.length; i++) {
          const t = tasks[i];
          applyOverlays(map, style, t.extra_cats || []);
          const validLayers = t.style_layers.filter((id) => !!map.getLayer(id));
          if (!validLayers.length) {
            await log("SKIP [" + (i + 1) + "/" + tasks.length + "] " + t.id + " (no valid layers)");
            continue;
          }

          // Build ordered list of candidate anchors:
          // - If pinned, use exact (lon, lat) directly (still verified at center).
          // - Otherwise snap around seed first (if curated), then 20-zone scan hits.
          const tryList = [];
          if (t.has_seed && t.pin) {
            tryList.push({ anchor: [t.lon, t.lat], place: t.place, name: t.place });
          } else if (t.has_seed) {
            const seedMatch = await findRenderedMatch(map, [t.lon, t.lat], t.zoom, validLayers, t.prop_filter);
            if (seedMatch) {
              tryList.push({ anchor: seedMatch.anchor, place: t.place, name: seedMatch.name });
            }
          }
          if (!tryList.length) {
            if (!zoneCandidates) {
              zoneCandidates = await scanFallbackZones(map, style, tasks.slice(i), fallbacks);
            }
            const cands = zoneCandidates.get(t.id) || [];
            for (const c of cands) {
              const label = c.name ? (c.name + "（" + c.zoneName + "）") : (c.zoneName + "實景");
              tryList.push({ anchor: c.anchor, place: t.has_seed ? t.place : label, name: c.name || c.zoneName });
            }
          }

          let saved = null;
          let chosenPlace = t.place;
          let chosenName = "";
          for (const cand of tryList) {
            const res = await verifyAndCapture(map, t, cand.anchor, validLayers, outCanvas, outCtx);
            if (res) {
              saved = res;
              chosenPlace = cand.place;
              chosenName = cand.name;
              break;
            }
          }

          if (!saved) {
            await log("SKIP [" + (i + 1) + "/" + tasks.length + "] " + t.id + " (no verified feature across " + fallbacks.length + " zones)");
            continue;
          }

          const qs = "?lat=" + saved.exactLat.toFixed(5) +
            "&lon=" + saved.exactLon.toFixed(5) +
            "&zoom=" + t.zoom +
            "&place=" + encodeURIComponent(chosenPlace);
          await fetch("/save/" + encodeURIComponent(t.id) + qs, { method: "POST", body: saved.blob });
          await log(
            "OK   [" + (i + 1) + "/" + tasks.length + "] " + t.id +
            " -> (" + saved.exactLat.toFixed(5) + ", " + saved.exactLon.toFixed(5) + ") " + (chosenName || chosenPlace)
          );
        }

        await fetch("/done", { method: "POST", body: "ok" });
      } catch (err) {
        await log("ERROR: " + (err && err.stack ? err.stack : String(err)));
        await fetch("/done", { method: "POST", body: "error" });
      }
    }

    run();
  </script>
</body>
</html>
"""


def find_local_pmtiles(explicit: Path | None) -> Path | None:
    if explicit and explicit.is_file():
        return explicit
    for cand in (
        Path("build-taiwan/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
        Path("build/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
        Path("download/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
    ):
        if cand.is_file():
            return cand
    return None


def find_local_dem(explicit: Path | None) -> Path | None:
    if explicit and explicit.is_file():
        return explicit
    for cand in (
        Path("build-taiwan/dem/taiwan_dem.pmtiles"),
        Path("build/dem/taiwan_dem.pmtiles"),
        Path("download/taiwan_dem.pmtiles"),
    ):
        if cand.is_file():
            return cand
    return None


def find_local_glyphs() -> Path | None:
    for cand in (Path("build-taiwan/glyphs"), Path("build/glyphs"), Path("download/glyphs")):
        if cand.is_dir() and (cand / "Noto Sans Regular").is_dir():
            return cand
    return None


def build_style_layer_index(style: dict[str, Any]) -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    """Index style.json layers by MOI_OSM.xml row number (`<kind>-<n>` and `<kind>-x<m>`)."""
    by_n: dict[int, list[str]] = {}
    by_xm: dict[int, list[str]] = {}
    kind_n_re = re.compile(r"^(?:area|line|road|trail|waterway|boundary|poi|place)-(\d+)$")
    kind_xm_re = re.compile(r"^(?:area|line|road|trail|waterway|boundary|poi|place)-x(\d+)$")
    for lay in style.get("layers", []):
        lid = lay.get("id", "")
        mx = kind_xm_re.match(lid)
        if mx:
            by_xm.setdefault(int(mx.group(1)), []).append(lid)
            continue
        mn = kind_n_re.match(lid)
        if mn:
            by_n.setdefault(int(mn.group(1)), []).append(lid)
    return by_n, by_xm


def resolve_style_layers(
    item: dict[str, Any],
    rows: list[dict[str, Any]],
    active_cats: set[str],
    by_n: dict[int, list[str]],
    by_xm: dict[int, list[str]],
    all_overlay_cats: set[str] | None = None,
) -> list[str]:
    """Return the exact style.json layer IDs that render this catalog item."""
    item_id = item["id"]
    if item_id in EXPLICIT_STYLE_LAYERS:
        return list(EXPLICIT_STYLE_LAYERS[item_id])

    geom = item.get("geom", "point")
    e = item.get("e", "node" if geom == "point" else "way")
    closed = item.get("closed", "yes" if geom == "area" else ("no" if geom == "line" else "any"))
    tags = {str(k): str(v) for k, v in item.get("tags", {}).items()}
    extra = list(item.get("extra_cats", []))

    lids: list[str] = []
    seen: set[str] = set()
    for z in range(13, 18):
        mrows, _ = bl.match_rows(rows, active_cats, e, closed, tags, z, extra, all_overlay_cats)
        for r in mrows:
            if r["instr"] in ("caption", "pathText"):
                continue
            cands = by_n.get(r["n"], []) if r["n"] is not None else by_xm.get(r["m"], [])
            for lid in cands:
                if lid not in seen:
                    seen.add(lid)
                    lids.append(lid)
    return lids


def prepare_style(
    style_path: Path,
    pmtiles_url: str,
    dem_url: str | None,
    glyphs_url: str,
) -> dict[str, Any]:
    style: dict[str, Any] = json.loads(style_path.read_text(encoding="utf-8"))
    style["sources"]["topo"]["url"] = f"pmtiles://{pmtiles_url}"
    style["glyphs"] = glyphs_url
    style.pop("sprite", None)

    if dem_url and "dem" in style["sources"]:
        style["sources"]["dem"]["url"] = f"pmtiles://{dem_url}"
    else:
        style["sources"].pop("dem", None)
        style["layers"] = [lay for lay in style["layers"] if lay.get("type") != "hillshade"]

    # Supplement off-by-default MOI_OSM.xml overlays & circle symbols omitted from default style.json
    # so legend sample verification can render them straight from Taiwan PMTiles.
    extra_layers: list[dict[str, Any]] = [
        {
            "id": "legend-border-county-band",
            "type": "line",
            "source": "topo",
            "source-layer": "boundary",
            "filter": ["all", ["==", ["get", "class"], "administrative"], ["in", ["get", "admin_level"], ["literal", [4, "4"]]]],
            "minzoom": 7,
            "layout": {"visibility": "none", "line-cap": "butt"},
            "paint": {"line-color": "#DC94E9", "line-opacity": 0.44, "line-width": 12},
            "metadata": {"taiwan-topo:cats": ["borders"]},
        },
        {
            "id": "legend-border-county-dash",
            "type": "line",
            "source": "topo",
            "source-layer": "boundary",
            "filter": ["all", ["==", ["get", "class"], "administrative"], ["in", ["get", "admin_level"], ["literal", [4, "4"]]]],
            "minzoom": 7,
            "layout": {"visibility": "none", "line-cap": "butt"},
            "paint": {"line-color": "#78517F", "line-width": 1.6, "line-dasharray": [6, 2]},
            "metadata": {"taiwan-topo:cats": ["borders"]},
        },
        {
            "id": "legend-border-county-tick",
            "type": "line",
            "source": "topo",
            "source-layer": "boundary",
            "filter": ["all", ["==", ["get", "class"], "administrative"], ["in", ["get", "admin_level"], ["literal", [4, "4"]]]],
            "minzoom": 7,
            "layout": {"visibility": "none", "line-cap": "butt"},
            "paint": {"line-color": "#6E0D7F", "line-width": 4.2, "line-dasharray": [0, 2.2, 1.0, 4.8]},
            "metadata": {"taiwan-topo:cats": ["borders"]},
        },
        {
            "id": "legend-trail-closed-dash",
            "type": "line",
            "source": "topo",
            "source-layer": "transportation",
            "filter": [
                "all",
                ["in", ["get", "class"], ["literal", ["path", "footway"]]],
                ["in", ["get", "access"], ["literal", ["no", "acc_no"]]],
            ],
            "minzoom": 12,
            "layout": {"visibility": "none", "line-cap": "butt"},
            "paint": {"line-color": "#404040", "line-width": 1.8, "line-dasharray": [3.5, 2.0]},
            "metadata": {"taiwan-topo:cats": ["hike-no_access"]},
        },
        {
            "id": "legend-trail-closed-hatch",
            "type": "line",
            "source": "topo",
            "source-layer": "transportation",
            "filter": [
                "all",
                ["in", ["get", "class"], ["literal", ["path", "footway"]]],
                ["in", ["get", "access"], ["literal", ["no", "acc_no"]]],
            ],
            "minzoom": 13,
            "layout": {"visibility": "none"},
            "paint": {"line-pattern": "p_access-no-12", "line-width": 8},
            "metadata": {"taiwan-topo:cats": ["hike-no_access"]},
        },
        {
            "id": "legend-poi-saddle-circle",
            "type": "circle",
            "source": "topo",
            "source-layer": "poi",
            "filter": ["==", ["get", "mountain_pass"], "yes"],
            "minzoom": 12,
            "layout": {"visibility": "visible"},
            "paint": {
                "circle-radius": 4.5,
                "circle-color": "#CCCCCC",
                "circle-stroke-color": "#666666",
                "circle-stroke-width": 1.8,
            },
            "metadata": {"taiwan-topo:cats": ["landscapefeat"]},
        },
        {
            "id": "legend-poi-giant-tree",
            "type": "symbol",
            "source": "topo",
            "source-layer": "poi",
            "filter": ["==", ["get", "natural"], "giant_tree"],
            "minzoom": 11,
            "layout": {
                "visibility": "none",
                "icon-image": "p_giant_tree-24",
                "icon-allow-overlap": True,
                "text-field": ["get", "name"],
                "text-font": ["Noto Sans Bold"],
                "text-size": 11,
                "text-anchor": "top",
                "text-offset": [0, 1.0],
                "text-optional": True,
            },
            "paint": {"text-color": "#000000", "text-halo-color": "#FFFFFF", "text-halo-width": 2},
            "metadata": {"taiwan-topo:cats": ["giant_tree"]},
        },
    ]
    # Allow poi-823 (private/closed alpine hut) to win symbol collision during legend capture
    for lay in style["layers"]:
        if lay.get("id") == "poi-823":
            lay.setdefault("layout", {})["icon-allow-overlap"] = True

    style["layers"].extend(extra_layers)
    return style


def _serve_range_file(handler: http.server.BaseHTTPRequestHandler, file_path: Path) -> None:
    size = file_path.stat().st_size
    rng = handler.headers.get("Range")
    ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    if not rng:
        handler.send_response(200)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Content-Length", str(size))
        handler.send_header("Accept-Ranges", "bytes")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        with file_path.open("rb") as f:
            shutil.copyfileobj(f, handler.wfile)
        return

    m = re.match(r"bytes=(\d+)-(\d*)", rng)
    if not m:
        handler.send_error(416)
        return
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else size - 1
    end = min(end, size - 1)
    length = end - start + 1
    handler.send_response(206)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.send_header("Content-Length", str(length))
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    with file_path.open("rb") as f:
        f.seek(start)
        rem = length
        while rem > 0:
            chunk = f.read(min(65536, rem))
            if not chunk:
                break
            handler.wfile.write(chunk)
            rem -= len(chunk)


def run_capture(
    tasks: list[dict[str, Any]],
    style_path: Path,
    res_dir: Path,
    out_dir: Path,
    local_pmtiles: Path | None,
    remote_pmtiles_url: str,
    local_dem: Path | None,
    local_glyphs: Path | None,
) -> dict[str, tuple[float, float, int, str]]:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("google-chrome / chromium is required to capture map samples")

    out_dir.mkdir(parents=True, exist_ok=True)
    done_event = threading.Event()
    snapped_coords: dict[str, tuple[float, float, int, str]] = {}
    status_result = ["timeout"]
    bound_port = [0]

    class CaptureHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            path = unquote(self.path.split("?", 1)[0])
            if path == "/capture.html":
                body = _CAPTURE_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/config.json":
                port = bound_port[0]
                pmtiles_url = f"http://127.0.0.1:{port}/topo.pmtiles" if local_pmtiles else remote_pmtiles_url
                dem_url = f"http://127.0.0.1:{port}/dem.pmtiles" if local_dem else None
                glyphs_url = (
                    f"http://127.0.0.1:{port}/glyphs/{{fontstack}}/{{range}}.pbf"
                    if local_glyphs
                    else DEFAULT_REMOTE_GLYPHS
                )
                style = prepare_style(style_path, pmtiles_url, dem_url, glyphs_url)
                fallbacks = [{"name": n, "lat": la, "lon": lo} for n, la, lo in FALLBACK_ZONES]
                body = json.dumps(
                    {"style": style, "tasks": tasks, "fallbacks": fallbacks},
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/topo.pmtiles" and local_pmtiles:
                _serve_range_file(self, local_pmtiles)
                return

            if path == "/dem.pmtiles" and local_dem:
                _serve_range_file(self, local_dem)
                return

            if path.startswith("/res/"):
                rel = Path(path[len("/res/") :]).name
                fp = res_dir / rel
                if fp.is_file():
                    _serve_range_file(self, fp)
                    return
                self.send_error(404)
                return

            if path.startswith("/glyphs/") and local_glyphs:
                rel_p = path[len("/glyphs/") :].lstrip("/")
                fp = (local_glyphs / rel_p).resolve()
                if fp.is_file() and str(fp).startswith(str(local_glyphs.resolve())):
                    _serve_range_file(self, fp)
                    return
                self.send_error(404)
                return

            self.send_error(404)

        def do_POST(self) -> None:
            raw_path = self.path
            path_part, _, qs = raw_path.partition("?")
            path = unquote(path_part)
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length) if length > 0 else b""

            if path.startswith("/save/"):
                item_id = re.sub(r"[^a-zA-Z0-9_-]", "", path[len("/save/") :])
                if item_id and data:
                    (out_dir / f"{item_id}.png").write_bytes(data)
                    m_lat = re.search(r"lat=([0-9.-]+)", qs)
                    m_lon = re.search(r"lon=([0-9.-]+)", qs)
                    m_zoom = re.search(r"zoom=([0-9.]+)", qs)
                    m_place = re.search(r"place=([^&]+)", qs)
                    if m_lat and m_lon:
                        z_val = round(float(m_zoom.group(1))) if m_zoom else 16
                        place_val = unquote(m_place.group(1)) if m_place else ""
                        snapped_coords[item_id] = (
                            float(m_lat.group(1)),
                            float(m_lon.group(1)),
                            z_val,
                            place_val,
                        )
                self.send_response(204)
                self.end_headers()
                return

            if path == "/log":
                print(f"[capture] {data.decode('utf-8', errors='replace')}", flush=True)
                self.send_response(204)
                self.end_headers()
                return

            if path == "/done":
                status_result[0] = data.decode("utf-8", errors="replace")
                done_event.set()
                self.send_response(204)
                self.end_headers()
                return

            self.send_error(404)

    class ReusableServer(http.server.ThreadingHTTPServer):
        allow_reuse_address = True

    with ReusableServer(("127.0.0.1", 0), CaptureHandler) as httpd:
        port = httpd.server_port
        bound_port[0] = port
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        url = f"http://127.0.0.1:{port}/capture.html"
        cmd = [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--force-device-scale-factor=4",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--window-size=600,460",
            url,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            timeout_s = max(120, 90 + len(tasks) * 10)
            done_event.wait(timeout=timeout_s)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            httpd.shutdown()

    if status_result[0] != "ok":
        print(
            f"WARNING: capture ended with status={status_result[0]} (verified {len(snapped_coords)}/{len(tasks)})",
            file=sys.stderr,
        )
    return snapped_coords


def _toml_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def update_catalog_coords(
    catalog_path: Path, snapped: dict[str, tuple[float, float, int, str]]
) -> tuple[int, int]:
    """Update existing `example = ...` coords and insert newly auto-discovered examples into catalog.toml."""
    lines = catalog_path.read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    cur_id = ""
    cur_has_example = False
    updated = 0
    inserted = 0

    def flush_pending() -> None:
        nonlocal inserted
        if cur_id and not cur_has_example and cur_id in snapped:
            lat, lon, zoom, place = snapped[cur_id]
            # Insert immediately after the last non-blank, non-comment line of the item block
            idx = len(out_lines)
            while idx > 0 and (not out_lines[idx - 1].strip() or out_lines[idx - 1].lstrip().startswith("#")):
                idx -= 1
            ex_line = (
                f'example = {{ place = "{_toml_str(place)}", '
                f"lat = {lat:.5f}, lon = {lon:.5f}, zoom = {zoom} }}"
            )
            out_lines.insert(idx, ex_line)
            inserted += 1

    for ln in lines:
        if ln.strip() == "[[items]]":
            flush_pending()
            cur_id = ""
            cur_has_example = False
            out_lines.append(ln)
            continue

        m_id = re.match(r'^id\s*=\s*"([^"]+)"', ln)
        if m_id:
            cur_id = m_id.group(1)
            out_lines.append(ln)
            continue

        if ln.startswith("example = "):
            cur_has_example = True
            if cur_id in snapped:
                lat, lon, _zoom, _place = snapped[cur_id]
                new_ln = re.sub(r"lat\s*=\s*[0-9.-]+", f"lat = {lat:.5f}", ln)
                new_ln = re.sub(r"lon\s*=\s*[0-9.-]+", f"lon = {lon:.5f}", new_ln)
                if new_ln != ln:
                    updated += 1
                    ln = new_ln
            out_lines.append(ln)
            continue

        out_lines.append(ln)

    flush_pending()

    if updated or inserted:
        new_text = "\n".join(out_lines) + "\n"
        # Validate TOML before overwriting
        tomllib.loads(new_text)
        catalog_path.write_text(new_text, encoding="utf-8")
    return updated, inserted


def _default_capture_zoom(item: dict[str, Any]) -> int:
    geom = item.get("geom", "point")
    base_z = int(item.get("zoom", 16))
    if geom == "area":
        if item.get("id") == "area_building":
            return 16
        return max(14, min(15, base_z))
    if geom == "line":
        return max(14, min(16, base_z))
    return max(16, min(17, base_z))


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture verified real Taiwan map example thumbnails for legend.")
    parser.add_argument("--catalog", type=Path, default=Path("docs/legend/catalog.toml"))
    parser.add_argument("--theme", type=Path, default=Path("styles/mapsforge_style/MOI_OSM.xml"))
    parser.add_argument("--style", type=Path, default=Path("styles/pmtiles_style/style.json"))
    parser.add_argument("--res-dir", type=Path, default=Path("styles/mapsforge_style/moiosm_res"))
    parser.add_argument("--out-dir", type=Path, default=Path("download/legend_samples"))
    parser.add_argument("--pmtiles", type=Path, default=None, help="Local PMTiles file path")
    parser.add_argument("--dem", type=Path, default=None, help="Local DEM PMTiles file path")
    parser.add_argument("--pmtiles-url", default=DEFAULT_REMOTE_PMTILES, help="Fallback remote PMTiles URL")
    parser.add_argument("--force", action="store_true", help="Re-capture even if cached PNG exists")
    parser.add_argument(
        "--auto-discover",
        action="store_true",
        help="Also scan representative Taiwan zones to auto-discover examples for items lacking `example`",
    )
    parser.add_argument(
        "--update-catalog",
        action="store_true",
        help="Write verified snapped (and newly auto-discovered) coordinates back to catalog.toml",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Optional comma-separated catalog item IDs to capture (implies --force for those IDs)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional max items to capture")
    args = parser.parse_args()

    only_ids = {s.strip() for s in args.only.split(",") if s.strip()}
    catalog = tomllib.loads(args.catalog.read_text(encoding="utf-8"))
    style_raw: dict[str, Any] = json.loads(args.style.read_text(encoding="utf-8"))
    by_n, by_xm = build_style_layer_index(style_raw)
    layer_cats: dict[str, list[str]] = {
        lay.get("id", ""): list((lay.get("metadata") or {}).get("taiwan-topo:cats") or [])
        for lay in style_raw.get("layers", [])
    }
    root, active_cats, rows = pt.all_rows(str(args.theme), style_id="elmt-hiking")
    all_overlay_cats = set(bl.parse_stylemenu_overlays(root, style_id="elmt-hiking").keys())

    cat_dense = {c["id"]: bool(c.get("dense", False)) for c in catalog["categories"]}
    tasks: list[dict[str, Any]] = []
    unsupported_ids: list[str] = []
    for item in catalog["items"]:
        if only_ids and item["id"] not in only_ids:
            continue
        is_dense = bool(item.get("dense", False)) or cat_dense.get(item["category"], False)
        ex = item.get("example")
        if not ex and (not args.auto_discover or is_dense):
            continue
        style_layers = resolve_style_layers(item, rows, active_cats, by_n, by_xm, all_overlay_cats)
        out_png = args.out_dir / f"{item['id']}.png"
        if not style_layers:
            if ex:
                unsupported_ids.append(item["id"])
            if out_png.is_file():
                out_png.unlink()
            continue
        if out_png.is_file() and not args.force and not only_ids:
            continue

        # Ensure any overlay cats required by the item's style.json layers are enabled
        extra_cats = list(item.get("extra_cats", []))
        for lid in style_layers:
            for c in layer_cats.get(lid, []):
                if c not in extra_cats:
                    extra_cats.append(c)

        has_seed = bool(ex)
        tasks.append(
            {
                "id": item["id"],
                "geom": item.get("geom", "point"),
                "place": ex.get("place", item["name"]) if ex else item["name"],
                "has_seed": has_seed,
                "pin": bool(ex.get("pin", False)) if ex else False,
                "lat": float(ex["lat"]) if ex else 0.0,
                "lon": float(ex["lon"]) if ex else 0.0,
                "zoom": float(ex.get("zoom", _default_capture_zoom(item))) if ex else float(_default_capture_zoom(item)),
                "extra_cats": extra_cats,
                "style_layers": style_layers,
                "prop_filter": EXPLICIT_PROP_FILTERS.get(item["id"]),
            }
        )

    if unsupported_ids:
        print(f"Skipping {len(unsupported_ids)} items not present in PMTiles style.json: {unsupported_ids}")

    if args.limit > 0:
        tasks = tasks[: args.limit]

    if not tasks:
        print(f"All verifiable real-map samples already cached in {args.out_dir}.")
        return

    local_pmtiles = find_local_pmtiles(args.pmtiles)
    local_dem = find_local_dem(args.dem)
    local_glyphs = find_local_glyphs()
    src_desc = str(local_pmtiles) if local_pmtiles else args.pmtiles_url
    print(f"Capturing & verifying {len(tasks)} real Taiwan map samples from {src_desc} ...")

    snapped = run_capture(
        tasks=tasks,
        style_path=args.style,
        res_dir=args.res_dir,
        out_dir=args.out_dir,
        local_pmtiles=local_pmtiles,
        remote_pmtiles_url=args.pmtiles_url,
        local_dem=local_dem,
        local_glyphs=local_glyphs,
    )
    print(f"Done: verified & saved {len(snapped)}/{len(tasks)} samples into {args.out_dir}")

    if args.update_catalog and snapped:
        n_upd, n_ins = update_catalog_coords(args.catalog, snapped)
        print(f"Catalog {args.catalog}: updated {n_upd} coords, added {n_ins} auto-discovered examples")


if __name__ == "__main__":
    main()
