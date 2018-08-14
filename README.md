# *Taiwan TOPO* Taiwan Hiking/Geocaching Maps

## Before getting start

Since GitHub cannot host large data for pre-generated contour lines, please download all the files from [Dropbox](https://www.dropbox.com/sh/zek16veghjhs9d2/AAC3nfwMvilok9Fzaugjb0ZGa?dl=0) and put them into `$HOME/osm_elevations`.

## Usage

    $ make SUITE=taiwan_bw gmapsupp   ### make a Garmin handheld map
    
    $ make SUITE=taiwan mapsforge   ### make a mapsforge map
    
    $ make SUITE=bbox REGION=陽明山 \  ### make a small mapsforge map 
        TOP=25.24917 BOTTOM=25.11332 \
        LEFT=121.48012 RIGHT=121.63218 \ 
        mapsforge

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

