## QUICK-START

```bash
# cd to root or this repo
docker build docker/ -t rudymap:1.0
docker run \
    -it --rm \
    --user $(id -u):$(id -g) \
    -w /app \
    -v `pwd`:/app \
    -v /etc/passwd:/etc/passwd \
    -v /etc/group:/etc/group 
    rudymap:1.0 bash

# Inside container
make SUITE=taiwan mapsforge
```
