"""
POI

holds point of interest

"""
class Poi:
    def __init__(self, node_id, name, lat, lon):
        self.name = name
        self.node_id = node_id
        self.lat = lat
        self.lon = lon
        self.tags = dict()

    def set_type(self,type):
        self.type = type

    def set_osm_type(self,osm_type):
        self.osm_type = osm_type

    def add_tag(self, k, v):
        self.tags[k] = v

    def add_tags(self,tags):
        self.tags = tags
    
    def pop_tag(self, k):
        self.tags.pop(k)

    def filter_tags(self, valid_tags):
        new_tags = dict()
        for key in self.tags.keys():
            if key in valid_tags.keys():
                new_tags[key] = self.tags[key]
        self.tags = new_tags

    def translate_name(self, translations):
        if self.type in translations.keys():
                self.name = translations[self.type]

    def __repr__(self):
        return "ID: {}, Name: {}, OSM Type: {}, Lat: {}, Lon: {}, Tags:{}".format(self.node_id, self.name, self.osm_type, self.lat, self.lon, self.tags)

