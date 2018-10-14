FROM ubuntu:18.04
MAINTAINER Rudy Chung <rudyboy.tw@gmail.com>

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
        git \
        libc6:i386 libncurses5:i386 libstdc++6:i386 \
        locales \
        make \
        nsis \
        osmctools \
        p7zip-full \
        python-lxml \
        python-pyosmium \
        ssh \
        sudo \
        tree \
        zip \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
RUN adduser --disabled-password --gecos '' builder && adduser builder sudo
ADD ./rootfs /
RUN chown -R builder:builder /home/builder

USER builder
WORKDIR /home/builder

CMD ["/bin/bash"]
