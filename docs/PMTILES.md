# Using the PMTiles Map

Taiwan TOPO is also built as a vector map in [PMTiles](https://docs.protomaps.com/pmtiles/),
drawn with [MapLibre](https://maplibre.org/) on the web and in apps. This page is for
anyone who wants to show it: what each release contains, how the style finds its
data, and what a web page or an app has to do.

## Files

Each release has three files for the vector map:

| File | Contents |
|---|---|
| `MOI_OSM_Taiwan_TOPO_Rudy.pmtiles` | The map: vector tiles in this project's own schema, zoom 4–14 (MapLibre overzooms beyond 14). |
| `MOI_OSM_Taiwan_TOPO_Rudy_pmtiles_style.zip` | The styles and what they need: `style.json` (the Mapsforge look), `paper.json` (the paper look), `sprite/` and `sprite-paper/` (icons), `glyphs/` (Latin text), `version.txt`, `License.txt`. |
| `taiwan_dem.pmtiles` | Elevations for hillshading: Terrarium-encoded 512 px raster tiles, zoom 6–12. Optional. |

The zip's glyphs cover only the Latin range (`0-255.pbf` of each font). Chinese,
Japanese and Korean text is drawn with the device's own fonts; see
[CJK text](#cjk-text).

## How a style finds its data

A MapLibre style must name its sources, so `style.json` and `paper.json` have two:

| Source id | Type | Default URL in the file |
|---|---|---|
| `topo` | `vector` | `pmtiles://MOI_OSM_Taiwan_TOPO_Rudy.pmtiles` |
| `dem` | `raster-dem` | `pmtiles://taiwan_dem.pmtiles` |

Every layer refers to a source by its id, never by a file name. The URLs in the
files, like `glyphs` (`glyphs/{fontstack}/{range}.pbf`) and `sprite` (`sprite/sprite`,
or `sprite-paper/sprite` in `paper.json`), are names relative to the folder that
holds the files. They are defaults, so the style opens as it is when everything sits
in one folder.

What a web page or an app does, before it hands the style to MapLibre:

1. Set `sources.topo.url` and `sources.dem.url` to where it keeps the two archives.
   Fill them by source id. Do not look files up by the names written in the style.
2. Set `glyphs` and `sprite` the same way.
3. Without the DEM, remove the `dem` source and the layers that use it (the layer
   `hillshade`). The map then draws without hillshading.
4. If a source cannot be filled, stop with an error. Falling back to the URL written in
   the style would quietly draw a different map.

The same steps let one style draw any archive built with this project's schema.

## On a web page (MapLibre GL JS)

Unzip the style zip next to the two archives on your server. The server must answer
HTTP Range requests, which PMTiles reads with. If the page is on another origin, it
must also allow that origin with CORS.

```html
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/pmtiles@3.2.1/dist/pmtiles.js"></script>
<div id="map" style="height: 100vh"></div>
<script>
  // The folder holding the files, made absolute.
  const base = new URL("taiwan-topo/", location.href).href;

  maplibregl.addProtocol("pmtiles", new pmtiles.Protocol().tile);

  fetch(base + "style.json").then((r) => r.json()).then((style) => {
    style.sources.topo.url = "pmtiles://" + base + "MOI_OSM_Taiwan_TOPO_Rudy.pmtiles";
    style.sources.dem.url = "pmtiles://" + base + "taiwan_dem.pmtiles";
    style.glyphs = base + "glyphs/{fontstack}/{range}.pbf";   // must be absolute
    style.sprite = base + "sprite/sprite";                     // must be absolute
    new maplibregl.Map({ container: "map", style, center: [121.0, 23.7], zoom: 7 });
  });
</script>
```

[`styles/pmtiles_style/viewer.html`](../styles/pmtiles_style/viewer.html) is a fuller
example: it takes the archive, DEM, glyph and sprite locations from its query string,
draws `paper.json` with `?style=paper`, and has the overlay switches described below.

## In an app (MapLibre Native)

Download the three files, following the rules in the README's
[For app developers](../README.md#給-app-開發者--for-app-developers) section, into one
folder on the device, and unzip the style zip there.
Then point every URL at a local file:

| Field | Value |
|---|---|
| `sources.topo.url` | `pmtiles://file:///…/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles` |
| `sources.dem.url` | `pmtiles://file:///…/taiwan_dem.pmtiles` |
| `glyphs` | `file:///…/glyphs/{fontstack}/{range}.pbf` |
| `sprite` | `file:///…/sprite/sprite` |

After this rewrite the map makes no network request, so it works offline. It needs a
MapLibre Native release that reads `pmtiles://` sources.

## CJK text

The style zip carries Latin glyphs only, because CJK glyph files are large and every
phone and browser already has CJK fonts. MapLibre draws CJK characters with a local
font when its `localIdeographFontFamily` option is set:

- MapLibre GL JS sets it to `sans-serif` by default. Setting it to `false` makes the
  map ask the glyph URL for CJK characters, and the labels come out blank.
- In MapLibre Native, check that the map options set it. Some SDK wrappers leave it
  unset. CJK labels then come out blank while Latin text and numbers still show.

Only ideographs, kana and hangul are drawn with the local font. Other characters
outside the Latin range, such as full-width punctuation, have no glyphs in the zip and
are left out of the label.

## Versions

One build stamps the same `VERSION` (for example `2026.11.19`) in three places:

- the archive's metadata, as `version`;
- each style's metadata, as `taiwan-topo:version`;
- `version.txt` in the style zip.

When they agree, the map and the style are from the same build.

Each style's metadata also has `taiwan-topo:dem_version`: the first 16 hex digits of
the DEM archive's SHA-256. The DEM build is deterministic, so this changes only when
the elevations do. An app can skip downloading the DEM again while it stays the same,
and can check a downloaded DEM against it.

## Overlay switches

Like the Mapsforge theme's style menu, the styles have switches for groups of layers
(hiking routes, contour lines, waymarks and so on). They live in the style's
metadata:

- `taiwan-topo:overlays` lists the switches. Each has an `id`, a `name` (`zh`, `en`),
  whether it is `enabled` by default, and the `cats` it turns on.
- `taiwan-topo:style-cats` lists the cats that are always on.
- A layer's `metadata["taiwan-topo:cats"]` lists the cats it needs.

A cat is active when it is in `style-cats` or belongs to a switch that is on. A layer
is visible when every one of its cats is active. `viewer.html` (`overlayMenu`) does
exactly this.
