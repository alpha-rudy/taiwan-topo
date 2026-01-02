"""
poiwriter

updates POI data and converts POIs for storing in database

"""
class PoiWriter:
    def __init__(self, db, translation_file):
        self.db = db
        self.available_tags = dict(db.read_tags())
        self.folders_sub = dict(db.read_folders_sub())
        translations = []

        with open(translation_file,'r',encoding='utf-8') as f:
            line = f.readline()
            while line:
                if not line.startswith('#') and len(line) > 2:
                    translations.append(line.strip().split('='))
                line = f.readline()
        self.translations = dict(translations)


    # TODO store conversion values in config file or database
    def update_poi_type(self, poi):
        if poi.type[1] not in self.folders_sub:
            if poi.type[1] == 'fuel':
                poi.set_type(('subfolder', 'gas_station'))
            elif poi.type[1] == 'summit_board':
                poi.set_type(('subfolder', 'peak'))
            elif poi.type[1] == 'air_defense_shelter':
                poi.set_type(('subfolder', 'air_defense_shelter'))
            elif poi.type[1] == 'giant_tree':
                poi.set_type(('subfolder', 'giant_tree'))
            elif poi.type[1] == 'bus_stop':
                poi.set_type(('subfolder', 'bus_and_tram_stop'))
            elif poi.type[1] == 'tram_stop':
                poi.set_type(('subfolder', 'bus_and_tram_stop'))
            elif poi.type[1] == 'station':
                poi.set_type(('subfolder', 'railway_station'))
            elif poi.type[1] == 'halt':
                poi.set_type(('subfolder', 'railway_station'))
            elif poi.type[1] == 'subway_entrance':
                poi.set_type(('subfolder', 'subway'))
            elif poi.type[1] == 'cave_entrance':
                poi.set_type(('subfolder', 'mine_cave'))
            elif poi.type[1] == 'mine':
                poi.set_type(('subfolder', 'mine_cave'))
            elif poi.type[1] == 'bureau_de_change':
                poi.set_type(('subfolder', 'exchange'))
            elif poi.type[1] in ('school', 'university', 'college', 'kindergarten'):
                poi.set_type(('subfolder', 'education'))
            elif poi.type[1] in ('doctors', 'dentist'):
                poi.set_type(('subfolder', 'doctor_dentist'))
            elif poi.type[1] in ('bar', 'pub'):
                poi.set_type(('subfolder', 'bar_pub'))
            elif poi.type[1] in ('hospital', 'clinic'):
                poi.set_type(('subfolder', 'hospital_clinic'))
            elif poi.type[1] in ('supermarket', 'convenience'):
                poi.set_type(('subfolder', 'supermarket_convenience'))
            elif poi.type[1] == 'pitch':
                poi.set_type(('subfolder', 'sport_pitch'))
            elif poi.type[1] == 'aerodrome':
                poi.set_type(('subfolder', 'airport'))
            elif poi.type[1] == 'ferry_terminal':
                poi.set_type(('subfolder', 'ferries'))
            elif poi.type[1] == 'information':
                poi.set_type(('subfolder', 'info'))
            elif poi.type[1] in ('camp_site', 'caravan_site'):
                poi.set_type(('subfolder', 'camp_caravan'))
            elif poi.type[0] == 'historic':
                poi.set_type(('subfolder', 'castle_ruin_monument'))
            elif poi.type[0] == 'shop':
                poi.set_type(('subfolder', 'other'))
            else:
                #poi.set_type(('subfolder', 'golf')) # used to find out what is not sorted properly
                pass
        return True

    def poi_map_similar_tags(self, poi):
        if 'website' in poi.tags:
            poi.add_tag('url', poi.tags.get('website'))
        if 'contact:website' in poi.tags:
            poi.add_tag('url', poi.tags.get('contact:website'))
        if 'contact:phone' in poi.tags:
            poi.add_tag('phone', poi.tags.get('contact:phone'))
        if poi.tags.get('man_made', '') == 'summit_board':
            poi.pop_tag('man_made')
            poi.add_tag('natural', 'peak')

    def write_poi(self, poi):
        if poi:
            if not self.update_poi_type(poi):
                print("Poi type unknown: {}".format(poi))
                return
            self.poi_map_similar_tags(poi)
            poi.filter_tags(self.available_tags)
            poi.translate_name(self.translations)
            self.db.write_poi(poi)
