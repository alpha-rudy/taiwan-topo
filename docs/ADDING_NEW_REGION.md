# Adding a New Region to Taiwan-TOPO

This document describes the step-by-step process for adding a new geographic region to the Taiwan-TOPO map building system. The example below uses **Nikko-Oze** (日光尾瀨地區) as a reference.

## Table of Contents

- [Concepts](#concepts)
- [Terminology](#terminology)
- [MAPID Indexing](#mapid-indexing)
- [Prerequisites](#prerequisites)
- [Step-by-Step Guide](#step-by-step-guide)
  - [Step 1: Update Makefile](#step-1-update-makefile)
  - [Step 2: Update Main Documentation](#step-2-update-main-documentation)
  - [Step 3: Prepare HGT Elevation Data](#step-3-prepare-hgt-elevation-data)
  - [Step 4: Generate Suite Definitions](#step-4-generate-suite-definitions)
  - [Step 5: Generate CartoType Configuration](#step-5-generate-cartotype-configuration)
  - [Step 6: Generate Locus Map XML](#step-6-generate-locus-map-xml)
  - [Step 7: Generate Region Documentation](#step-7-generate-region-documentation)
  - [Step 8: Build the Suites](#step-8-build-the-suites)
  - [Step 9: Generate Mirror Checking Configuration](#step-9-generate-mirror-checking-configuration)
- [Variant: Region Without Contours / HGT](#variant-region-without-contours--hgt)
- [Generated Files Summary](#generated-files-summary)
- [Commit Example](#commit-example)

---

## Concepts

### What is a "Region"?
A region is a geographic area for which we generate offline maps. Each region produces:
- **Mapsforge maps** (`.map` files) for Android apps like Locus Map, OruxMaps
- **POI databases** (`.poi`, `.db` files) for point-of-interest data
- **Garmin maps** (`.img` files) for GPS devices
- **CartoType packages** (`.cpkg` files) for CartoType-based apps
- **HGT elevation data** for hillshading and elevation profiles

### What is a "Suite"?
A suite is a specific build configuration for a region. Each region typically has multiple suites:
- **Base suite** (`region`): Mapsforge build with `LANG=zh` (Chinese display names)
- **Garmin DEM native** (`region_bc_dem`): Garmin map with `LANG=zh` and DEM
- **Garmin DEM English** (`region_bc_dem_en`): Garmin map with `LANG=en` and DEM

`NATIVE_LANG` is set in all suites to indicate the script language of the region's OSM `name` tags (e.g., `ja`, `ne`, `hi`, `ru`). `complete_name.py` uses it to romanize names into `name:en` and `name:zh`.

### Build Pipeline
1. **Extract**: Download and extract OSM data for the bounding box
2. **Process**: Add elevation contours and POI data
3. **Render**: Generate map tiles using mkgmap/mapsforge
4. **Package**: Create distributable ZIP/CPKG files

> **Regions without elevation:** a region can ship with *no contour lines and no
> HGT/DEM* (the first example is `moscow`). The contour append (`Makefile:693-703`
> plus the two `tools/*-input-build.sh` scripts) is skipped when the suite omits
> `ELEVATION_FILE` / `ELEVATION_MIX_FILE`, and the Garmin build falls back to the
> `map_nodem_*` path when `GMAPDEM` is unset. If that is what you want, follow
> [Variant: Region Without Contours / HGT](#variant-region-without-contours--hgt)
> instead of Steps 3–7 below.

---

## Terminology

| Term | Description |
|------|-------------|
| **Region** | Display name with proper capitalization (e.g., `Nikko-Oze`) |
| **region_lower** | Lowercase identifier with underscores (e.g., `nikko_oze`) |
| **DEM** | Digital Elevation Model - elevation data source |
| **AW3D30** | ALOS World 3D 30m - high resolution DEM from JAXA |
| **HGT** | Height file format for elevation data |
| **MAPID** | Unique hexadecimal identifier for Garmin maps |
| **CODE_PAGE** | Character encoding (65001 = UTF-8) |
| **Bounding Box** | Geographic extent defined by left/right/top/bottom coordinates |

---

## MAPID Indexing

### What MAPID is

`MAPID` is the **unique hexadecimal Garmin map identifier** declared by every
suite `.mk` file:

```makefile
MAPID := $(shell printf %d 0x100c)
```

The `Makefile` consumes it as the mkgmap `--family-id`, the per-suite tiles
directory (`tiles-$(MAPID)`), the overview mapnumber (`$(MAPID)0000`), and the
generated `.img` filenames. **It must be globally unique across all suites** —
two suites sharing a MAPID produce conflicting Garmin maps. Values are 4 hex
digits (`0x0000`–`0xffff`).

### The two numbering schemes

This repo has two historical conventions, and they **share the `0x10xx` /
`0x20xx` space** — the source of past collisions. Know which one applies before
picking a value.

**1. Foreign-region pair scheme — use this for all new regions.**
A region gets a sequential index `N` and claims a pair:

| Variant | MAPID |
|---------|-------|
| Native (zh) | `0x100N` |
| English | `0x200N` |

`N` runs from 1. This is what `tools/generate_suite.py`
(`find_next_mapid_pair()`) allocates automatically.

**2. Taiwan-area (legacy) scheme — do not extend, kept for reference.**
Encoded as `0x<RR><T>` (and a mirrored `0x2<RR><T>` band for `srtm3` / `jing` /
`_en` / secondary variants):

| `RR` (region code) | Region |
|--------------------|--------|
| `10` | taiwan |
| `11` | taipei |
| `13` | beibeiji |
| `14` | yushan |
| `1f` | bbox |
| `23` | kyushu |

| `T` (product-type digit) | Product |
|--------------------------|---------|
| `0` | jing |
| `2` | odc |
| `3` | bw |
| `4` | odc_dem |
| `5` | bw_dem |
| `6` | bc |
| `7` | bc_dem |

Taiwan's English variants used `0x100<T>`: `taiwan_bc_dem_en = 0x1007`,
`taiwan_bw_en = 0x2007`. Because the legacy scheme reuses the same `0x10xx` /
`0x20xx` bytes as the foreign pair scheme, several Taiwan-area ids occupy
foreign `N` slots and must be skipped (see Reserved list).

### Allocation reference

Foreign-pair regions (sorted by `N`):

| N | Region | Native | English |
|---|--------|--------|---------|
| 1 | kumano | `0x1001` | `0x2001` |
| 2 | annapurna | `0x1002` | `0x2002` |
| 3 | kashmir | `0x1003` | `0x2003` |
| 4 | fujisan | `0x1004` | `0x2004` |
| 5 | nikko_oze | `0x1005` | `0x2005` |
| 6 | elbrus | `0x1006` | `0x2006` |
| 7 | *(reserved by taiwan English)* | `0x1007` | `0x2007` |
| 8 | alps_core | `0x1008` | `0x2008` |
| 9 | alps_eastern | `0x1009` | `0x2009` |
| a | alps_western | `0x100a` | `0x200a` |
| b | alps_fareast | `0x100b` | `0x200b` |

➡️ **Next free foreign pair: `N = 0xc` → `0x100c` / `0x200c`.**

### The rule for a new region

1. New regions follow the **foreign-region pair scheme**: pick the lowest `N`
   where **both** `0x100N` and `0x200N` are unused, then assign `0x100N` to the
   native (zh) suite and `0x200N` to the English suite.
2. **Prefer auto-allocation.** Omit `--mapid-native` / `--mapid-english` when
   running `generate_suite.py` — it scans `suites/**/*.mk` and returns the next
   free pair automatically. Supply them only to claim a specific value.
3. **Verify before committing** any manually chosen value:

   ```bash
   # list duplicates (should print nothing)
   grep -rn "MAPID :=" suites/ --include="*.mk" \
     | grep -oE '0x[0-9a-f]+' | sort | uniq -d
   ```

### Reserved / do-not-reuse values

These Taiwan-area ids squat the `0x10xx` / `0x20xx` space and are skipped by the
pair allocator — never assign them to a foreign region:

- `0x1007` + `0x2007` — taiwan English variants (`taiwan_bc_dem_en`,
  `taiwan_bw_en`), occupying foreign slot `N=7`.
- The remaining legacy ids: taiwan (`0x1012`–`0x1017`, `0x2010`–`0x2013`),
  sheipa (`0x1019`), taipei (`0x11xx`/`0x21xx`), beibeiji (`0x13xx`), yushan
  (`0x14xx`), bbox (`0x1fxx`), kyushu (`0x2313`).

---

## Prerequisites

1. **Determine the bounding box** for your region:
   - `left`: Western longitude
   - `right`: Eastern longitude  
   - `bottom`: Southern latitude
   - `top`: Northern latitude

2. **Identify the OSM extract file** for your region:
   - Browse [https://download.geofabrik.de/](https://download.geofabrik.de/) and navigate to the most specific sub-region that fully covers your bounding box. Smaller extracts download faster and are far less likely to fail.
   - Note the **full URL path** to the extract directory. The Makefile defaults to `https://download.geofabrik.de/asia` — if your region is elsewhere (e.g., Russia, Europe, Africa), you must override `EXTRACT_URL` in the generated suite `.mk` files.
   - Example: Elbrus (Russia Caucasus) → `north-caucasus-fed-district-latest` from `https://download.geofabrik.de/russia`.

3. **Prepare HGT files** covering the region

4. **Choose unique MAPIDs** that don't conflict with existing regions

---

## Step-by-Step Guide

### Step 1: Update Makefile

Add an include statement for the new region's suite files in the main `Makefile`:

```makefile
include $(wildcard $(ROOT_DIR)/suites/nikko_oze/*.mk)
```

**Location**: Add after the last existing regional include in the Makefile (before `include $(wildcard $(ROOT_DIR)/suites/bbox/*.mk)`)

No further Makefile change is needed to get `<suite>_topo-en.html` built and
installed — the `topo.md` and `install` targets already look for
`docs/$(REGION)/$(SUITE)_topo-en.md` generically (for every suite) and build
it alongside `<suite>_topo.html` whenever that file exists.

---

### Step 2: Update Main Documentation

Edit `docs/Taiwan/taiwan_topo.md` to list the new region:

```markdown
* Nikko Oze, 日光尾瀨地區
  * https://rudymap.tw/nikko_oze_topo.html
  * 地圖範圍：
    * 緯度範圍: N36.50 ~ N37.47
    * 經度範圍: E138.68 ~ E139.86
```

Add the same entry to `docs/Taiwan/taiwan_topo-en.md` (the pure-English
counterpart of the main doc) — **link to the `-en.html` page**, not the
Chinese one, so English readers stay on English pages:

```markdown
* Nikko Oze
  * https://rudymap.tw/nikko_oze_topo-en.html
  * Map coverage: 
    * Latitude range: N36.50 ~ N37.47
    * Longitude range: E138.68 ~ E139.86
```

---

> **Skip this step** (and Steps 5 & 7's DEM/CartoType pieces) for a region
> without contours/HGT — see
> [Variant: Region Without Contours / HGT](#variant-region-without-contours--hgt).

### Step 3: Prepare HGT Elevation Data

Create a ZIP file containing HGT files for the region and place it in the `hgt/` directory:

```
hgt/nikko_oze_hgtmix.zip
```

The HGT files should cover all tiles within the bounding box. For Nikko-Oze (lat 36.50-37.68, lon 138.52-140.62), you need:
- N36E138.hgt, N36E139.hgt, N36E140.hgt
- N37E138.hgt, N37E139.hgt, N37E140.hgt

#### Elevation PBF Files

The build also downloads pre-generated elevation PBF files from `http://moi.kcwu.csie.org/osm_elevations/`. **These do not exist on the server for a new region** — you must generate them from the HGT data and place them locally before building:

```
download/osm_elevations/ele_<region>_10_100_500.pbf
download/osm_elevations/marker/ele_<region>_10_100_500_mix.pbf
```

After placing both files, generate their checksum files:

```bash
cd download/osm_elevations
md5sum ele_<region>_10_100_500.pbf > ele_<region>_10_100_500.pbf.md5

cd marker
md5sum ele_<region>_10_100_500_mix.pbf > ele_<region>_10_100_500_mix.pbf.md5
```

---

### Step 4: Generate Suite Definitions

Run the suite generator to create Makefile definitions:

```bash
./tools/generate_suite.py \
    --region Nikko-Oze \
    --region-lower nikko_oze \
    --dem-name AW3D30 \
    --lang ja \
    --extract-file japan-latest \
    --right=140.62 \
    --top=37.68 \
    --left=138.52 \
    --bottom=36.50 \
    --code-page 65001 \
    --mapid-native 0x1005 \
    --mapid-english 0x2005
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--region` | Display name | `Nikko-Oze` |
| `--region-lower` | Lowercase identifier | `nikko_oze` |
| `--dem-name` | DEM source | `AW3D30` |
| `--lang` | Native script language (becomes `NATIVE_LANG`) | `ja` (Japanese) |
| `--extract-file` | OSM country extract | `japan-latest` |
| `--left/right/top/bottom` | Bounding box coordinates | See above |
| `--code-page` | Character encoding | `65001` (UTF-8) |
| `--mapid-native` | *(optional)* Garmin MAPID for zh variant — auto-detected if omitted | `0x1005` |
| `--mapid-english` | *(optional)* Garmin MAPID for English — auto-detected if omitted | `0x2005` |

`--mapid-native` and `--mapid-english` are optional. When omitted, the script scans all existing `suites/**/*.mk` files to find the next unused `0x100N` / `0x200N` pair. Supply them explicitly only if you need a specific value. See [MAPID Indexing](#mapid-indexing) for the full scheme, allocation table, and reserved values.

**Output**: Creates files in `suites/nikko_oze/`:
- `nikko_oze.mk` - Base mapsforge suite (`NATIVE_LANG=ja`, `LANG=zh`)
- `nikko_oze_bc_dem.mk` - Garmin DEM with zh language (`NATIVE_LANG=ja`, `LANG=zh`)
- `nikko_oze_bc_dem_en.mk` - Garmin DEM with English (`NATIVE_LANG=ja`, `LANG=en`)

**For non-Asia regions**: `generate_suite.py` does not emit `EXTRACT_URL` (the Makefile defaults to `https://download.geofabrik.de/asia`). If your extract is under a different continent/country path, manually add `EXTRACT_URL` to **all three** generated `.mk` files, directly after the `EXTRACT_FILE` line:

```makefile
EXTRACT_FILE := north-caucasus-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
```

---

### Step 5: Generate CartoType Configuration

Generate CartoType mapdetails JSON files:

```bash
./tools/generate_carto_mapdetails.py \
    --region Nikko-Oze \
    --dem-name AW3D30 \
    --map-lat 37.0 \
    --map-lon 139.0 \
    --auto-estimate
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--region` | Display name | `Nikko-Oze` |
| `--dem-name` | DEM source | `AW3D30` |
| `--map-lat` | Center latitude for map view | `37.0` |
| `--map-lon` | Center longitude for map view | `139.0` |
| `--auto-estimate` | Auto-calculate file sizes from build directory | |

**Output**: Creates files in `auto-install/carto/Nikko-Oze/`:
- `all.json` - Complete package configuration
- `map.json` - Map-only package
- `dem.json` - DEM-only package
- `style.json` - Style-only package
- `upgrade.json` - Upgrade package

---

### Step 6: Generate Locus Map XML

Generate Locus Map auto-install XML files:

```bash
./tools/generate_locus_xml.py \
    --region Nikko-Oze \
    --region-lower nikko_oze
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--region` | Display name | `Nikko-Oze` |
| `--region-lower` | Lowercase identifier | `nikko_oze` |

**Output**: Creates files in `auto-install/locus/Nikko-Oze/`:
- `nikko_oze_all-{provider}.xml` - Full install for each mirror
- `nikko_oze_map-{provider}.xml` - Map-only install
- `nikko_oze_dem-{provider}.xml` - DEM-only install
- `nikko_oze_upgrade-{provider}.xml` - Upgrade install

Providers: `cedric`, `happyman`, `kcwu`

---

### Step 7: Generate Region Documentation

Generate the region's documentation page:

```bash
./tools/generate_topo_md.py \
    --region Nikko-Oze \
    --region-lower nikko_oze \
    --title "Nikko-Oze Region" \
    --hgt-files "N36E138, N36E139, N36E140, N37E138, N37E139, N37E140"
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--region` | Display name | `Nikko-Oze` |
| `--region-lower` | Lowercase identifier | `nikko_oze` |
| `--title` | Page title (used verbatim as the `<h1>` in **both** the Chinese and English doc — restyle either afterward if you want, e.g. a more evocative English title) | `Nikko-Oze Region` |
| `--hgt-files` | Comma-separated HGT file list | `N36E138, N36E139, ...` |

**Output**: Creates two files:
- `docs/Nikko-Oze/nikko_oze_topo.md` — the primary (Chinese) doc
- `docs/Nikko-Oze/nikko_oze_topo-en.md` — a pure-English counterpart, generated automatically by translating the shared boilerplate (installation instructions, mirror links, copyright notices, etc.) via a dictionary in `generate_topo_md.py`. Its "Info pages" mirror links already point at its own `_topo-en.html`, not the Chinese page.

Both files start with **empty** `### 著名的山頭 (Famous Peaks)` / `### 著名的健行路線 (Famous Trekking Routes)` / `### 著名景點` / `### 歷史事件` sections (`### Famous Peaks` / `### Famous Trekking Routes` / `### Famous Sights` / `### Historical Events` in the English file) — write the region's peaks/routes/sights/historical-events content into the Chinese file first, then translate that same content into the English file. This is manual/AI-assisted work; the generator only produces the shared boilerplate around it. See the existing `docs/*/*_topo.md` + `*_topo-en.md` pairs for the expected style and level of detail.

---

### Step 8: Build the Suites

Build all suites for the new region:

```bash
make nikko_oze_suites
```

This will:
1. Download and extract OSM data for the bounding box
2. Merge elevation contours
3. Build mapsforge maps
4. Generate POI databases
5. Build Garmin maps (native and English)
6. Create CartoType packages
7. Package all outputs

---

### Step 9: Generate Mirror Checking Configuration

Generate the mirror checking configuration:

```bash
./tools/generate_checking.py nikko_oze --label "Nikko Oze"
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| First arg | Region lower name | `nikko_oze` |
| `--label` | Display label for reports | `Nikko Oze` |

**Output**: Creates `tools/mirror-configs/nikko_oze.json`

Verify mirrors are properly synced:

```bash
./tools/check-mirrors.py -S nikko_oze
```

**Expected output**:
```
Checking suite: nikko_oze (Nikko Oze)
  ✓ nikko_oze_topo.html
  ✓ nikko_oze_topo-en.html
  ✓ AW3D30_OSM_Nikko-Oze_TOPO_Rudy.map.zip
  ✓ AW3D30_OSM_Nikko-Oze_TOPO_Rudy.zip
  ...
All files synced successfully!
```

Note: `generate_checking.py` always checks both `<suite>_topo.html` and
`<suite>_topo-en.html` on every mirror — make sure Step 8's `install` build
actually produced the `-en.html` (i.e. `docs/<Region>/<suite>_topo-en.md`
exists from Step 7) before syncing, or this check will report the English
page as missing on all mirrors.

---

## Variant: Region Without Contours / HGT

Some regions ship with **no contour lines and no HGT/DEM elevation data** (the
first example is `moscow`). The build supports this as a first-class variant,
analogous to the existing no-DEM Garmin path — you do **not** prepare any HGT or
elevation-PBF data.

### What changes vs a normal region

| Aspect | Normal region | No-elevation region |
|--------|---------------|---------------------|
| Suite vars | `ELEVATION_FILE`, `ELEVATION_MIX_FILE`, `HGT`, `GMAPDEM`, `DEM_NAME` set | all **omitted** |
| Garmin suites | `<region>_bc_dem` / `_bc_dem_en` (DEM) | `<region>_bc` / `_bc_en` (nodem) |
| Base `TARGETS` | includes `gts_all carto_all` | **drops** `gts_all` and `carto_all` (both hard-require `$(HGT)`) |
| Contour merge | `ELEVATION` / `ELEVATION_MIX` appended into map inputs | skipped automatically |
| File names | `AW3D30_OSM_<Region>...`, `gmapsupp_<Region>_aw3d30_zh_camp3D` | DEM token dropped: `OSM_<Region>...`, `gmapsupp_<Region>_zh_camp` |
| Garmin style | `camp3D` | `camp` |
| Data files (Step 3) | HGT zip + elevation PBFs required | **not needed** |
| CartoType (Step 5) | 5 `.cpkg` packages | **skipped** (no `.cpkg` produced) |
| Products | mapsforge, POI, Locus, Garmin, CartoType, GTS | mapsforge, POI, Locus, Garmin (nodem) |

### How the build stays correct

- The contour append is gated on the elevation vars: `$(GMAP_INPUT)` and
  `$(MAPSFORGE_PBF)` depend on `$(if $(ELEVATION_FILE),$(ELEVATION))` /
  `$(if $(ELEVATION_MIX_FILE),$(ELEVATION_MIX))` (`Makefile:693-703`), and
  `gmap-input-build.sh` / `mapsforge-input-build.sh` skip the append when the
  elevation argument is empty.
- Garmin uses the `map_nodem_*` path automatically when `GMAPDEM` is empty
  (`Makefile:117-126`).
- The DEM_NAME token disappears from every generated file name because the
  Makefile builds them from `DEM_PREFIX` / `DEM_INFIX` / `DEM_DOT`, which expand
  to empty when `DEM_NAME` is unset (existing regions are unchanged).
- The `install` HGT copy is soft (`-cp hgt/$(SUITE)_hgt*.zip`, `Makefile:265`),
  so a missing HGT zip does not fail the install.

### Sea rendering (coastal no-elevation regions)

The mapsforge sea is **not** computed by the map-writer — it comes from
`natural=sea`/`natural=nosea` polygons that the kcwu `ele_*_mix.pbf` files
carry for normal regions (see the `land_sea` entries in
`osm_scripts/tag-mapping.xml`): one fixed `natural=sea` rectangle covering the
whole bbox, with `natural=nosea` land polygons drawn on top of it — the sea is
never computed, only the land shape is. A no-elevation region skips the mix
file, so a **coastal** region would render without sea (Garmin is
unaffected — mkgmap takes sea from `precomp-sea`).

Set `LANDSEA := true` in the base suite (or pass `--landsea` to
`generate_suite.py`): the build then reproduces the same scheme via
`tools/sealand-creator.sh`, ported in from the sibling **taiwan-contour**
project — clip the authoritative OSM land-polygons dataset
([land-polygons-split-4326](https://osmdata.openstreetmap.de/data/land-polygons.html))
to the bbox for the land shape, laying the fixed sea rectangle underneath. The
dataset (~880MB) is downloaded once to `download/land-polygons/` and shared
across all regions. Landlocked regions (e.g. `moscow`) must leave `LANDSEA`
unset.

### Generating a no-elevation region

The generators take a `--no-elevation` flag that emits the stripped, correctly
named output directly — no hand-editing required:

```bash
# Suites: omit ELEVATION_*/HGT/GMAPDEM/DEM_NAME, drop gts_all/carto_all, name the
# Garmin suites _bc / _bc_en (nodem, "camp" style). MAPID pair auto-allocated.
# Add --landsea for a coastal region (sea/nosea overlay from land-polygons).
./tools/generate_suite.py --region Moscow --region-lower moscow --lang ru \
    --extract-file central-fed-district-latest \
    --left 36.03 --right 39.00 --bottom 54.94 --top 56.48 --no-elevation

# Documentation: strips all HGT/DEM/contour/CartoType blocks + credits and drops
# the DEM_NAME token / uses the "camp" style in file names. Produces both
# moscow_topo.md and moscow_topo-en.md with the same blocks stripped.
./tools/generate_topo_md.py --region Moscow --region-lower moscow \
    --title "Moscow Region" --no-elevation

# Locus XML: only the map + upgrade variants (skips dem / all) with the no-DEM name.
./tools/generate_locus_xml.py --region Moscow --region-lower moscow --no-elevation

# Mirror-check config: auto-detected from the suite .mk — no flag needed. It drops
# the gts_all zip, .cpkg packages, HGT zip, dem/all Locus XML, and the DEM token.
./tools/generate_checking.py moscow --label "Moscow"
```

`generate_carto_mapdetails.py` also accepts `--no-elevation` (emits only
`map/style/upgrade` json without the DEM prefix), but because a no-elevation
region has `carto_all` disabled, CartoType generation (Step 5) is normally
**skipped entirely**.

Since the suite `.mk` files omit `EXTRACT_URL`, add it manually for non-Asia
regions exactly as in [Step 4](#step-4-generate-suite-definitions). Moscow uses
`https://download.geofabrik.de/russia` with `central-fed-district-latest`.

### Reference example

`suites/moscow/` (`moscow.mk`, `moscow_bc.mk`, `moscow_bc_en.mk`) is the
canonical no-elevation region — copy it the way `suites/elbrus/` is the reference
for a Russia extract.

---

## Generated Files Summary

After completing all steps, the following files should be created:

```
taiwan-topo/
├── Makefile                                    # Updated with include
├── docs/
│   ├── Taiwan/taiwan_topo.md                   # Updated with region link
│   ├── Taiwan/taiwan_topo-en.md                # Updated with region link (-en.html)
│   ├── Nikko-Oze/nikko_oze_topo.md            # New documentation (zh)
│   └── Nikko-Oze/nikko_oze_topo-en.md         # New documentation (en)
├── hgt/
│   └── nikko_oze_hgtmix.zip                   # Elevation data
├── suites/nikko_oze/
│   ├── nikko_oze.mk                           # Base suite
│   ├── nikko_oze_bc_dem.mk                    # Garmin native
│   └── nikko_oze_bc_dem_en.mk                 # Garmin English
├── auto-install/
│   ├── carto/Nikko-Oze/
│   │   ├── all.json
│   │   ├── map.json
│   │   ├── dem.json
│   │   ├── style.json
│   │   └── upgrade.json
│   └── locus/Nikko-Oze/
│       ├── nikko_oze_all-cedric.xml
│       ├── nikko_oze_all-happyman.xml
│       ├── nikko_oze_all-kcwu.xml
│       ├── nikko_oze_map-*.xml
│       ├── nikko_oze_dem-*.xml
│       └── nikko_oze_upgrade-*.xml
└── tools/mirror-configs/
    └── nikko_oze.json                         # Mirror checking config
```

---

## Commit Example

Reference commit: `3bd281cea24a99a58e3a49abda1d6b75ea09f80d`

```
added Nikko Oze region

- Updated Makefile to include nikko_oze suites
- Added HGT elevation data (nikko_oze_hgtmix.zip)
- Generated suite definitions (nikko_oze/*.mk)
- Generated CartoType configurations (auto-install/carto/Nikko-Oze/)
- Generated Locus XML files (auto-install/locus/Nikko-Oze/)
- Created documentation (docs/Nikko-Oze/nikko_oze_topo.md + nikko_oze_topo-en.md)
- Updated docs/Taiwan/taiwan_topo.md and taiwan_topo-en.md with the new region link
- Added mirror checking config (tools/mirror-configs/nikko_oze.json)
```

---

## Troubleshooting

### Common Issues

1. **MAPID conflicts**: `generate_suite.py` auto-detects the next free MAPID pair by scanning all existing `suites/**/*.mk` files, so conflicts are avoided automatically. If you supply `--mapid-native` / `--mapid-english` manually, verify they are not already used: `grep -r "MAPID" suites/ --include="*.mk"`. See [MAPID Indexing](#mapid-indexing) for the numbering scheme and reserved values.

2. **Missing HGT files**: Verify all tiles in your bounding box are included in the HGT ZIP.

3. **Build failures**: Check that the extract file exists in `download/extracts/` or will be downloaded.

4. **Mirror sync issues**: Run `./tools/check-mirrors.py -S region_lower` to diagnose sync problems.

5. **`osmconvert Error: unknown file format`**: The downloaded `.osm.pbf` is actually an HTML error page (typically ~162 bytes). The root cause is a wrong `EXTRACT_URL` — the server returned a 404 page instead of the actual PBF. Verify the URL manually: open `$(EXTRACT_URL)/$(EXTRACT_FILE).osm.pbf` in a browser. Common fix: set `EXTRACT_URL := https://download.geofabrik.de/<continent>` in the suite `.mk` files, and choose a valid sub-region extract name.

6. **Missing elevation PBF files (`curl` downloads 162 bytes)**: The elevation files don't exist on the server for new regions. Generate them from HGT data and place them in `download/osm_elevations/` and `download/osm_elevations/marker/`, then create `.md5` checksums with `md5sum`. See Step 3.

7. **`gmap` zip is empty / jmc_cli produces `OSM map.gmap`**: the TYP-compile step
   used to leave default-named `osmmap.img`/`osmmap.tdb` in the map directory, and
   `jmc_cli` picks the alphabetically-first `.tdb` — so any region whose
   `NAME_WORD` sorts after "osmmap" (e.g. `Saint-Petersburg_...`; regions with an
   `AW3D30_`/`MOI_` prefix always sorted first and were never affected) got its
   `.gmap` named `OSM map.gmap`, and the follow-up rename/zip failed with
   `errno=2 : No such file or directory`. Fixed in the build system (`macros.mk`
   removes the stray files after the TYP compile; the `gmap` rule also cleans
   them and any stale `OSM map.gmap` before running jmc_cli, so existing build
   directories self-heal on re-run). If you see this on an old tree, delete
   `osmmap.img osmmap.tdb` from the `*_hidem`/`*_nodemhr` directory and re-run.

8. **Garmin map shows sea but mapsforge doesn't** (coastal no-elevation region):
   the mapsforge sea comes from `natural=sea`/`nosea` polygons normally carried
   by the kcwu `ele_*_mix.pbf`, which no-elevation regions skip; Garmin's sea
   comes from mkgmap `precomp-sea` and keeps working. Fix: set
   `LANDSEA := true` in the base suite `.mk` and rebuild — the build clips the
   OSM land-polygons dataset to the bbox via `tools/sealand-creator.sh` (see
   [Sea rendering](#sea-rendering-coastal-no-elevation-regions)). The first
   build with any `LANDSEA` region downloads the ~880MB dataset to
   `download/land-polygons/` — expect that step to take a while once.

### Getting Help

- GitHub: https://github.com/alpha-rudy/taiwan-topo
- Facebook Group: https://www.facebook.com/groups/taiwan.topo
