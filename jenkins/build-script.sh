set -ex
build=NG
instance=ttb-hd

## start Google GCE for taiwan topo building
gcloud compute instances start ${instance} && sleep 30

for i in {1..5}; do 
  gcloud compute ssh --command="~/bin/build.sh" rudychung@${instance} && build=OK && break
  
  ## failed, let's retry
  gcloud compute instances stop ${instance}
  sleep $((i*1200))
  gcloud compute instances start ${instance} && sleep 30
done || echo "Failed after retry 5 times."

gcloud compute instances stop ${instance}


## Deploy to Dropbox
[ "${build}" = "OK" ] && echo "Build Done" || echo "Build Failed"
