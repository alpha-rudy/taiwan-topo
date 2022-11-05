# -*- coding: utf-8 -*-
import sys
import osmium

hknetworks = {}
national_park = {}


class NationalParkLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        if r.tags['boundary'] == 'national_park':
            parks = dict([('name', r.tags['name']), ('name:en', r.tags['name:en'])])
            for m in r.members:
                if m.role == 'outer' and m.type == 'w':
                    national_park[m.ref] = parks


def round_float(value):
    try:
        return str(int(round(float(value))))
    except ValueError:
        return None


class HknetworkLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        network = dict([('name', r.tags['name']), ('name:en', r.tags['name:en']), ('network', r.tags['network']), ('ref', r.tags.get('ref', ''))])
        for m in r.members:
            if not hknetworks.get(m.ref):
                hknetworks[m.ref] = []
            hknetworks[m.ref].append(network)


def my_g_format(the_float):
    return "{:.2f}".format(the_float).rstrip('0').rstrip('.')


class MapsforgeHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer

    def node(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        if n.id in hknetworks:
            self.handle_hknetwork_node(n.id, tags)

        if tags.get('natural', '') == 'peak':
            self.handle_peak(tags)
        elif tags.get('natural', '') == 'spring' and \
                tags.get('drinking_water', '') == 'yes':
            self.handle_drinking_spring(tags)
        elif tags.get('information', '') == 'mobile':
            self.handle_mobile_sign(tags)
        elif tags.get('highway', '') == 'milestone' and \
                tags.get('tourism', '') == 'information' and \
                tags.get('information', '') == 'route_marker':
            self.handle_trail_milestone(tags)
        elif tags.get('highway', '') == 'emergency_access_point':
            self.handle_eap(tags)
        elif tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental(tags)
        
        if tags.get('addr:housenumber') != None:
            self.handle_house_number(tags)

        if len(tags) != 0:
            tags['osm_id'] = "P/{}".format(n.id)
            n = n.replace(tags=tags)
        self.writer.add_node(n)

    def way(self, w):
        tags = dict((tag.k, tag.v) for tag in w.tags)

        if w.id in hknetworks and 'highway' in tags:
            self.handle_hknetwork_way(w.id, tags)
        if w.id in national_park:
            self.handle_national_park(w.id, tags)

        if tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental(tags)
        elif tags.get('highway', '') in ['footway', 'path']:
            if tags.get('access', '') == 'no':
                self.handle_no_access_trail(tags)
            elif tags.get('trail_visibility', '') in ['bad', 'horrible', 'no'] or \
              tags.get('sac_scale', '') in ['demanding_alpine_hiking', 'difficult_alpine_hiking']:
                self.handle_tough_trail(tags)

        if tags.get('addr:housenumber') != None:
            self.handle_house_number(tags)

        if len(tags) != 0:
            tags['osm_id'] = "W/{}".format(w.id)
            w = w.replace(tags=tags)
        self.writer.add_way(w)

    def relation(self, r):
        tags = dict((tag.k, tag.v) for tag in r.tags)

        if tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental(tags)

        if tags.get('addr:housenumber') != None:
            self.handle_house_number(tags)

        if len(tags) != 0:
            tags['osm_id'] = "R/{}".format(r.id)
            r = r.replace(tags=tags)
        self.writer.add_relation(r)

    def handle_eap(self, tags):
        if tags.get('name') is None:
            if tags.get('ref') is None:
                tags['name'] = '救援樁'
            else:
                tags['name'] = tags['ref'] + ' 號救援樁'
        if tags.get('name:en') is None:
            if tags.get('ref') is None:
                tags['name:en'] = 'emergency'
            else:
                tags['name:en'] = 'emergency #' + tags['ref']

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
            tags['name'] = 'water'

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
            if not tags.get('name'):
                tags['name'] = name
            if not tags.get('name:en'):
                tags['name:en'] = name

    def handle_peak(self, tags):
        ref = tags.get('ref')
        name = tags.get('name')
        name_en = tags.get('name:en')
        if ref is not None:
            if name is None or '百岳#' not in ref:
                del tags['ref']
            else:
                if '小百岳#' in ref:
                    tags['zl'] = '2'
                else:
                    if name in ['玉山', '北大武山', '雪山主峰']:
                        tags['zl'] = '0'
                    else:
                        tags['zl'] = '1'

                tags['ref'] = '(%s)' % ref

        ele = tags.get('ele')
        if ele is not None and name is not None:
            ele = round_float(ele)
            if ele is not None:
                tags['name'] = '%s, %sm' % (name, ele)
                tags['name:en'] = '%s, %sm' % (name_en, ele)

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

    def handle_bicycle_rental(self, tags):
        # YouBike and iBike use network:en
        if tags.get('network:en', '') in ('iBike', 'YouBike'):
            tags['network'] = tags['network:en']

    def is_only_addr_tags(self, tags):
        only_addr = False  ## no tags mean no addr (False)
        for tag in tags:
            if tag.k.startswith('addr:'):
                only_addr = True  ## accumulating in True
                continue
            else:       
                only_addr = False  ## one other tags, no needd to go on
                break
        return only_addr

        # these dataset come from city government
        tags['place'] = 'address_holder'
        tags.pop('addr:tw:dataset', None)

    def handle_house_number(self, tags):
        if tags.get('addr:full') == None:
            tags['addr:full'] =  tags.get('addr:city', '').replace('臺', '台') + \
                tags.get('addr:district', '') + \
                tags.get('addr:place', '') + \
                tags.get('addr:street', '') + \
                tags.get('addr:housenumber', '') + \
                tags.get('addr:floor', '') + \
                tags.get('addr:unit', '')

        # removes rest
        tags.pop('addr:TW:dataset', None)
        tags.pop('addr:country', None)
        tags.pop('addr:province', None)
        tags.pop('addr:city', None)
        tags.pop('addr:district', None)
        tags.pop('addr:postcode', None)
        tags.pop('addr:hamlet', None)
        tags.pop('addr:neighbourhood', None)
        tags.pop('addr:place', None)
        tags.pop('addr:street', None)
        tags.pop('addr:housenumber', None)
        tags.pop('addr:housenumber_1', None)
        tags.pop('addr:floor', None)
        tags.pop('addr:unit', None)

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
    if len(sys.argv) != 3:
        print("Usage: python %s <infile> <outfile>" % sys.argv[0])
        sys.exit(-1)
    infile = sys.argv[1]
    outfile = sys.argv[2]

    nknetwork_loader = HknetworkLoader()
    nknetwork_loader.apply_file('hknetworks.osm')

    national_park_loader = NationalParkLoader()
    national_park_loader.apply_file('national_park.osm')

    writer = osmium.SimpleWriter(outfile)
    mapsforge_handler = MapsforgeHandler(writer)
    mapsforge_handler.apply_file(infile)
    writer.close()


if __name__ == '__main__':
    main()
