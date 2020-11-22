-- SQL database initialization for Locus POI db
-- initial version by Lars Noschinski, https://gitlab.com/noschinl/locus-poi-db

CREATE TABLE FoldersRoot (id INTEGER NOT NULL PRIMARY KEY,name TEXT NOT NULL);
CREATE TABLE FoldersSub (id INTEGER NOT NULL PRIMARY KEY,name TEXT NOT NULL);

CREATE TABLE TagKeys (id INTEGER NOT NULL PRIMARY KEY,name TEXT NOT NULL);
CREATE TABLE TagValues (id INTEGER NOT NULL PRIMARY KEY,name TEXT NOT NULL, UNIQUE(name));

CREATE TABLE Points_Root_Sub (Points_id INTEGER NOT NULL,FoldersRoot_id INTEGER NOT NULL,FoldersSub_id INTEGER NOT NULL);
CREATE TABLE Points_Key_Value (Points_id INTEGER NOT NULL,TagKeys_id INTEGER NOT NULL,TagValues_id INTEGER NOT NULL);
CREATE TABLE Points (id INTEGER NOT NULL,type TEXT NOT NULL,name TEXT);
SELECT AddGeometryColumn('Points', 'geom', 4326, 'POINT', 'XY');
SELECT CreateSpatialIndex('Points', 'geom');

