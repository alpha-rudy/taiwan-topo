import osmium
from poiconverter.poi import Poi

class FileImporter(osmium.SimpleHandler):

    def __init__(self, callback, tag_filter):
        osmium.SimpleHandler.__init__(self)
        self.callback = callback
        self.tag_filter = tag_filter

    def handle_node(self, node):
        node_tags = dict()
        for k,v in node.tags:
            node_tags[k] = v
        node_type = self.tag_filter.tag_matched(node_tags)
        if node_type:
            name = node.tags.get('name', '')
            poi = Poi(node.id, name, node.location.lat, node.location.lon)
            poi.set_type(node_type)
            poi.add_tags(node_tags)
            poi.set_osm_type('P')
            self.callback(poi)

    def node(self, node):
        self.handle_node(node)
