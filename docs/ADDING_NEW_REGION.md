# Adding a New Region to Taiwan-TOPO

This document describes the step-by-step process for adding a new geographic region to the Taiwan-TOPO map building system. The example below uses **Nikko-Oze** (日光尾瀨地區) as a reference.

## Table of Contents

- [Concepts](#concepts)
- [Terminology](#terminology)
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
- **Base suite** (`region`): Mapsforge build with native language
- **Garmin DEM native** (`region_bc_dem`): Garmin map with native language and DEM
- **Garmin DEM English** (`region_bc_dem_en`): Garmin map with English and DEM

### Build Pipeline
1. **Extract**: Download and extract OSM data for the bounding box
2. **Process**: Add elevation contours and POI data
3. **Render**: Generate map tiles using mkgmap/mapsforge
4. **Package**: Create distributable ZIP/CPKG files

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

## Prerequisites

1. **Determine the bounding box** for your region:
   - `left`: Western longitude
   - `right`: Eastern longitude  
   - `bottom`: Southern latitude
   - `top`: Northern latitude

2. **Identify the OSM extract file** (e.g., `japan-latest`, `nepal-latest`)

3. **Prepare HGT files** covering the region

4. **Choose unique MAPIDs** that don't conflict with existing regions

---

## Step-by-Step Guide

### Step 1: Update Makefile

Add an include statement for the new region's suite files in the main `Makefile`:

```makefile
include $(wildcard $(ROOT_DIR)/suites/nikko_oze/*.mk)
```

**Location**: Add after other regional includes (around line 73)

---

### Step 2: Update Main Documentation

Edit `docs/Taiwan/taiwan_topo.md` to list the new region:

```markdown
* Nikko Oze, 日光尾瀨地區
  * https://rudymap.tw/nikko_oze_topo.html
  * 涵蓋的長距離步道：
    * ???
```

---

### Step 3: Prepare HGT Elevation Data

Create a ZIP file containing HGT files for the region and place it in the `hgt/` directory:

```
hgt/nikko_oze_hgtmix.zip
```

The HGT files should cover all tiles within the bounding box. For Nikko-Oze (lat 36.50-37.68, lon 138.52-140.62), you need:
- N36E138.hgt, N36E139.hgt, N36E140.hgt
- N37E138.hgt, N37E139.hgt, N37E140.hgt

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
| `--lang` | Primary language code | `ja` (Japanese) |
| `--extract-file` | OSM country extract | `japan-latest` |
| `--left/right/top/bottom` | Bounding box coordinates | See above |
| `--code-page` | Character encoding | `65001` (UTF-8) |
| `--mapid-native` | Garmin MAPID for native lang | `0x1005` |
| `--mapid-english` | Garmin MAPID for English | `0x2005` |

**Output**: Creates files in `suites/nikko_oze/`:
- `nikko_oze.mk` - Base mapsforge suite
- `nikko_oze_bc_dem.mk` - Garmin DEM with native language
- `nikko_oze_bc_dem_en.mk` - Garmin DEM with English

Build the initial suite structure:

```bash
make nikko_oze_suites
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
    --lang ja \
    --hgt-files "N36E138, N36E139, N36E140, N37E138, N37E139, N37E140"
```

**Parameters**:
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--region` | Display name | `Nikko-Oze` |
| `--region-lower` | Lowercase identifier | `nikko_oze` |
| `--title` | Page title | `Nikko-Oze Region` |
| `--lang` | Language code | `ja` |
| `--hgt-files` | Comma-separated HGT file list | `N36E138, N36E139, ...` |

**Output**: Creates `docs/Nikko-Oze/nikko_oze_topo.md`

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
  ✓ AW3D30_OSM_Nikko-Oze_TOPO_Rudy.map.zip
  ✓ AW3D30_OSM_Nikko-Oze_TOPO_Rudy.zip
  ...
All files synced successfully!
```

---

## Generated Files Summary

After completing all steps, the following files should be created:

```
taiwan-topo/
├── Makefile                                    # Updated with include
├── docs/
│   ├── Taiwan/taiwan_topo.md                   # Updated with region link
│   └── Nikko-Oze/nikko_oze_topo.md            # New documentation
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
- Created documentation (docs/Nikko-Oze/nikko_oze_topo.md)
- Added mirror checking config (tools/mirror-configs/nikko_oze.json)
```

---

## Troubleshooting

### Common Issues

1. **MAPID conflicts**: Ensure your MAPID values don't conflict with existing regions. Check `tools/generate_suite.py` for the registry.

2. **Missing HGT files**: Verify all tiles in your bounding box are included in the HGT ZIP.

3. **Build failures**: Check that the extract file exists in `download/extracts/` or will be downloaded.

4. **Mirror sync issues**: Run `./tools/check-mirrors.py -S region_lower` to diagnose sync problems.

### Getting Help

- GitHub: https://github.com/alpha-rudy/taiwan-topo
- Facebook Group: https://www.facebook.com/groups/taiwan.topo
