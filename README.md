# *Taiwan TOPO* Taiwan Hiking/Geocaching Maps

## 給 App 開發者 / For app developers

魯地圖歡迎 App 使用，免費或收費、有沒有廣告都可以，只要遵守以下幾點：

1. **不透過下載魯地圖收費。** 地圖檔、DEM 與樣式（theme）都可以讓使用者在 App 內直接下載，但不能對下載本身收費。
2. **標明出處。** 在 App 中標示魯地圖，並附上說明網頁 https://rudymap.tw 。
3. **下載一律連 https://rudymap.tw 。** 不要直接連鏡像站；rudymap.tw 會依各站狀況分流。
4. **User-Agent 帶上 App 名稱。** 格式是 `AppName/版本 (+聯絡網址)`，例如 `MyHikingApp/2.1.0 (+https://example.com/contact)`。查詢更新與實際下載的請求都要帶。查有沒有新版用 HEAD，每個檔案只 GET 一次，續傳直接連轉址後的鏡像站網址。細節見 https://oslab.tw/rudymap/developers 。

其他問題請開 issue。

Apps are welcome to use Rudy Map, free or paid, with or without ads, as long as they:

1. **Do not charge for downloading Rudy Map.** Users may download the maps, DEM and themes from inside the app, but the download itself must not be sold.
2. **Credit Rudy Map** in the app, with a link to https://rudymap.tw .
3. **Download through https://rudymap.tw**, never from a mirror directly; rudymap.tw spreads downloads across the mirrors.
4. **Name the app in the User-Agent**, as `AppName/version (+contact URL)`, e.g. `MyHikingApp/2.1.0 (+https://example.com/contact)`, on both update checks and downloads. Check for updates with HEAD, GET each file once, and resume against the mirror URL you were redirected to. Details: https://oslab.tw/rudymap/developers .

For anything else, please open an issue.

## Usage

    $ make SUITE=taiwan_bw gmapsupp   ### make a Garmin handheld map
    
    $ make SUITE=taiwan mapsforge   ### make a mapsforge map
    
    $ make SUITE=bbox REGION=陽明山 \
        TOP=25.24917 BOTTOM=25.11332 \
        LEFT=121.48012 RIGHT=121.63218 \ 
        mapsforge

    $ make SUITE=bbox REGION=kumano_kodo \
        DEM_NAME=AW3D30 LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        ELEVATION_MIX_FILE=ele_kumano_kodo_10_100_500_mix.pbf \
        EXTRACT_FILE=japan-latest \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        mapsforge_zip poi_v2

    $ make SUITE=bbox_bc_dem REGION=kumano \
        DEM_NAME=AW3D LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        EXTRACT_FILE=japan-latest \
        GMAPDEM=/home/rudychung/Works/taiwan-topo/hgt/kumano_hgtmix.zip \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        gmap nsis

    $ make SUITE=bbox_odc_dem REGION=kumano \
        DEM_NAME=AW3D LANG=ja CODE_PAGE=65001 \
        ELEVATION_FILE=ele_kumano_kodo_10_100_500.pbf \
        EXTRACT_FILE=japan-latest \
        GMAPDEM=/home/rudychung/Works/taiwan-topo/hgt/kumano_hgtmix.zip \
        TOP=35.0 BOTTOM=33.0 \
        LEFT=135.0 RIGHT=137.0 \
        gmapsupp_zip

## Docker Usage

Build with your user ID to avoid permission issues:

```bash
docker build \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) \
  -t taiwan-topo:latest .
```

Running Make Commands Directly:
    
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -u builder \
  taiwan-topo:latest \
  make SUITE=taiwan mapsforge
```

Using a Wrapper Script:

```bash
./tools/docker-make SUITE=taiwan mapsforge
```

## SUITE list

* Garmin GMAP Maps
  * `taiwan_bw`: Taiwan region, bw style
  * `taiwan_odc`: Taiwan region, odc style
  * `bbox_bw`: Bonding Box, bw style (TOP/BOTTOM/LEFT/RIGHT)
  * `bbox_odc`: Bonding Box, odc style (TOP/BOTTOM/LEFT/RIGHT)
* Mapsforge Maps
  * `taiwan`: Taiwan
  * `bbox`: Bonding Box with coords (TOP/BOTTOM/LEFT/RIGHT)

## target list

* `all`
  * for Garmin GMAP, it is `gmap`, `gmapsupp`, `nsis`
  * for Mapsforge, it is `mapsforge`, `mapsforge_style`
* `distclean`
  * clean every thing, include downloaded maps
* `clean`
  * clean compilation stuff
* `install`
  * develping use, copy GMAP .img file to $INSTALL_DIR
* `drop`
  * daily build use, copy `all` targets to $INSTALL_DIR
* `gmap`
  * macOS installer
* `gmapsupp`
  * Garmin handheld gmapsupp.img
* `nsis`
  * Windows installer
* `mapsforge`
  * Mapsforge map
* `mapsforge_style`
  * Mapsforge style

