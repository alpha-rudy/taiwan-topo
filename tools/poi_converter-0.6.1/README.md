# Poi Converter
Reads POIs and creates Locus POI databases

This is a python based command line application that converts POIs (points-of-interest) into the database
format suitable for Locus vector maps.

## Installation (Ubuntu Linux):
* Install required packages: python3 git libsqlite3-mod-spatialite python3-pipenv
* Install pipenv `pip3 install pipenv`
* clone this git repository `git clone https://github.com/lieblerj/poi_converter.git`
* change into the repository `cd poi_converter`
* run `pipenv update` to download and install the necessary dependencies (pyosmium, pyspatialite and tdqm)
* run `pipenv shell` to activate the virtual environment
* running `python poiconverter.py -h` will show the following output

```
usage: poiconverter.py [-h] [-version] -if {pbf,poi} -om {create,append}
                       input_file output_file

Extracts POIs from osm file and create Locus poi database

positional arguments:
  input_file           enter input filename
  output_file          enter output spatialite filename (.db)

optional arguments:
  -h, --help           show this help message and exit
  -version             show program's version number and exit
  -if {pbf,poi}        specify input file format
  -om {create,append}  specify output mode: create will newly create database
                       and append will only append new POIs.
```

## Configuration
All configuration files are located in the config subfolder:
### init.sql
Contains SQLite commands that setup the database and create the required tables

### tagfilter.txt
Contains `<tag>=<value>` pairs which are used for filtering. The script searches for the first matching
tag,value pair and uses this to assign a type to each POI. The type is used as POI name if a POI does
not have a name tag and will also be used for Root/Subfolder mapping. The first match will be used so
tags at the top have higher priority.

### translation.txt
POIs without a name will get the type as name. The file is used to convert the name into
something more readable.

## Open topics
* only rudimentary error handling implemented
* support for POIs in ways and relations missing in PBF converter
* output tag mapping is hardcoded in python code

## Differences for PBF vs. POI input
* POI input file conversion is at least 10x faster
* POI input will use POIs from nodes, ways and relations, for PBF only nodes are supported currently

## Input file download:
* PBF files: https://download.geofabrik.de/europe/germany/bayern.html
* https://download.geofabrik.de/europe/germany/bayern/oberbayern-latest.osm.pbf
* POI files: https://www.openandromaps.org/downloads/deutschland
* http://download.openandromaps.org/pois/Germany/bayern.poi.zip


More information on the POI database format can be found here:
* https://www.openandromaps.org/oam-forums/topic/poi-nutzbarkeit-der-dateien-mit-locus
* https://gitlab.com/noschinl/locus-poi-db
