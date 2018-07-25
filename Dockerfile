FROM cravattlab/cimage_base:old

MAINTAINER Radu Suciu <radusuciu@gmail.com>

# Create user with non-root privileges
RUN adduser --disabled-password --gecos '' ctesi
RUN chown -R ctesi /home/ctesi

# install some deps
RUN apt-get update && apt-get -y install \
    python3-pip \
    python3-venv \
    cifs-utils \
    git \
    imagemagick

RUN pip3 install wheel

# Setup cimage
RUN ln -s /home/ctesi/cimage-minimal/cimage2 /usr/local/bin
RUN ln -s /home/ctesi/cimage-minimal/cimage_combine /usr/local/bin
ENV CIMAGE_PATH /home/ctesi/cimage-minimal

RUN mkdir -p /data/tmp
RUN chown ctesi:ctesi -R /data

USER ctesi
WORKDIR /home/ctesi/ctesi
CMD [ "/bin/bash", "/home/ctesi/ctesi/start.sh" ]
