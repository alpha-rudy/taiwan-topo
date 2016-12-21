build=NG

## start Google GCE for taiwan topo building
gcloud compute instances start taiwan-topo-builder
for i in 1 2 3; do 
  gcloud compute ssh --command="~/bin/build.sh" rudychung@taiwan-topo-builder && build=OK && break
  
  ## failed, let's retry
  gcloud compute instances stop taiwan-topo-builder
  sleep $((i*60))
  gcloud compute instances start taiwan-topo-builder
done || echo "Failed after retry 10 times."

gcloud compute instances stop taiwan-topo-builder


## Deploy to Dropbox
[ "${build}" = "OK" ] || exit 1

VERSION=$(date +%Y.%m.%d)

gsutil cp gs://osm-twmap-drops/v${VERSION}.tgz .
tar xzf v${VERSION}.tgz 
cp -r v${VERSION}/* /var/shared/Dropbox/Public/drops/  ### daily drops

[ "$(date +%w)" -eq 4 ] && {  ### weekly drops
  cp -r v${VERSION}/* /var/shared/Dropbox/Public/maps/
  cp -r v${VERSION}/MOI_OSM_Taiwan_TOPO_Rudy* /var/shared/Dropbox/Apps/share-mapdata/
  echo "Completed with weeekly drop."
}  || echo "Completed without weekly drop."
