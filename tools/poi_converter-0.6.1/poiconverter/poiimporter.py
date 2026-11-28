'''
Importer for OpenAndroMaps (v2) and Mapsforge (v3) POI databases.

File format:
- sqlite3 database with 3 tables: poi_index, poi_categories and poi_data

- poi_index contains index and boundary box for location as R*tree (v2) or lat/lon columns (v3)
- poi_data contains index and tags as string
- poi_categories contains category tree (not used)

'''

import re
import sqlite3

from tqdm import tqdm

from poiconverter.poi import Poi

_TAIWAN_OSM_ID_RE = re.compile(r'(P|W)/(\d+)')
_OAM_OSM_ID_RE = re.compile(r'openstreetmap\.org/(node|way|relation)/(\d+)')
_OAM_TYPE_MAP = {
    'node': 'P',
    'way': 'W',
    'relation': 'R',
}


class PoiImporter:

    def __init__(self, callback, tag_filter):
        self.callback = callback
        self.tag_filter = tag_filter

    def osm_get_info(self, osm_data):
        result = _TAIWAN_OSM_ID_RE.search(osm_data)
        if result:
            osm_id = int(result.group(2))
            osm_type = 'W' if result.group(1) == 'W' else 'P'
            return osm_id, osm_type

        result = _OAM_OSM_ID_RE.search(osm_data)
        if result:
            osm_id = int(result.group(2))
            osm_type = _OAM_TYPE_MAP[result.group(1)]
            return osm_id, osm_type

        return None, None

    def parse_tags(self, data):
        tags = {}
        if not data:
            return tags

        if '\r\n' in data:
            data = data.replace('\r\n', ' ')
        if '\r' in data:
            data = data.replace('\r', '\n')

        for line in data.split('\n'):
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            tags[key] = value

        return tags

    def handle_result(self, row, version):
        if version >= 3:
            row_id = row[0]
            lat = row[1]
            lon = row[2]
            data = row[3]
        else:
            row_id = None
            lat = (row[0] + row[1]) / 2
            lon = (row[2] + row[3]) / 2
            data = row[4]

        tags = self.parse_tags(data)
        node_type = self.tag_filter.tag_matched(tags)
        if not node_type:
            return

        name = tags.get('name')

        # Prefer Taiwan-TOPO osm_id (P/W/<id>) or OpenAndroMaps osm_id_link when present.
        parsed_id, parsed_type = self.osm_get_info(
            tags.get('osm_id') or tags.get('osm_id_link') or ''
        )
        if parsed_id is not None:
            osm_id = parsed_id
            osm_type = parsed_type or 'P'
        elif version >= 3 and row_id is not None:
            osm_id = row_id
            osm_type = 'P'
        else:
            osm_id = 0
            osm_type = 'P'

        poi = Poi(osm_id, name, lat, lon)
        poi.set_osm_type(osm_type)
        poi.set_type(node_type)
        poi.add_tags(tags)

        self.callback(poi)

    def apply_file(self, filename):
        with sqlite3.connect(filename) as connection:
            cursor = connection.cursor()

            tables = {
                row[0]
                for row in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

            if 'metadata' in tables:
                try:
                    version = int(
                        cursor.execute(
                            "SELECT value FROM metadata WHERE name='version'"
                        ).fetchone()[0]
                    )
                except (TypeError, ValueError, sqlite3.Error):
                    version = 2
            else:
                version = 2

            if version >= 3:
                sql = """
                SELECT
                    poi_index.id,
                    poi_index.lat,
                    poi_index.lon,
                    poi_data.data
                FROM poi_index
                JOIN poi_data USING(id)
                """
            else:
                sql = """
                SELECT
                    poi_index.minLat,
                    poi_index.maxLat,
                    poi_index.minLon,
                    poi_index.maxLon,
                    poi_data.data
                FROM poi_index
                JOIN poi_data USING(id)
                """

            result = cursor.execute(sql)

            for row in tqdm(result, unit=' entries', smoothing=0.1, mininterval=1.0, miniters=10000):
                self.handle_result(row, version)
