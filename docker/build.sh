#!/bin/bash

set -ex

TARGET=$1
[[ "${TARGET}" == *"suites"* ]] || [ "${TARGET}" == "daily" ] || [ "${TARGET}" == "world" ] || exit 1

export PATH=~/bin:$PATH
export JAVA8_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre
export RCLONE_OPTS="--checksum --transfers 1 --checkers 1 --tpslimit 12 --low-level-retries 10"

date > log/mem_$(date +%d).log
while sleep 10; do { date +'DS: %H:%M:%S'; free -h; df -h /; } >> log/mem_$(date +%d).log; done > /dev/null 2> /dev/null &
# background logging is fine, as build machine would be shutdown after building

cd ~/taiwan-topo
make distclean-extracts
git clean -fd
git checkout master -- .
git pull --rebase

INSTALL_DIR=install/v$(date +%Y.%m.%d)
rm -rf ${INSTALL_DIR}
mkdir -p ${INSTALL_DIR}

if [[ "${TARGET}" == *"suites"* ]]; then
    make INSTALL_DIR=/workspace/${INSTALL_DIR} ${TARGET}
    make exps || echo make exps failed
    cd ${INSTALL_DIR}
    tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html
    rclone copy ${RCLONE_OPTS} . rudybox:Apps/share-mapdata/
    echo "Completed with weekly drop."
elif [ "${TARGET}" == "daily" ]; then
    make INSTALL_DIR=/workspace/${INSTALL_DIR} ${TARGET}
    make exps || echo make exps failed
    cd ${INSTALL_DIR}
    tree -L 1 -H . | sed -e 's,<br>.*href="\./.*/".*</a>.*<br>,<br>,' -e 's,<a .*href="\.".*>\.</a>,,' > files.html
    rclone copy ${RCLONE_OPTS} . rudybox:Apps/share-mapdata/drops/
    echo "Completed with daily drop."
elif [ "${TARGET}" == "world" ]; then
    for i in annapurna alps_core alps_western alps_eastern alps_fareast elbrus fujisan kashmir kumano nikko_oze; do
    	make ${i}_suites
        cd install-${i}
        rclone copy ${RCLONE_OPTS} . rudybox:Apps/share-mapdata/
	cd ..
    done
    echo "Completed with weekly world drop."
fi
