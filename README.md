# *Taiwan TOPO* Taiwan Hiking/Geocaching Maps

## Usage

    $ make SUITE=taiwan_bw gmapsupp

## SUITE list

* Garmin GMAP Maps
  * `taiwan_bw`: Taiwan region, bw style
  * `taiwan_odc`: Taiwan region, odc style
* Mapsforge Maps
  * `taiwan`: Taiwan

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

