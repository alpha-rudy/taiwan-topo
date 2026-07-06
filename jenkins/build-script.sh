#!/bin/bash
set -ex
build=NG
instance=ttb-hd
TARGET="${1:-daily}"

## start Google GCE for taiwan topo building
gcloud compute instances start ${instance} && sleep 30

for i in {1..5}; do
  # VM-side script requires TARGET argument (daily / *suites* / world)
  gcloud compute ssh --command="~/bin/build.sh ${TARGET}" rudychung@${instance} && build=OK && break

  ## failed, let's retry
  gcloud compute instances stop ${instance}
  sleep $((i*1200))
  gcloud compute instances start ${instance} && sleep 30
done

gcloud compute instances stop ${instance}

if [ "${build}" = "OK" ]; then
    echo "Build Done"
else
    echo "Build Failed after 5 attempts."
    exit 1
fi
