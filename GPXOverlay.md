# GPX Overlay

## Tag:gpx=trk 

⽤來標⽰航跡，只用於 OSM way

### Useful combination 

	* name=*: 名稱, ex: 雪山主東線

	* zl=1/2: 顯示相關，用來提示高低 zoom level (尚未支援)
		* z1=1: 長天數 track zoom level 10 ~ max
		* zl=2: 短天數 track zoom level 13 ~ max (default) 

	* color=*: 航跡顏色 (尚未支援)
		Garmin display colors, ex: DarkBlue
		參考: http://www.tic2.org/Ignacio/GPS/Practica/UsoAvanzado/Varios/GpxExtensionsv3.htm#h421429051


## Tag:gpx=wpt 

用來標示航點，只用於 OSM node

### Useful combination

	* name=*: 名稱, ex: ⽟玉⼭山

	* ele=*: 海拔, 單位公尺, ex: 3930.24 

	* sym=*: Garmin Waypoint Symbol, ex: Summit (山頭)
	  參考: https://freegeographytools.com/2008/garmin-gps-unit-waypoint-icons-table
	  參考: https://www.gpsbabel.org/htmldoc-development/GarminIcons.html


## Tag:gpx=rte (暫不⽀支援) 

用來標⽰航線，只⽤於 OSM way 

### Useful combination 

	* name=*

	* zl=1/2
		* z1=1: 長天數 track zoom level 10 ~ max 
		* zl=2: 短天數 track zoom level 13 ~ max
