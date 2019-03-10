# GPX Overlay

## OSM tagging

### Tag:gpx=trk 

⽤來標⽰航跡，只用於 OSM way

Useful combination:

	* name=*: 名稱, ex: 雪山主東線

	* zl=1/2: 顯示相關，用來提示高低 zoom level (尚未支援)
		* z1=1: 長天數 track zoom level 10 ~ max
		* zl=2: 短天數 track zoom level 13 ~ max (default) 

	* color=*: 航跡顏色 (尚未支援)
		Garmin display colors, ex: DarkBlue
		參考: http://www.tic2.org/Ignacio/GPS/Practica/UsoAvanzado/Varios/GpxExtensionsv3.htm#h421429051


### Tag:gpx=wpt 

用來標示航點，只用於 OSM node

Useful combination:

	* name=*: 名稱, ex: ⽟玉⼭山

	* ele=*: 海拔, 單位公尺, ex: 3930.24 

	* sym=*: Garmin Waypoint Symbol, ex: Summit (山頭)
	  參考: https://freegeographytools.com/2008/garmin-gps-unit-waypoint-icons-table
	  參考: https://www.gpsbabel.org/htmldoc-development/GarminIcons.html


### Tag:gpx=rte (暫不支援) 

用來標⽰航線，只⽤於 OSM way 

Useful combination:

	* name=*

	* zl=1/2
		* z1=1: 長天數 track zoom level 10 ~ max 
		* zl=2: 短天數 track zoom level 13 ~ max


## 製作範例

假設你有 track.pbf 來放航跡，waypoint.pbf 來放航點

1. 透過 osm_scrpts/gpx_handle.py 來作前製處理。

        $ python3 osm_scripts/gpx_handler.py track.pbf track-sed.pbf
        $ python3 osm_scripts/gpx_handler.py waypoint.pbf waypoint-sed.pbf

2. 作一次重編號，並透過 osm_scripts/osium-append.sh 結合兩個檔案。

        $ osmium renumber \
            -s 1,1,0 \
            $(BUILD_DIR)/track-sed.pbf \
            -Oo Happyman.pbf
        $ osm_scripts/osium-append.sh Happyman.pbf $(BUILD_DIR)/waypoint-sed.pbf

3. 透過 osm_scripts/gpx-mapping.xml 轉成 mapsforge 圖資檔
            
        $ export JAVACMD_OPTIONS="-Xmx30G -server" && \
        sh ./osmosis/bin/osmosis \
            --read-pbf Happyman.pbf \
            --buffer --mapfile-writer \
            type=ram \
            threads=8 \
            bbox=21.55682,118.12141,26.44212,122.31377 \
            preferred-languages="zh,en" \
            tag-conf-file=osm_scripts/gpx-mapping.xml \
            polygon-clipping=true way-clipping=true label-position=true \
            zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
            map-start-zoom=12 \
            comment="$(VERSION) / (c) Map: Happyman" \
            file="Happyman.map"

大功告成！