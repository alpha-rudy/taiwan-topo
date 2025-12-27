#!/bin/bash

TARGET=$1
[[ "${TARGET}" == *"suites"* ]] || [ "${TARGET}" == "daily" ] || exit 1

set -ex

export PATH=~/bin:$PATH
export JAVA8_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre

date > log/mem_$(date +%d).log
while sleep 10; do { date +'DS: %H:%M:%S'; free -h; df -h /; } >> log/mem_$(date +%d).log; done > /dev/null 2> /dev/null &
# background logging is fine, as build machine would be shutdown after building

cd ~/taiwan-topo
make distclean-extracts
git clean -fd
git checkout -- .
git pull --rebase

INSTALL_DIR=$PWD/install/v$(date +%Y.%m.%d)
rm -rf ${INSTALL_DIR}
mkdir -p ${INSTALL_DIR}

make INSTALL_DIR=${INSTALL_DIR} ${TARGET}
make exps || echo make exps failed

## rclone to dropbox
cd ${INSTALL_DIR}
tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html
if [[ "${TARGET}" == *"suites" ]]; then
    rclone copy --update . rudybox:Apps/share-mapdata/
    echo "Completed with weeekly drop."
elif [ "${TARGET}" == "daily" ]; then
    rclone copy --update . rudybox:Apps/share-mapdata/drops/
    echo "Completed with daily drop."
fi