CREATE TABLE Regions (id BIGINT NOT NULL PRIMARY KEY);
SELECT AddGeometryColumn('Regions', 'geom', 4326, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('Regions', 'geom');
CREATE TABLE Regions_Names (regionid BIGINT NOT NULL,langcode TEXT NOT NULL, name TEXT, namenorm TEXT NOT NULL);

CREATE TABLE Cities (id BIGINT NOT NULL PRIMARY KEY,type INT NOT NULL, parentcityid BIGINT, regionid BIGINT, lon INT, lat INT);
SELECT AddGeometryColumn('Cities', 'center', 4326, 'POINT', 'XY');
SELECT AddGeometryColumn('Cities', 'geom', 4326, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('Cities', 'geom');

CREATE TABLE Cities_Names (cityid BIGINT NOT NULL,langcode TEXT NOT NULL, name TEXT, namenorm TEXT NOT NULL);
CREATE VIEW View_Cities_Def_Names AS SELECT Cities.ROWID as ROWID, Cities.id, Cities_Names.name, Cities_Names.namenorm, Cities.geom FROM Cities JOIN Cities_Names ON Cities.id = Cities_Names.cityid WHERE Cities_Names.langcode = 'def';
INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only) VALUES ('view_cities_def_names', 'geom', 'rowid', 'cities', 'geom', 1);

CREATE TABLE Streets (id INT NOT NULL PRIMARY KEY,name ,namenorm TEXT NOT NULL, data BLOB);
SELECT AddGeometryColumn('Streets', 'geom', 4326, 'MULTILINESTRING', 'XY');
SELECT CreateSpatialIndex('Streets', 'geom');
CREATE TABLE Street_In_Cities (streetid INT NOT NULL,cityid BIGINT NOT NULL);

CREATE TABLE Postcodes (id INTEGER PRIMARY KEY, postcode TEXT);

CREATE TABLE MetaData (id TEXT PRIMARY KEY,value TEXT);

-- Create indices
CREATE INDEX idx_cities_lon_lat ON Cities (lon, lat);
CREATE INDEX idx_cities_names_cityid ON Cities_Names (cityid);
CREATE INDEX idx_cities_names_namenorm ON Cities_Names (namenorm, langcode);
CREATE INDEX idx_pkv_points_id ON Points_Key_Value (Points_id);
CREATE INDEX idx_prs_points_id ON Points_Root_Sub (Points_id);
CREATE INDEX idx_prs_root ON Points_Root_Sub (FoldersRoot_id);
CREATE INDEX idx_prs_root_sub ON Points_Root_Sub (FoldersRoot_id, FoldersSub_id);
CREATE INDEX idx_regions_names_cityid ON Regions_Names (regionid);
CREATE INDEX idx_regions_names_langcode ON Regions_Names (langcode);
-- Called 'idx_strees_in_cities_cityid' in LoMaps
CREATE INDEX idx_streets_in_cities_cityid ON Street_In_Cities (cityid);
-- Called 'idx_strees_in_cities_streetid' in LoMaps
CREATE INDEX idx_streets_in_cities_streetid ON Street_In_Cities (streetid);
CREATE INDEX idx_streets_namenorm ON Streets (namenorm);

-- fill in metadata, seems not used in Locus
INSERT INTO 'MetaData' VALUES ('versiondbpoi', '1');
INSERT INTO 'MetaData' VALUES ('versiondbaddress', '1');

-- fill in root and sub folder values 
INSERT INTO FoldersRoot (name) VALUES ('accommodation');
INSERT INTO FoldersRoot (name) VALUES ('financial_post_services');
INSERT INTO FoldersRoot (name) VALUES ('culture_tourism');
INSERT INTO FoldersRoot (name) VALUES ('public_services');
INSERT INTO FoldersRoot (name) VALUES ('hiking_cycling');
INSERT INTO FoldersRoot (name) VALUES ('nature');
INSERT INTO FoldersRoot (name) VALUES ('emergency_health');
INSERT INTO FoldersRoot (name) VALUES ('place_of_worship');
INSERT INTO FoldersRoot (name) VALUES ('food_drink');
INSERT INTO FoldersRoot (name) VALUES ('shopping');
INSERT INTO FoldersRoot (name) VALUES ('sport_leisure');
INSERT INTO FoldersRoot (name) VALUES ('car_services');
INSERT INTO FoldersRoot (name) VALUES ('transportation');


INSERT INTO FoldersSub (name)  VALUES ('alpine_hut');
INSERT INTO FoldersSub (name)  VALUES ('camp_caravan');
INSERT INTO FoldersSub (name)  VALUES ('motel');
INSERT INTO FoldersSub (name)  VALUES ('hostel');
INSERT INTO FoldersSub (name)  VALUES ('hotel');
INSERT INTO FoldersSub (name)  VALUES ('bank');
INSERT INTO FoldersSub (name)  VALUES ('exchange');
INSERT INTO FoldersSub (name)  VALUES ('atm');
INSERT INTO FoldersSub (name)  VALUES ('post_office');
INSERT INTO FoldersSub (name)  VALUES ('post_box');
INSERT INTO FoldersSub (name)  VALUES ('info');
INSERT INTO FoldersSub (name)  VALUES ('museum');
INSERT INTO FoldersSub (name)  VALUES ('cinema');
INSERT INTO FoldersSub (name)  VALUES ('theatre');
INSERT INTO FoldersSub (name)  VALUES ('castle_ruin_monument');
INSERT INTO FoldersSub (name)  VALUES ('attraction');
INSERT INTO FoldersSub (name)  VALUES ('toilets');
INSERT INTO FoldersSub (name)  VALUES ('townhall');
INSERT INTO FoldersSub (name)  VALUES ('library');
INSERT INTO FoldersSub (name)  VALUES ('education');
INSERT INTO FoldersSub (name)  VALUES ('embassy');
INSERT INTO FoldersSub (name)  VALUES ('telephone');
INSERT INTO FoldersSub (name)  VALUES ('grave_yard');
INSERT INTO FoldersSub (name)  VALUES ('parking');
INSERT INTO FoldersSub (name)  VALUES ('bicycle_parking');
INSERT INTO FoldersSub (name)  VALUES ('guidepost');
INSERT INTO FoldersSub (name)  VALUES ('map');
INSERT INTO FoldersSub (name)  VALUES ('picnic_site');
INSERT INTO FoldersSub (name)  VALUES ('shelter');
INSERT INTO FoldersSub (name)  VALUES ('viewpoint');
INSERT INTO FoldersSub (name)  VALUES ('protected_area');
INSERT INTO FoldersSub (name)  VALUES ('peak');
INSERT INTO FoldersSub (name)  VALUES ('spring');
INSERT INTO FoldersSub (name)  VALUES ('mine_cave');
INSERT INTO FoldersSub (name)  VALUES ('glacier');
INSERT INTO FoldersSub (name)  VALUES ('fire_station');
INSERT INTO FoldersSub (name)  VALUES ('police');
INSERT INTO FoldersSub (name)  VALUES ('doctor_dentist');
INSERT INTO FoldersSub (name)  VALUES ('hospital_clinic');
INSERT INTO FoldersSub (name)  VALUES ('veterinary');
INSERT INTO FoldersSub (name)  VALUES ('buddhist');
INSERT INTO FoldersSub (name)  VALUES ('christian');
INSERT INTO FoldersSub (name)  VALUES ('hindu');
INSERT INTO FoldersSub (name)  VALUES ('jewish');
INSERT INTO FoldersSub (name)  VALUES ('muslim');
INSERT INTO FoldersSub (name)  VALUES ('shinto');
INSERT INTO FoldersSub (name)  VALUES ('taoist');
INSERT INTO FoldersSub (name)  VALUES ('bar_pub');
INSERT INTO FoldersSub (name)  VALUES ('cafe');
INSERT INTO FoldersSub (name)  VALUES ('restaurant');
INSERT INTO FoldersSub (name)  VALUES ('fast_food');
INSERT INTO FoldersSub (name)  VALUES ('confectionery');
INSERT INTO FoldersSub (name)  VALUES ('drinking_water');
INSERT INTO FoldersSub (name)  VALUES ('veg_food');
INSERT INTO FoldersSub (name)  VALUES ('department_store');
INSERT INTO FoldersSub (name)  VALUES ('pharmacy');
INSERT INTO FoldersSub (name)  VALUES ('bakery');
INSERT INTO FoldersSub (name)  VALUES ('other');
INSERT INTO FoldersSub (name)  VALUES ('supermarket_convenience');
INSERT INTO FoldersSub (name)  VALUES ('sport_outdoor');
INSERT INTO FoldersSub (name)  VALUES ('golf');
INSERT INTO FoldersSub (name)  VALUES ('swimming');
INSERT INTO FoldersSub (name)  VALUES ('sport_centre');
INSERT INTO FoldersSub (name)  VALUES ('sport_pitch');
INSERT INTO FoldersSub (name)  VALUES ('stadium');
INSERT INTO FoldersSub (name)  VALUES ('skiing');
INSERT INTO FoldersSub (name)  VALUES ('clubs_dancing');
INSERT INTO FoldersSub (name)  VALUES ('gas_station');
INSERT INTO FoldersSub (name)  VALUES ('rest_area');
INSERT INTO FoldersSub (name)  VALUES ('car_shop_and_repair');
INSERT INTO FoldersSub (name)  VALUES ('bus_and_tram_stop');
INSERT INTO FoldersSub (name)  VALUES ('bus_station');
INSERT INTO FoldersSub (name)  VALUES ('railway_station');
INSERT INTO FoldersSub (name)  VALUES ('subway');
INSERT INTO FoldersSub (name)  VALUES ('airport');
INSERT INTO FoldersSub (name)  VALUES ('ferries');


-- fill in tag keys (used in Poi detailed view)
INSERT INTO TagKeys (name) VALUES ('tourism');
INSERT INTO TagKeys (name) VALUES ('amenity');
INSERT INTO TagKeys (name) VALUES ('information');
INSERT INTO TagKeys (name) VALUES ('historic');
INSERT INTO TagKeys (name) VALUES ('landuse');
INSERT INTO TagKeys (name) VALUES ('boundary');
INSERT INTO TagKeys (name) VALUES ('natural');
INSERT INTO TagKeys (name) VALUES ('man_made');
INSERT INTO TagKeys (name) VALUES ('religion');
INSERT INTO TagKeys (name) VALUES ('shop');
INSERT INTO TagKeys (name) VALUES ('diet:vegetarian');
INSERT INTO TagKeys (name) VALUES ('diet:lacto_vegetarian');
INSERT INTO TagKeys (name) VALUES ('diet:ovo_vegetarian');
INSERT INTO TagKeys (name) VALUES ('diet:vegan');
INSERT INTO TagKeys (name) VALUES ('diet:fruitarian');
INSERT INTO TagKeys (name) VALUES ('vegetarian');
INSERT INTO TagKeys (name) VALUES ('leisure');
INSERT INTO TagKeys (name) VALUES ('sport');
INSERT INTO TagKeys (name) VALUES ('aerialway');
INSERT INTO TagKeys (name) VALUES ('club');
INSERT INTO TagKeys (name) VALUES ('highway');
INSERT INTO TagKeys (name) VALUES ('railway');
INSERT INTO TagKeys (name) VALUES ('station');
INSERT INTO TagKeys (name) VALUES ('aeroway');
INSERT INTO TagKeys (name) VALUES ('brand');
INSERT INTO TagKeys (name) VALUES ('cuisine');
INSERT INTO TagKeys (name) VALUES ('description');
INSERT INTO TagKeys (name) VALUES ('opening_hours');
INSERT INTO TagKeys (name) VALUES ('operator');
INSERT INTO TagKeys (name) VALUES ('shop');
INSERT INTO TagKeys (name) VALUES ('sport');
INSERT INTO TagKeys (name) VALUES ('stars');
INSERT INTO TagKeys (name) VALUES ('wikipedia');
INSERT INTO TagKeys (name) VALUES ('denomination');
INSERT INTO TagKeys (name) VALUES ('email');
INSERT INTO TagKeys (name) VALUES ('phone');
INSERT INTO TagKeys (name) VALUES ('url');
INSERT INTO TagKeys (name) VALUES ('bus_lines');
INSERT INTO TagKeys (name) VALUES ('bus_routes');
INSERT INTO TagKeys (name) VALUES ('route_ref');
INSERT INTO TagKeys (name) VALUES ('wheelchair');
INSERT INTO TagKeys (name) VALUES ('shelter');
INSERT INTO TagKeys (name) VALUES ('network');
INSERT INTO TagKeys (name) VALUES ('access');
INSERT INTO TagKeys (name) VALUES ('fee');


-- Table not in official database, but used for folder mapping
CREATE TABLE RootSubMapping (id INTEGER NOT NULL PRIMARY KEY, subname TEXT NOT NULL, rootname TEXT NOT NULL);

INSERT INTO RootSubMapping (subname, rootname)  VALUES ('alpine_hut','accommodation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('camp_caravan','accommodation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('motel','accommodation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('hostel','accommodation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('hotel','accommodation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bank','financial_post_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('exchange','financial_post_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('atm','financial_post_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('post_office','financial_post_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('post_box','financial_post_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('info','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('museum','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('cinema','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('theatre','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('castle_ruin_monument','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('attraction','culture_tourism');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('toilets','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('townhall','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('library','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('education','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('embassy','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('telephone','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('grave_yard','public_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bicycle_parking','hiking_cycling');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('guidepost','hiking_cycling');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('map','hiking_cycling');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('picnic_site','hiking_cycling');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('shelter','hiking_cycling');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('viewpoint','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('protected_area','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('peak','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('spring','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('mine_cave','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('glacier','nature');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('fire_station','emergency_health');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('police','emergency_health');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('doctor_dentist','emergency_health');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('hospital_clinic','emergency_health');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('veterinary','emergency_health');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('buddhist','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('christian','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('hindu','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('jewish','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('muslim','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('shinto','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('taoist','place_of_worship');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bar_pub','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('cafe','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('restaurant','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('fast_food','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('confectionery','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('drinking_water','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('veg_food','food_drink');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('department_store','shopping');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('pharmacy','shopping');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bakery','shopping');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('other','shopping');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('supermarket_convenience','shopping');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('sport_outdoor','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('golf','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('swimming','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('sport_centre','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('sport_pitch','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('stadium','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('skiing','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('clubs_dancing','sport_leisure');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('gas_station','car_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('rest_area','car_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('car_shop_and_repair','car_services');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bus_and_tram_stop','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('bus_station','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('railway_station','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('subway','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('airport','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('ferries','transportation');
INSERT INTO RootSubMapping (subname, rootname)  VALUES ('parking','transportation');
