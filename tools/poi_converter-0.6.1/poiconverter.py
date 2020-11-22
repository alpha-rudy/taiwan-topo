"""
POI Converter

Extracts POIs from osm file and create Locus poi database

"""
import sys
import argparse
import time
import os

from poiconverter.poi import Poi
from poiconverter.database import Database
from poiconverter.fileimporter import FileImporter
from poiconverter.poiimporter import PoiImporter
from poiconverter.poiwriter import PoiWriter
from poiconverter.tagfilter import TagFilter

version = '0.6.1' # update version

def main():
    parser = argparse.ArgumentParser(description='Extracts POIs from osm file and create Locus poi database')
    parser.add_argument('input_file', help='enter input filename')
    parser.add_argument('output_file', help='enter output spatialite filename (.db)')
    parser.add_argument('-version', action='version', version='%(prog)s ' + version)
    parser.add_argument('-if', dest='input_format', required=True, choices=['pbf', 'poi'],
                    help="specify input file format")
    parser.add_argument('-om', dest='output_mode', required=True, choices=['create', 'append'],
                    help="specify output mode: create will newly create database and append will only append new POIs.")

    arguments = parser.parse_args()

    if not os.path.isfile(arguments.input_file):
        print("input file '{}' does not exist!".format(arguments.input_file))
        sys.exit(1)

    script_root_dir = os.path.dirname(os.path.realpath(__file__))

    db = Database(os.path.join(script_root_dir,'config/init.sql'))

    start_time = time.time()
    print("Preparing database, please wait ... ", end='')
    sys.stdout.flush()
    db.open(arguments.output_file, arguments.output_mode)
    print("finished!")

    tag_filter = TagFilter(os.path.join(script_root_dir,'config/tagfilter.txt'))
    writer = PoiWriter(db, os.path.join(script_root_dir,'config/translation.txt'))

    if arguments.input_format == 'poi':
        importer = PoiImporter(writer.write_poi, tag_filter)
    elif arguments.input_format == 'pbf':
        importer = FileImporter(writer.write_poi, tag_filter)
    else:
        sys.exit(2)

    print("Adding POIs ... ")
    importer.apply_file(arguments.input_file)
    db.close()
    print("Finished!")

    print("{} POIs added to database in {:.2f} sec!".format(db.entries, (time.time()-start_time)))

if __name__ == "__main__":
    main()
