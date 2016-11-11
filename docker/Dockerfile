FROM ubuntu:16.04
MAINTAINER Rudy Chung <rudyboy.tw@gmail.com>

ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    echo "dash dash/sh boolean false" | debconf-set-selections; dpkg-reconfigure -f noninteractive dash
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        bash \
        curl \
        discount \
        default-jre \ 
        git \
        libc6:i386 libncurses5:i386 libstdc++6:i386 \
        make \
        nsis \
        zip \
    && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos '' builder

USER builder
WORKDIR /home/builder

CMD ["bash"]
