#!/bin/sh
set -ex

PATH=~/bin:$PATH

export INSTALL_DIR=v$(date +%Y.%m.%d)
GS_FILENAME="dayofmonth_$(date +%d)"
DAYOFWEEK="$(date +%w)"

while sleep 60; do free -h >> log/mem_$(date +%d).log; done > /dev/null 2> /dev/null &

cd ~/taiwan-topo
git clean -fdx
git pull --rebase
make distclean

make suites
make exps || echo make exps failed
make license

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
cd install/${INSTALL_DIR}
tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html

## rclone to dropbox
#rclone copy --update . rudybox:Public/drops/
rclone copy --update . rudybox:Apps/share-mapdata/drops/
[ "${DAYOFWEEK}" -eq 4 ] && {
    #rclone copy --update . rudybox:Public/maps/
    rclone copy --update . rudybox:Apps/share-mapdata/
    echo "Completed with weeekly drop."
} || echo "Completed without weekly drop."
  

### put to google bucket
#tar czf install/${GS_FILENAME}.tgz -C install ${INSTALL_DIR}
#gsutil cp install/${GS_FILENAME}.tgz gs://osm-twmap-drops/
