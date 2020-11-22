"""
Create database and write POIs into file
"""
import spatialite
import os

class Database:
    def __init__(self, init_file):
        self.entries = 0
        self.init_file = init_file
        self.batch_size = 10000
        self.batched_pois = []

    def open_append(self):
        self.db = spatialite.connect(self.file_name)
        self.cursor = self.db.cursor()
        last_ROWID = self.cursor.execute("SELECT max(ROWID) from Points").fetchone()[0]
        if last_ROWID is None:
            self.first_free_points_id = 0
        else:
            self.first_free_points_id = last_ROWID + 1

    def open_create(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)
        self.db = spatialite.connect(self.file_name)
        self.cursor = self.db.cursor()
        self.initialize_database()
        self.first_free_points_id = 0

    def open(self, file, mode):
        self.file_name = file
        self.output_mode = mode
        if mode == 'create':
            self.open_create()
        elif mode == 'append':
            self.open_append()
        else:            
            raise ValueError('Wrong mode parameter')

    def close(self):
        self.write_pois()
        self.db.commit()
        self.db.close()

    def initialize_database(self):
        self.cursor = self.db.cursor()
        with open(self.init_file,'r') as f:
            sql_commands = f.readlines()
            sql = 'SELECT InitSpatialMetadata(1)'
            result = self.db.execute(sql).fetchone()
            for command in sql_commands:
                if command.strip(): #skip empty lines
                    result = self.db.execute(command)

    def insert_pois(self, pois_with_ids):
        def iterator(pois_with_ids):
            for (id, poi) in pois_with_ids:
                yield [id, poi.node_id, poi.osm_type, poi.name, "POINT({} {})".format(poi.lon, poi.lat)]

        sql = "INSERT INTO 'Points'(ROWID, id, type, name, geom) VALUES(?,?,?,?, GEOMFROMTEXT(?,4326));"
        self.cursor.executemany(sql, iterator(pois_with_ids))

    def insert_root_sub_folders(self, pois_with_ids):
        def iterator(pois_with_ids):
            for (id, poi) in pois_with_ids:
                yield [id, poi.type[1], poi.type[1]]

        sql = """INSERT INTO Points_root_sub VALUES(
            ?,
            (SELECT fr.id FROM FoldersRoot fr JOIN RootSubMapping rsm ON fr.name = rsm.rootname WHERE rsm.subname = ?),
            (SELECT fs.id FROM FoldersSub fs WHERE fs.name = ?)
        )
        """
        self.cursor.executemany(sql, iterator(pois_with_ids))

    def insert_tags(self, pois_with_ids):
        def value_iterator(pois_with_ids):
            for (_, poi) in pois_with_ids:
                for (k, v) in poi.tags.items():
                    yield [v]

        def pkv_iterator(pois_with_ids):
            for (id, poi) in pois_with_ids:
                for (k,v) in poi.tags.items():
                    yield [id, k, v]

        sql = "INSERT OR IGNORE INTO TagValues (name) VALUES(?);"
        self.cursor.executemany(sql, value_iterator(pois_with_ids))

        sql = "INSERT INTO Points_Key_Value (Points_id, TagKeys_id, TagValues_id) VALUES(?, (SELECT id FROM TagKeys WHERE TagKeys.name = ?), (SELECT id FROM TagValues WHERE TagValues.name = ?));"
        self.cursor.executemany(sql, pkv_iterator(pois_with_ids))

    def write_poi(self, poi):
        self.batched_pois.append(poi)
        self.entries += 1
        if len(self.batched_pois) >= self.batch_size:
            self.write_pois()

    def write_pois(self):
        pois_with_ids = []
        for poi in self.batched_pois:
            pois_with_ids.append((self.first_free_points_id, poi))
            self.first_free_points_id += 1

        self.insert_pois(pois_with_ids)
        self.insert_root_sub_folders(pois_with_ids)
        self.insert_tags(pois_with_ids)
        self.batched_pois.clear()


    def read_tags(self):
        sql = "SELECT name, id from TagKeys;"
        result = self.db.execute(sql).fetchall()
        return result

    def read_folders_sub(self):
        sql = "SELECT name, id from FoldersSub;"
        result = self.db.execute(sql).fetchall()
        return result
