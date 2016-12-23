#!/bin/sh
set -ex

export INSTALL_DIR=v$(date +%Y.%m.%d)
GS_FILENAME="dayofmonth_$(date +%d)"

cd ~/taiwan-topo

git pull --rebase

make distclean
make SUITE=taiwan_bw all
make SUITE=taiwan_odc all
make SUITE=taiwan all

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
tar czf install/${GS_FILENAME}.tgz -C install ${INSTALL_DIR}

gsutil cp install/${GS_FILENAME}.tgz gs://taiwan-topo-drops/
