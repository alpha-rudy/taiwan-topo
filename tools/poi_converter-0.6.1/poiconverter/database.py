"""
Create database and write POIs into file
"""
import os

import spatialite

_DEFERRED_CREATE_PREFIXES = (
    "SELECT CreateSpatialIndex('Points', 'geom')",
    "CREATE INDEX idx_pkv_points_id ",
    "CREATE INDEX idx_prs_points_id ",
    "CREATE INDEX idx_prs_root ",
    "CREATE INDEX idx_prs_root_sub ",
)


class Database:
    def __init__(self, init_file):
        self.entries = 0
        self.init_file = init_file
        self.batch_size = 50000
        self.batched_pois = []
        self._deferred_sql = []
        self._bulk_create = False
        self._root_sub_map = {}
        self._tag_keys = {}
        self._tag_values = {}
        self._next_tag_value_id = 1
        self._missing_rootsub = set()
        self._missing_folderssub = set()

    def _load_caches(self):
        # Cache static folder mapping: subname -> (FoldersRoot_id, FoldersSub_id)
        root_by_sub = {}
        for subname, fr_id in self.cursor.execute(
            "SELECT rsm.subname, fr.id "
            "FROM FoldersRoot fr "
            "JOIN RootSubMapping rsm ON fr.name = rsm.rootname"
        ):
            if subname not in root_by_sub:
                root_by_sub[subname] = fr_id

        sub_by_name = {}
        for subname, fs_id in self.cursor.execute("SELECT name, id FROM FoldersSub"):
            if subname not in sub_by_name:
                sub_by_name[subname] = fs_id

        self._root_sub_map = {}
        for subname, fr_id in root_by_sub.items():
            fs_id = sub_by_name.get(subname)
            if fs_id is not None:
                self._root_sub_map[subname] = (fr_id, fs_id)
        self._root_by_sub = root_by_sub
        self._sub_by_name = sub_by_name

        # Preserve first-row id when TagKeys has duplicate names (matches SQL subquery)
        self._tag_keys = {}
        for name, tid in self.cursor.execute("SELECT name, id FROM TagKeys ORDER BY id ASC"):
            if name not in self._tag_keys:
                self._tag_keys[name] = tid

        # Load any existing TagValues (empty in create mode, populated in append mode)
        self._tag_values = {}
        max_tv_id = 0
        for tid, name in self.cursor.execute("SELECT id, name FROM TagValues"):
            self._tag_values[name] = tid
            max_tv_id = max(max_tv_id, tid)
        self._next_tag_value_id = max_tv_id + 1

    def open_append(self):
        self.db = spatialite.connect(self.file_name)
        self.cursor = self.db.cursor()
        self._bulk_create = False
        last_ROWID = self.cursor.execute("SELECT max(ROWID) from Points").fetchone()[0]
        if last_ROWID is None:
            self.first_free_points_id = 0
        else:
            self.first_free_points_id = last_ROWID + 1
        self._load_caches()

    def open_create(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)
        self.db = spatialite.connect(self.file_name)
        self.cursor = self.db.cursor()
        self._bulk_create = True
        self.db.execute("PRAGMA synchronous = OFF")
        self.db.execute("PRAGMA journal_mode = MEMORY")
        self.db.execute("PRAGMA temp_store = MEMORY")
        self.db.execute("PRAGMA cache_size = -131072")
        self.initialize_database()
        self.first_free_points_id = 0
        self._load_caches()

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
        if self._missing_rootsub:
            print("\nWarning: missing RootSubMapping for subnames:", sorted(self._missing_rootsub))
        if self._missing_folderssub:
            print("\nWarning: missing FoldersSub for subnames:", sorted(self._missing_folderssub))

        if self._bulk_create:
            # Build Points spatial index and secondary indexes after bulk insert
            for cmd in self._deferred_sql:
                self.db.execute(cmd)
            self._deferred_sql.clear()
        self.db.commit()
        if self._bulk_create:
            self.db.execute("PRAGMA journal_mode = DELETE")
            self.db.execute("PRAGMA synchronous = FULL")
        self.db.close()

    def initialize_database(self):
        self.cursor = self.db.cursor()
        self._deferred_sql = []
        with open(self.init_file, 'r') as f:
            sql_commands = f.readlines()
            self.db.execute('SELECT InitSpatialMetadata(1)').fetchone()
            for command in sql_commands:
                stripped = command.strip()
                if not stripped or stripped.startswith('--'):
                    continue
                if stripped.startswith(_DEFERRED_CREATE_PREFIXES):
                    self._deferred_sql.append(stripped)
                else:
                    self.db.execute(stripped)

    def insert_pois(self, pois_with_ids):
        def iterator(pois_with_ids):
            for (id, poi) in pois_with_ids:
                yield [id, poi.node_id, poi.osm_type, poi.name, f"POINT({poi.lon} {poi.lat})"]

        sql = "INSERT INTO 'Points'(ROWID, id, type, name, geom) VALUES(?,?,?,?, GEOMFROMTEXT(?,4326));"
        self.cursor.executemany(sql, iterator(pois_with_ids))

    def insert_root_sub_folders(self, pois_with_ids):
        root_sub_map = self._root_sub_map
        root_by_sub = self._root_by_sub
        valid_rows = []
        for pid, poi in pois_with_ids:
            subname = poi.type[1]
            mapped = root_sub_map.get(subname)
            if mapped is not None:
                valid_rows.append((pid, mapped[0], mapped[1]))
            elif subname not in root_by_sub:
                self._missing_rootsub.add(subname)
            else:
                self._missing_folderssub.add(subname)

        if valid_rows:
            self.cursor.executemany("INSERT INTO Points_root_sub VALUES(?, ?, ?)", valid_rows)

    def insert_tags(self, pois_with_ids):
        tag_keys = self._tag_keys
        tag_values = self._tag_values
        next_tv_id = self._next_tag_value_id
        new_tag_values = []
        pkv_rows = []

        for pid, poi in pois_with_ids:
            for k, v in poi.tags.items():
                tk_id = tag_keys.get(k)
                tv_id = tag_values.get(v)
                if tv_id is None:
                    tv_id = next_tv_id
                    next_tv_id += 1
                    tag_values[v] = tv_id
                    new_tag_values.append((tv_id, v))
                pkv_rows.append((pid, tk_id, tv_id))

        self._next_tag_value_id = next_tv_id
        if new_tag_values:
            self.cursor.executemany(
                "INSERT INTO TagValues (id, name) VALUES(?, ?);",
                new_tag_values,
            )
        if pkv_rows:
            self.cursor.executemany(
                "INSERT INTO Points_Key_Value (Points_id, TagKeys_id, TagValues_id) VALUES(?, ?, ?);",
                pkv_rows,
            )

    def write_poi(self, poi):
        self.batched_pois.append(poi)
        self.entries += 1
        if len(self.batched_pois) >= self.batch_size:
            self.write_pois()

    def write_pois(self):
        if not self.batched_pois:
            return
        start_id = self.first_free_points_id
        pois_with_ids = list(enumerate(self.batched_pois, start=start_id))
        self.first_free_points_id = start_id + len(pois_with_ids)

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
