#!/bin/sh

# ubuntu based script


if [ "$UID" -ne "0" ]; then
    printf "ERROR: must be root\n"
    sudo $0
    exit $?
fi

apt-get -y install python3-pip build-essential cmake pkg-config
pip3 install pynetworktables numpy

cd /tmp/
rm -rf opencv-3.4.0
curl -L https://github.com/opencv/opencv/archive/3.4.0.tar.gz > opencv.tar.gz
tar xfv opencv.tar.gz
apt-get -y install python3.5-dev
apt-get -y install build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev

mkdir build; cd build

cmake .. -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local

make -j8

make install


#apt-get -y install libjpeg8-dev libpng12-dev libatlas-base-dev libv4l-dev v4l-utils

#pip3 install pynetworktables opencv-python numpy
