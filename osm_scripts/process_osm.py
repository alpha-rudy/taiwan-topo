import math
import sys

import osmium

hknetworks = {}
national_park = {}
strict_protected = {}
summit_boards = {}

_ADDR_DROP_KEYS = (
    'addr:TW:dataset',
    'addr:country',
    'addr:province',
    'addr:city',
    'addr:district',
    'addr:postcode',
    'addr:hamlet',
    'addr:neighbourhood',
    'addr:place',
    'addr:street',
    'addr:housenumber',
    'addr:housenumber_1',
    'addr:floor',
    'addr:unit',
)
_TOUGH_VIS = frozenset(('bad', 'horrible', 'no'))
_TOUGH_SAC = frozenset(('demanding_alpine_hiking', 'difficult_alpine_hiking'))
_TRAIL_HW = frozenset(('footway', 'path'))
_TOP_BAIYUE = frozenset(('玉山', '北大武山', '雪山主峰'))


class NationalParkLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        if r.tags['boundary'] == 'national_park':
            parks = {'name': r.tags['name'], 'name:en': r.tags['name:en']}
            for m in r.members:
                if m.role == 'outer' and m.type == 'w':
                    national_park[m.ref] = parks


class StrictProtectedLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        if r.tags['boundary'] == 'protected_area' and r.tags['protect_class'] == '1':
            ways = {'name': r.tags['name'], 'name:en': r.tags['name:en']}
            for m in r.members:
                if m.role == 'outer' and m.type == 'w':
                    strict_protected[m.ref] = ways


class SummitBoardLoader(osmium.SimpleHandler):
    def node(self, n):
        lon, lat = n.location.lon, n.location.lat
        summit_boards.setdefault((int(lon * 100), int(lat * 100)), []).append((lon, lat))


def near_summit_board(lon, lat, radius=100):
    # grid cells are 0.01 deg (~1 km), so the 3x3 neighbourhood covers radius
    cx, cy = int(lon * 100), int(lat * 100)
    cos_lat = math.cos(math.radians(lat)) * 111320
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            pts = summit_boards.get((cx + i, cy + j))
            if not pts:
                continue
            for x, y in pts:
                dx = (x - lon) * cos_lat
                dy = (y - lat) * 110540
                if math.hypot(dx, dy) < radius:
                    return True
    return False


def round_float(value):
    try:
        return str(round(float(value)))
    except ValueError:
        return None


class HknetworkLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        if r.tags.get('access', '') == 'no':
            return
        network = {
            'name': r.tags['name'],
            'name:en': r.tags['name:en'],
            'network': r.tags['network'],
            'ref': r.tags.get('ref', ''),
        }
        for m in r.members:
            hknetworks.setdefault(m.ref, []).append(network)


def my_g_format(the_float):
    return f"{the_float:.2f}".rstrip('0').rstrip('.')


class MapsforgeHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer

    def node(self, n):
        if len(n.tags) == 0:
            if n.id not in hknetworks:
                self.writer.add_node(n)
                return
            tags = {}
        else:
            tags = dict(n.tags)

        if n.id in hknetworks:
            self.handle_hknetwork_node(n.id, tags)

        if tags:
            if tags.get('man_made') == 'summit_board':
                self.handle_summit_board(tags)
            elif tags.get('natural') == 'peak':
                self.handle_peak(tags, n.location)
            elif tags.get('natural') == 'spring' and tags.get('drinking_water') == 'yes':
                self.handle_drinking_spring(tags)
            elif tags.get('information') == 'mobile':
                self.handle_mobile_sign(tags)
            elif (
                tags.get('highway') == 'milestone'
                and tags.get('tourism') == 'information'
                and tags.get('information') == 'route_marker'
            ):
                self.handle_trail_milestone(tags)
            elif tags.get('highway') == 'emergency_access_point':
                self.handle_eap(tags)
            elif tags.get('highway') == 'platform' and tags.get('bus') == 'yes':
                self.handle_bus_platform(tags)
            elif tags.get('amenity') == 'bicycle_rental':
                self.handle_bicycle_rental(tags)

            if 'addr:housenumber' in tags:
                self.handle_house_number(tags)

            tags['osm_id'] = f"P/{n.id}"
            n = n.replace(tags=tags)
        self.writer.add_node(n)

    def way(self, w):
        if len(w.tags) == 0 and w.id not in national_park and w.id not in strict_protected:
            self.writer.add_way(w)
            return
        tags = dict(w.tags)

        if w.id in hknetworks and 'highway' in tags:
            self.handle_hknetwork_way(w.id, tags)
        if w.id in national_park:
            self.handle_national_park(w.id, tags)
        if w.id in strict_protected:
            self.handle_strict_protected(w.id, tags)

        if tags:
            if tags.get('amenity') == 'bicycle_rental':
                self.handle_bicycle_rental(tags)
            elif tags.get('highway') in _TRAIL_HW:
                if tags.get('access') == 'no':
                    self.handle_no_access_trail(tags)
                elif tags.get('trail_visibility') in _TOUGH_VIS or tags.get('sac_scale') in _TOUGH_SAC:
                    self.handle_tough_trail(tags)

            if 'addr:housenumber' in tags:
                self.handle_house_number(tags)

            tags['osm_id'] = f"W/{w.id}"
            w = w.replace(tags=tags)
        self.writer.add_way(w)

    def relation(self, r):
        if len(r.tags) == 0:
            self.writer.add_relation(r)
            return
        tags = dict(r.tags)

        if tags.get('amenity') == 'bicycle_rental':
            self.handle_bicycle_rental(tags)

        if 'addr:housenumber' in tags:
            self.handle_house_number(tags)

        tags['osm_id'] = f"R/{r.id}"
        r = r.replace(tags=tags)
        self.writer.add_relation(r)

    def handle_eap(self, tags):
        ## handle zl tag
        if tags.get('ref'):
            try:
                ref = int(tags.get('ref'))
                if ref % 4 == 1:
                    tags['zl'] = '0'
                elif ref % 2 == 1:
                    tags['zl'] = '1'
                else:
                    tags['zl'] = '2'
            except ValueError:
                tags['zl'] = '1'
        else:
            tags['zl'] = '1'

        if tags.get('name') is None:
            if tags.get('ref') is None:
                tags['name'] = '救援樁'
            else:
                tags['name'] = '樁' + tags['ref']
        if tags.get('name:en') is None:
            if tags.get('ref') is None:
                tags['name:en'] = 'emergency'
            else:
                tags['name:en'] = '#' + tags['ref']

    def handle_mobile_sign(self, tags):
        operator_tag = 'internet_access:operator'

        if tags.get(operator_tag):
            operator = tags.get(operator_tag)

            name = '通訊點 ('
            if '中華' in operator:
                name += '中華,'
            if '遠傳' in operator:
                name += '遠傳,'
            if '星' in operator:
                name += '台星,'
            if '哥' in operator:
                name += '台哥大,'
            if '亞太' in operator:
                name += '亞太,'
            name = name.rstrip(',')  # get rid the last ','
            name += ',112)'
            tags['name'] = name

            en_name = 'mobile ('
            if '中華' in operator:
                en_name += 'CHT,'
            if '遠傳' in operator:
                en_name += 'FET,'
            if '星' in operator:
                en_name += 'T STAR,'
            if '哥' in operator:
                en_name += 'TWM,'
            if '亞太' in operator:
                en_name += 'A+,'
            en_name = en_name.rstrip(',')
            en_name += ',112)'
            tags['name:en'] = en_name

    def handle_drinking_spring(self, tags):
        if tags.get('name') is None:
            tags['name'] = '取水點'
        if tags.get('name:en') is None:
            tags['name:en'] = 'water'

    def handle_bus_platform(self, tags):
        tags['highway'] = 'bus_stop'
        tags.pop('bus')

    def handle_trail_milestone(self, tags):
        tags.pop('highway')
        tags.pop('tourism')
        tags['information'] = 'trail_milestone'

        name = ''
        # name += tags.get('network', '')  default removed network
        if tags.get('distance'):
            try:
                distance = float(tags.get('distance'))
                name += my_g_format(distance) + 'K'
                distance_n = int(round(distance, 1) * 10.0)
                if distance_n % 10 == 0:
                    tags['zl'] = '0'
                elif distance_n % 5 == 0:
                    tags['zl'] = '1'
                else:
                    tags['zl'] = '2'
            except ValueError:
                name += tags.get('distance')
        else:
            tags['zl'] = '1'

        if name:
            tags['name'] = name
            tags['name:en'] = name

    def handle_peak(self, tags, location):
        tags.pop('name', None)
        tags.pop('name:en', None)
        tags.pop('name:zh', None)
        tags['is_in'] = 'taiwan'
        # the nearby summit_board already shows ele in its name
        if near_summit_board(location.lon, location.lat):
            tags.pop('ele', None)

    def handle_summit_board(self, tags):
        ref = tags.get('ref')
        name = tags.get('name')
        if ref is not None:
            if name is None or '百岳#' not in ref:
                del tags['ref']
            else:
                # Split ref by semicolon and extract classification names (before '#')
                ref_parts = ref.split(';')
                classifications = set()
                for part in ref_parts:
                    if '#' in part:
                        classification = part.split('#')[0]
                        classifications.add(classification)

                # Check for exact classification names
                has_baiyue = '百岳' in classifications
                has_xiaobaiyue = '小百岳' in classifications

                if has_baiyue:
                    # Baiyue takes priority
                    if name in _TOP_BAIYUE:
                        tags['zl'] = '0'
                        tags['cat'] = 'baiyue'
                    else:
                        tags['zl'] = '1'
                        tags['cat'] = 'baiyue'
                elif has_xiaobaiyue:
                    tags['zl'] = '2'
                    tags['cat'] = 'xiaobaiyue'

                tags['ref'] = f'({ref})'

        ele = tags.get('ele')
        if ele is not None and name is not None:
            ele = round_float(ele.split(';')[0])
            if ele is not None:
                # name:zh too: complete_name.py fills it, and zh-preferring apps read it
                for k in ('name', 'name:en', 'name:zh'):
                    if tags.get(k):
                        tags[k] = f'{tags[k]}, {ele}m'

    def handle_hknetwork_node(self, id, tags):
        for network in hknetworks[id]:
            tags['hike_node'] = network['network']

    def handle_hknetwork_way(self, id, tags):
        for network in hknetworks[id]:
            tags['hknetwork'] = network['network']
            tags['ref'] = network['name']
            tags['ref:en'] = network['name:en']

    def handle_national_park(self, id, tags):
        tags['name'] = national_park[id]['name']
        tags['name:en'] = national_park[id]['name:en']
        tags['type'] = 'boundary'
        tags['boundary'] = 'national_park'

    def handle_strict_protected(self, id, tags):
        tags['name'] = strict_protected[id]['name']
        tags['name:en'] = strict_protected[id]['name:en']
        tags['type'] = 'boundary'
        tags['boundary'] = 'strict_protected'

    def handle_bicycle_rental(self, tags):
        brand = tags.get('brand', '').lower()
        if 'youbike' in brand:
            tags['amenity'] = 'bicycle_rental_YouBike'
        elif 'moovo' in brand:
            tags['amenity'] = 'bicycle_rental_Moovo'

    def handle_house_number(self, tags):
        if tags.get('addr:full') is None:
            tags['addr:full'] = (
                tags.get('addr:city', '').replace('臺', '台')
                + tags.get('addr:district', '')
                + tags.get('addr:place', '')
                + tags.get('addr:street', '')
                + tags.get('addr:housenumber', '')
                + tags.get('addr:floor', '')
                + tags.get('addr:unit', '')
            )

        # removes rest
        for k in _ADDR_DROP_KEYS:
            tags.pop(k, None)

    def handle_tough_trail(self, tags):
        if 'name' in tags:
            tags['name'] = tags['name'] + ' (艱難路線)'
            tags['name:en'] = tags['name:en'] + ' (tough)'
        else:
            tags['name'] = '(艱難路線)'
            tags['name:en'] = '(tough)'

    def handle_no_access_trail(self, tags):
        if 'name' in tags:
            tags['name'] = tags['name'] + ' (已封閉)'
            tags['name:en'] = tags['name:en'] + ' (closed)'
        else:
            tags['name'] = '(已封閉)'
            tags['name:en'] = '(closed)'



def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <infile> <outfile> [prefix]")
        sys.exit(-1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    prefix = sys.argv[3] if len(sys.argv) > 3 else ""

    # Use prefixed filenames to avoid conflicts between regions
    hknetworks_file = f"{prefix}_hknetworks.osm" if prefix else "hknetworks.osm"
    national_park_file = f"{prefix}_national_park.osm" if prefix else "national_park.osm"
    strict_protected_file = f"{prefix}_strict_protected.osm" if prefix else "strict_protected.osm"
    summit_board_file = f"{prefix}_summit_board.osm" if prefix else "summit_board.osm"

    nknetwork_loader = HknetworkLoader()
    nknetwork_loader.apply_file(hknetworks_file)

    national_park_loader = NationalParkLoader()
    national_park_loader.apply_file(national_park_file)

    strict_protected_loader = StrictProtectedLoader()
    strict_protected_loader.apply_file(strict_protected_file)

    summit_board_loader = SummitBoardLoader()
    summit_board_loader.apply_file(summit_board_file)

    writer = osmium.SimpleWriter(outfile)
    mapsforge_handler = MapsforgeHandler(writer)
    mapsforge_handler.apply_file(infile)
    writer.close()


if __name__ == '__main__':
    main()
