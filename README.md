# *Taiwan TOPO* Taiwan Hiking/Geocaching Maps

## Usage

    $ make SUITE=taiwan_bw gmapsupp   ### make a Garmin handheld map
    
    $ make SUITE=taiwan mapsforge   ### make a mapsforge map
    
    $ make SUITE=bbox REGION=陽明山 \
        TOP=25.24917 BOTTOM=25.11332 \
        LEFT=121.48012 RIGHT=121.63218 \ 
        mapsforge

    $ make SUITE=bbox REGION=kumano_kodo \
        DEM_NAME=AW3D30 LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        ELEVATION_MIX_FILE=ele_kumano_kodo_10_100_500_mix.pbf \
        EXTRACT_FILE=japan-latest \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        mapsforge_zip poi_v2

    $ make SUITE=bbox_bc_dem REGION=kumano \
        DEM_NAME=AW3D LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        EXTRACT_FILE=japan-latest \
        GMAPDEM=/home/rudychung/Works/taiwan-topo/hgt/kumano_hgtmix.zip \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        gmap nsis

    $ make SUITE=bbox_odc_dem REGION=kumano \
        DEM_NAME=AW3D LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        EXTRACT_FILE=japan-latest \
        GMAPDEM=/home/rudychung/Works/taiwan-topo/hgt/kumano_hgtmix.zip \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        gmapsupp_zip

## Docker Usage

Build with your user ID to avoid permission issues:

```bash
docker build \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) \
  -t taiwan-contour:latest .
```

Running Make Commands Directly:
    
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -u builder \
  taiwan-contour:latest \
  make SUITE=taiwan mapsforge
```

Using a Wrapper Script:

```bash
./tools/docker-make SUITE=taiwan mapsforge
```

## SUITE list

* Garmin GMAP Maps
  * `taiwan_bw`: Taiwan region, bw style
  * `taiwan_odc`: Taiwan region, odc style
  * `bbox_bw`: Bonding Box, bw style (TOP/BOTTOM/LEFT/RIGHT)
  * `bbox_odc`: Bonding Box, odc style (TOP/BOTTOM/LEFT/RIGHT)
* Mapsforge Maps
  * `taiwan`: Taiwan
  * `bbox`: Bonding Box with coords (TOP/BOTTOM/LEFT/RIGHT)

## target list

* `all`
  * for Garmin GMAP, it is `gmap`, `gmapsupp`, `nsis`
  * for Mapsforge, it is `mapsforge`, `mapsforge_style`
* `distclean`
  * clean every thing, include downloaded maps
* `clean`
  * clean compilation stuff
* `install`
  * develping use, copy GMAP .img file to $INSTALL_DIR
* `drop`
  * daily build use, copy `all` targets to $INSTALL_DIR
* `gmap`
  * macOS installer
* `gmapsupp`
  * Garmin handheld gmapsupp.img
* `nsis`
  * Windows installer
* `mapsforge`
  * Mapsforge map
* `mapsforge_style`
  * Mapsforge style

