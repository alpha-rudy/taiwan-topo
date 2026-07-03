# tilemaker (PMTiles tile generator)

The PMTiles build target (`make SUITE=<region> pmtiles`) runs tilemaker.

## In the Docker build (default)

`./tools/docker-make ... pmtiles` already works out of the box: the
`taiwan-topo` image builds tilemaker v3.1.0 from source (see `docker/Dockerfile`)
and installs it to `/usr/local/bin/tilemaker`. `TILEMAKER_CMD` defaults to that
PATH binary when no vendored copy exists. Nothing else to do.

## Outside Docker

If you run `make` directly (no container), provide a tilemaker binary either at
`tools/tilemaker/tilemaker` or on `PATH`. Use **v3.0.0 or newer** — those write
`.pmtiles` directly via `--output x.pmtiles`. Older versions only emit
`.mbtiles` and would need a separate `pmtiles convert` step.

## Notes on the input data (already handled by tools/pmtiles-build.sh)

The prepared `$(MAPSFORGE_PBF)` needs two adaptations, both done automatically
by the build wrapper:
  - it is **sorted** with `osmium sort` (tilemaker streams nodes in type+id order);
  - tilemaker is run with **`--skip-integrity`** because the PBF carries a few
    dangling node references (the upstream osmosis step keeps incomplete
    entities). osmconvert `--drop-broken-refs` is *not* usable here — it drops
    every way on this data.

Also note the config (`osm_scripts/pmtiles/config.json`) must set top-level
`name`/`version`/`description` in `settings`: tilemaker reads them without a
null check and segfaults if any is missing. `version` uses the `__version__`
placeholder, substituted with the build version by the wrapper.

## Option A — build from source (Linux)

    sudo apt-get install -y build-essential cmake \
        libboost-program-options-dev libboost-filesystem-dev \
        libboost-system-dev libboost-iostreams-dev \
        libprotobuf-dev protobuf-compiler \
        libshp-dev libsqlite3-dev rapidjson-dev liblua5.1-0-dev

    git clone https://github.com/systemed/tilemaker
    cd tilemaker
    git checkout v3.1.0
    cmake -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build -j"$(nproc)"

    # then place/symlink the binary where the Makefile expects it:
    ln -sf "$(pwd)/build/tilemaker" /path/to/taiwan-topo/tools/tilemaker/tilemaker

## Option B — point the Makefile at an existing install

If tilemaker is already on `PATH`, override the variable per-invocation:

    make SUITE=taiwan pmtiles TILEMAKER_CMD=tilemaker

## Verifying the output

The build writes `build-<region>/<NAME_MAPSFORGE>.pmtiles`. Inspect it with the
PMTiles CLI (https://github.com/protomaps/go-pmtiles):

    pmtiles show build-taiwan/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles

Render it with `styles/pmtiles_style/style.json` in any MapLibre GL viewer
(update the `sources.topo.url` to point at your archive), or drop the raw
`.pmtiles` onto https://pmtiles.io to preview layers.

## Schema

The vector-tile schema (layers, zoom ranges) is defined by:

  - `osm_scripts/pmtiles/config.json`  — layer list + tile settings
  - `osm_scripts/pmtiles/process.lua`  — OSM tag → layer/attribute mapping

It mirrors the Mapsforge tag mapping in `osm_scripts/tag-mapping.xml`, clamped
to PMTiles maxzoom 14.
