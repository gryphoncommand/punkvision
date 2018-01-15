#!/bin/sh
# script to install opencv v3.4.0

apt-get -y install python3.5-dev
apt-get -y install build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev

cd /tmp/
rm -rf opencv-3.4.0
curl -L https://github.com/opencv/opencv/archive/3.4.0.tar.gz > opencv.tar.gz
tar xfv opencv.tar.gz

cd opencv-3.4.0

mkdir build; cd build

cmake .. -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local 
 
make -j8

make install



