#!/bin/sh
set -ex

PATH=~/bin:$PATH

export INSTALL_DIR=v$(date +%Y.%m.%d)
GS_FILENAME="dayofmonth_$(date +%d)"
DAYOFWEEK="$(date +%w)"

cd ~/taiwan-topo

git clean -fdx
git pull --rebase

make distclean
make SUITE=taiwan all
make SUITE=taiwan_lite all
make SUITE=taiwan_bw all
make SUITE=taiwan_odc all
make SUITE=taiwan_bw_dem all
make SUITE=taiwan_odc_dem all
make license

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
cd install/${INSTALL_DIR}
tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html

## rclone to dropbox
rclone copy --update . rudybox:Public/drops/
[ "${DAYOFWEEK}" -eq 4 ] && {
    rclone copy --update . rudybox:Public/maps/
    mkdir -p share-mapdata
    cp -r MOI_OSM_* share-mapdata/
    rclone copy --update share-mapdata/ rudybox:Apps/share-mapdata/
    echo "Completed with weeekly drop."
} || echo "Completed without weekly drop."
  

### put to google bucket
#tar czf install/${GS_FILENAME}.tgz -C install ${INSTALL_DIR}
#gsutil cp install/${GS_FILENAME}.tgz gs://osm-twmap-drops/
