# -*- coding: utf-8 -*-
import sys
import osmium


class GPXHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer

    def node(self, n):
        if n.tags.get('gpx','') == 'wpt' and n.tags.get('sym', ''):
            self.handle_sym_waypoint(n)
            return

        self.writer.add_node(n)
        return

    def way(self, w):
        if w.tags.get('gpx','') == 'trk' and w.tags.get('color', ''):
            self.handle_color_track(w)
            return

        self.writer.add_way(w)
        return

    def relation(self, r):
        self.writer.add_relation(r)
        return

    def handle_color_track(self, w):
        w = w.replace(tags=self.handle_color_tag(w))
        self.writer.add_way(w)

    def handle_color_tag(self, o):
        tags = dict((tag.k, tag.v) for tag in o.tags)
        tags['color'] = ''.join(c for c in tags['color'] if c.isalnum())
        return tags

    def handle_sym_waypoint(self, n):
        n = n.replace(tags=self.handle_sym_tag(n))
        self.writer.add_node(n)

    def handle_sym_tag(self, o):
        tags = dict((tag.k, tag.v) for tag in o.tags)
        tags['sym'] = ''.join(c for c in tags['sym'] if c.isalnum())
        return tags


def main():
    if len(sys.argv) != 3:
        print("Usage: python %s <infile> <outfile>" % sys.argv[0])
        sys.exit(-1)
    infile = sys.argv[1]
    outfile = sys.argv[2]

    writer = osmium.SimpleWriter(outfile)
    handler = GPXHandler(writer)
    handler.apply_file(infile)
    writer.close()


if __name__ == '__main__':
    main()
