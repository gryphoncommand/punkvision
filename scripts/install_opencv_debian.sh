#!/bin/sh
# script to install opencv v3.4.0
#!/bin/bash
# code to build opencv on debian platforms (works on ubuntu, raspbian, etc)
# this will create a file called opencv-ARCH.tar.gz where ARCH is your architecture
# to install, run "sudo tar xfv opencv-ARCH.tar.gz -C /usr/local"


OPENCV_TAR="https://github.com/opencv/opencv/archive/3.4.0.tar.gz"

MAIN_DIR="$PWD"

if [ "$EUID" -ne "0" ]; then
    printf "ERROR: must be root\n"
    sudo $0 $@
    exit $?
fi

# dependencies to build
sudo apt -y install build-essential cmake pkg-config gfortran python3-dev

# image formats
sudo apt -y install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev 

# encoding formats
sudo apt -y install libavcodec-dev libavformat-dev libswscale-dev libxvidcore-dev libx264-dev 

# gtk and other random stuff
sudp apt -y install libgtk2.0-dev libgtk-3-dev libcanberra-gtk* 

# speed up stuff
sudo apt -y install libatlas-base-dev libv4l-dev v4l-utils
 
 
cd /tmp/
curl -L $OPENCV_TAR > opencv.tar.gz

tar xfv opencv.tar.gz
mv opencv-* opencv_code/

cd opencv_code
mkdir build; cd build


export CFLAGS="-mcpu=cortex-a7 -mfpu=neon-vfpv4 -ftree-vectorize -mfloat-abi=hard -fPIC -O3 $CFLAGS"
export CXXFLAGS="-mcpu=cortex-a7 -mfpu=neon-vfpv4 -ftree-vectorize -mfloat-abi=hard -fPIC -O3 $CXXFLAGS"

cmake .. -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local -DWITH_OPENMP=ON -DBUILD_EXAMPLES=OFF -D BUILD_DOCS=OFF -D BUILD_PERF_TESTS=OFF -D BUILD_TESTS=OFF -D WITH_CSTRIPES=OFF -DENABLE_NEON=ON -DEXTRA_C_FLAGS="$CFLAGS" -DEXTRA_CXX_FLAGS="$CXXFLAGS"

time make -j $(nproc)

sudo make install

echo "that was the time with $(nproc) jobs"
