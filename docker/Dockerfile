FROM ubuntu:26.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set locale to UTF-8
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Since 24.04 apt sources live in deb822 format; /etc/apt/sources.list is empty.
RUN sed -i 's,archive.ubuntu.com,free.nchc.org.tw,g' /etc/apt/sources.list.d/ubuntu.sources
RUN apt-get update

ENV TZ=Asia/Taipei
RUN echo $TZ > /etc/timezone && apt-get install -y --no-install-recommends tzdata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# i386 libs: tools/jmc*/linux/jmc_cli is a 32-bit binary.
# openjdk-8 is only for the POI v2 osmosis (JAVA8_HOME); the rest use default-java.
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        7zip \
        aria2 \
        bash \
        bzip2 \
        curl \
        default-jre-headless \
        discount \
        gdal-bin \
        git \
        libc6:i386 libncurses6:i386 libstdc++6:i386 \
        libsqlite3-mod-spatialite \
        locales \
        make \
        nsis \
        openjdk-8-jre-headless \
        osmctools \
        osmium-tool \
        python3-gdal \
        python3-lxml \
        python3-pip \
        python3-rasterio \
        python3-requests \
        python3-tqdm \
        python3-unidecode \
        pyosmium \
        ssh \
        sudo \
        tilemaker \
        tree \
        unzip \
        zip \
        zstd \
    && rm -rf /var/lib/apt/lists/*

# Python packages: apt owns the compiled stack (numpy, GDAL, rasterio, lxml,
# osmium), pip only adds the pinned pure-Python packages in requirements.txt.
# pip cannot uninstall apt packages ("installed by debian"), and the apt
# bindings are built against Debian's numpy ABI, so pip must never replace
# them. Pin every apt-owned distribution as a constraint (except the packaging
# tools) so a pip dependency asking for another numpy/rasterio/... fails with a
# clear resolver error or picks an older compatible release.
RUN python3 -c 'import importlib.metadata as m; \
        [print(f"{d.name}=={d.version}") for d in m.distributions() \
         if str(d.locate_file("")).startswith("/usr/lib/python3/dist-packages") \
         and d.name.lower() not in ("pip", "setuptools", "wheel")]' \
        | sort -f > /etc/pip-constraints.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages \
        -c /etc/pip-constraints.txt -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt
# Guard ad-hoc `pip install` inside the container too.
ENV PIP_CONSTRAINT=/etc/pip-constraints.txt

ARG USER_ID=1000
ARG GROUP_ID=1000

# default-java follows default-jre (OpenJDK 25 on 26.04).
ENV JAVA_HOME=/usr/lib/jvm/default-java
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
