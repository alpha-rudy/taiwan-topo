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
            parks = dict(name=r.tags['name'])
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
        network = dict(name=r.tags['name'], network=r.tags['network'], ref=r.tags.get('ref', ''))
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
        if n.tags.get('natural', '') == 'peak':
            self.handle_peak(n)
            return
        elif n.tags.get('information', '') == 'mobile':
            self.handle_mobile_sign(n)
            return
        elif n.tags.get('highway', '') == 'milestone' and \
                n.tags.get('tourism', '') == 'information' and \
                n.tags.get('information', '') == 'route_marker':
            self.handle_trail_milestone(n)
            return
        elif n.tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental_node(n)
            return

        if n.id in hknetworks:
            self.handle_hknetwork_node(n)
            return

        self.writer.add_node(n)
        return

    def handle_bicycle_rental_node(self, n):
        n = n.replace(tags=self.handle_bicycle_rental_tags(n))
        self.writer.add_node(n)

    def handle_hknetwork_node(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        for network in hknetworks[n.id]:
            ''' disable highlight
            if network.get('ref', '') == 'twn:taipei_grand_hike':
                tags['highlight'] = 'yes'
                tags['name'] = tags['ref']
            '''
            tags['hike_node'] = network['network']

        n = n.replace(tags=tags)
        self.writer.add_node(n)

    def handle_mobile_sign(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        if tags.get('name') is None and tags.get('operator'):
            operator = tags.get('operator')
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
            name += ')'
            tags['name'] = name

        n = n.replace(tags=tags)
        self.writer.add_node(n)

    def handle_trail_milestone(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        tags.pop('highway')
        tags.pop('tourism')
        tags['information'] = 'trail_milestone'

        if tags.get('name') is None:
            name = ''
            # name += tags.get('network', '')  default removed network
            if tags.get('distance'):
                try:
                    distance = float(tags.get('distance'))
                    name += my_g_format(distance) + 'K'
                except ValueError:
                    name += tags.get('distance')
            if name:
                tags['name'] = name

        n = n.replace(tags=tags)
        self.writer.add_node(n)

    def handle_peak(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        ref = tags.get('ref')
        name = tags.get('name')
        if ref is not None:
            if name is None or '百岳#' not in ref:
                del tags['ref']
            else:
                if '小百岳#' in ref:
                    tags['zl'] = '2'
                else:
                    if name in ['玉山', '北大武山', '雪山']:
                        tags['zl'] = '0'
                    else:
                        tags['zl'] = '1'

                tags['ref'] = '(%s)' % ref

        ele = tags.get('ele')
        if ele is not None and name is not None:
            ele = round_float(ele)
            if ele is not None:
                tags['name'] = '%s, %sm' % (name, ele)

        n = n.replace(tags=tags)
        self.writer.add_node(n)

    def way(self, w):
        if w.id in hknetworks and 'highway' in w.tags:
            self.handle_hknetwork(w)
            return
        
        if w.id in national_park:
            self.handle_national_park(w)
            return

        if w.tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental_way(w)
            return

        self.writer.add_way(w)
        return

    def handle_hknetwork(self, w):
        networks = hknetworks[w.id]
        tags = dict((tag.k, tag.v) for tag in w.tags)
        for network in networks:
            ''' disable highlight
            if network.get('ref', '') == 'twn:taipei_grand_hike':
                tags['highlight'] = 'yes'
                if not tags.get('hknetwork'):
                    tags['ref'] = network['name']
            else:
            '''
            tags['hknetwork'] = network['network']
            tags['ref'] = network['name']
        w = w.replace(tags=tags)
        self.writer.add_way(w)
        return

    def handle_national_park(self, w):
        w = w.replace(tags=self.handle_national_park_tags(w))
        self.writer.add_way(w)

    def handle_national_park_tags(self, o):
        tags = dict((tag.k, tag.v) for tag in o.tags)
        tags['name'] = national_park[o.id]['name']
        tags['type'] = 'boundary'
        tags['boundary'] = 'national_park'
        return tags

    def handle_bicycle_rental_way(self, w):
        w = w.replace(tags=self.handle_bicycle_rental_tags(w))
        self.writer.add_way(w)

    def relation(self, r):
        if r.tags.get('amenity', '') == 'bicycle_rental':
            self.handle_bicycle_rental_relation(r)
            return

        self.writer.add_relation(r)
        return

    def handle_bicycle_rental_relation(self, r):
        r = r.replace(tags=self.handle_bicycle_rental_tags(r))
        self.writer.add_relation(r)

    def handle_bicycle_rental_tags(self, o):
        tags = dict((tag.k, tag.v) for tag in o.tags)
        # YouBike and iBike use network:en
        if tags.get('network:en', '') in ('iBike', 'YouBike'):
            tags['network'] = tags['network:en']
        return tags


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
