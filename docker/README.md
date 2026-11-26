## QUICK-START

```bash
# From the repository root, build the taiwan-topo:latest image with your UID/GID:
./tools/docker-build

# Run any make target directly via the wrapper script:
./tools/docker-make SUITE=taiwan mapsforge

# Or open an interactive shell inside the container:
docker run -it --rm \
    -v "$(pwd):/workspace" \
    -u builder \
    taiwan-topo:latest bash

# Inside container:
make SUITE=taiwan mapsforge
```

## Optional: a second copy on Cloudflare R2

`build.sh` uploads each drop to Dropbox (`rudybox:Apps/share-mapdata/`). When
the build machine's rclone config also has a remote named `rudyr2`, it copies
the same files to `rudyr2:share-mapdata/` (daily drops to
`rudyr2:share-mapdata/drops/`), the bucket behind data.rudymap.tw, so new
mirrors can sync from there instead of Dropbox. Without that remote nothing
changes; a failed R2 upload is reported in the log and does not fail the build.

Setup, once, on the machine whose rclone config holds `rudybox`. The access
key, secret, account ID and bucket name are sent privately; do not commit them.
Open the config file (`rclone config file` prints its path) and add:

```ini
[rudyr2-s3]
type = s3
provider = Cloudflare
access_key_id = <access key>
secret_access_key = <secret>
endpoint = https://<account id>.r2.cloudflarestorage.com
no_check_bucket = true

[rudyr2]
type = alias
remote = rudyr2-s3:<bucket>
```

The token may write this bucket but not create buckets, hence
`no_check_bucket`. Check it with a test file, then remove it:

```bash
echo test | rclone rcat rudyr2:share-mapdata/.write-test
rclone lsl rudyr2:share-mapdata/.write-test
rclone deletefile rudyr2:share-mapdata/.write-test
```
