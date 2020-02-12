#!/bin/sh
TARGET=$1
[ "${TARGET}" == "suites" ] || [ "${TARGET}" == "daily" ] || exit 1

set -ex

PATH=~/bin:$PATH

export INSTALL_DIR=v$(date +%Y.%m.%d)
GS_FILENAME="dayofmonth_$(date +%d)"

while sleep 10; do { date +'DS: %H:%M:%S'; free -h; } >> log/mem_$(date +%d).log; done > /dev/null 2> /dev/null &

cd ~/taiwan-topo
git clean -fd
git checkout -- .
git pull --rebase
make clean-extracts

make ${TARGET}
make exps || echo make exps failed
make license

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
cd install/${INSTALL_DIR}
tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html

## rclone to dropbox
if [ "${TARGET}" == "suites" ]; then
    rclone copy --update . rudybox:Apps/share-mapdata/
    echo "Completed with weeekly drop."
else
    rclone copy --update . rudybox:Apps/share-mapdata/drops/
    echo "Completed with daily drop."
fi
