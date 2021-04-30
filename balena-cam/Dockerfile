FROM balenalib/intel-nuc-debian:latest

RUN apt-get update && apt install wget

# Install dependencies
RUN apt-get install -yq \
    build-essential \
    autoconf \
    libtool \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    gstreamer-1.0 \
    libffi-dev \
    v4l-utils \
    libopus-dev \
    libvpx-dev \
    libsrtp2-dev \
    libopencv-dev \
    libatlas3-base \
    libatlas-base-dev \
    libilmbase-dev \
    libopenexr-dev \
    libavformat-dev \
    libswscale-dev \
    libqtgui4 \
    libqt4-test \
    libavdevice-dev \
    libavfilter-dev \
    libavcodec-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Enable the v4l2 driver for the Raspberry Pi camera
RUN printf "bcm2835-v4l2\n" >> /etc/modules
RUN pip3 install --upgrade pip wheel 

WORKDIR /usr/src/app

COPY ./app/ /usr/src/app/
RUN pip3 install -r requirements.txt
CMD ["python3", "/usr/src/app/server.py"]
