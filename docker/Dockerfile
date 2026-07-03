FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set locale to UTF-8
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN sed -i 's/archive.ubuntu.com/free.nchc.org.tw/g' /etc/apt/sources.list
RUN apt-get update

ENV TZ=Asia/Taipei
RUN echo $TZ > /etc/timezone && apt-get install -y --no-install-recommends tzdata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
RUN echo "dash dash/sh boolean false" | debconf-set-selections; dpkg-reconfigure -f noninteractive dash

RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        aria2 \
        bash \
        bzip2 \
        curl \
        default-jre \
        discount \
        gdal-bin \
        git \
        libc6:i386 libncurses6:i386 libstdc++6:i386 \
        libsqlite3-mod-spatialite \
        locales \
        make \
        nsis \
        openjdk-8-jre \
        osmctools \
        osmium-tool \
        p7zip-full \
        python3-lxml \
        python3-pip \
        python3-rasterio \
        pyosmium \
        ssh \
        sudo \
        tree \
        unzip \
        zip \
        zstd \
    && rm -rf /var/lib/apt/lists/*

# numpy is intentionally NOT upgraded here: python3-rasterio (apt) provides
# Debian's numpy 1.26.4, which pip may not uninstall ("installed by debian").
# That version already satisfies matplotlib, so let apt own numpy.
RUN pip3 install --break-system-packages --upgrade "setuptools<82" bs4 matplotlib
RUN pip3 install --no-cache-dir --break-system-packages \
                    cyrtranslit \
                    hanzi2reading \
                    indic-transliteration \
                    janome \
                    nepali_roman \
                    opencc-python-reimplemented \
                    osmium \
                    pyewts \
                    pykakasi \
                    requests \
                    rio-rgbify \
                    spatialite \
                    tqdm \
                    unidecode \
                    wheel

# Build tilemaker (PMTiles vector-tile generator) from source.
# Ubuntu does not package it; v3+ writes .pmtiles directly. The build deps also
# provide the shared libs tilemaker needs at runtime, so they are kept.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake \
        libboost-program-options-dev libboost-filesystem-dev \
        libboost-system-dev libboost-iostreams-dev \
        libprotobuf-dev protobuf-compiler \
        libshp-dev libsqlite3-dev rapidjson-dev liblua5.1-0-dev \
        zlib1g-dev \
    && git clone --depth 1 -b v3.1.0 https://github.com/systemed/tilemaker /tmp/tilemaker \
    && cmake -S /tmp/tilemaker -B /tmp/tilemaker/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /tmp/tilemaker/build -j"$(nproc)" \
    && cmake --install /tmp/tilemaker/build \
    && rm -rf /tmp/tilemaker /var/lib/apt/lists/* \
    && tilemaker --help >/dev/null

ARG USER_ID=1000
ARG GROUP_ID=1000

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV JAVA8_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN locale-gen en_US.UTF-8
RUN set -e && \
    # Create or modify group
    if getent group ${GROUP_ID} >/dev/null; then \
        GROUP_NAME=$(getent group ${GROUP_ID} | cut -d: -f1); \
    else \
        groupadd -g ${GROUP_ID} builder; \
        GROUP_NAME=builder; \
    fi && \
    # Create user with the group
    if id -u ${USER_ID} >/dev/null 2>&1; then \
        USER_NAME=$(id -un ${USER_ID}); \
        usermod -l builder -d /home/builder -m ${USER_NAME} 2>/dev/null || true; \
    else \
        useradd -m -s /bin/bash -u ${USER_ID} -g ${GROUP_ID} builder; \
    fi && \
    # Set password and sudo permissions
    echo "builder:builder" | chpasswd && \
    usermod -aG sudo builder && \
    echo "builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN mkdir -p /home/builder/bin
COPY --chown=builder:builder build.sh /home/builder/bin/build.sh
RUN chmod +x /home/builder/bin/build.sh

USER builder
WORKDIR /workspace
SHELL ["/bin/bash", "-c"]
CMD ["/bin/bash"]
