#!/bin/sh
set -ex

export INSTALL_DIR=v$(date +%Y.%m.%d)

cd ~/taiwan-topo

git pull --rebase

make distclean
make SUITE=taiwan_bw all
make SUITE=taiwan_odc all
make SUITE=taiwan all

rm -rf install/${INSTALL_DIR}
mkdir -p install/${INSTALL_DIR}
make INSTALL_DIR=install/${INSTALL_DIR} drop
tar czf install/${INSTALL_DIR}.tgz -C install ${INSTALL_DIR}

gsutil cp install/${INSTALL_DIR}.tgz gs://taiwan-topo-drops/
