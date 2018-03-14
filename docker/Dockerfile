FROM ubuntu:16.04
MAINTAINER Rudy Chung <rudyboy.tw@gmail.com>

ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    echo "dash dash/sh boolean false" | debconf-set-selections; dpkg-reconfigure -f noninteractive dash
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        p7zip-full \
        bash \
        bzip2 \
        curl \
        discount \
        default-jre \ 
        git \
        libc6:i386 libncurses5:i386 libstdc++6:i386 \
        make \
        nsis \
        osmctools \
        python-lxml \
        ssh \
        sudo \
        zip \
    && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos '' builder && adduser builder sudo

COPY rootfs/etc/sudoers /etc

USER builder
WORKDIR /home/builder

COPY rootfs/home/builder/bin /home/builder/
CMD ["/home/builder/bin/build.sh"]
