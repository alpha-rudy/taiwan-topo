#!/bin/sh
set -ex

PATH=~/bin:$PATH

export INSTALL_DIR=v$(date +%Y.%m.%d)
GS_FILENAME="dayofmonth_$(date +%d)"
DAYOFWEEK="$(date +%w)"
WEEKLY=4

while sleep 60; do free -h >> log/mem_$(date +%d).log; done > /dev/null 2> /dev/null &

cd ~/taiwan-topo
git clean -fdx
git pull --rebase
make distclean

if [ "${DAYOFWEEK}" -eq ${WEEKLY} ]; then
    make suites
else
    make daily
fi
make exps || echo make exps failed
make license

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
cd install/${INSTALL_DIR}
tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html

## rclone to dropbox
if [ "${DAYOFWEEK}" -eq ${WEEKLY} ]; then
    rclone copy --update . rudybox:Apps/share-mapdata/
    echo "Completed with weeekly drop."
else
    rclone copy --update . rudybox:Apps/share-mapdata/drops/
    echo "Completed with daily drop."
fi
