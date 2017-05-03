#!/bin/sh
# installs on raspberrypi


#if [ "$UID" -ne "0" ]; then
#    printf "ERROR: must be root\n"
#    sudo $0
#    exit $?
#fi

echo "This might take a while..."

if [ "$PLATFORM" = "" ]; then
  UNAMESTR=$(uname -s)

  case "$UNAMESTR" in
    "Linux") PLATFORM="linux";;
    "Darwin") PLATFORM="mac";;
    *"BSD") PLATFORM="bsd";;
    *) PLATFORM="build";;
  esac
fi

OS="$PLATFORM"

if [ "$PLATFORM" = "linux" ]; then
  if [ "$(cat /etc/debian_version)" != "" ]; then
    OS="debian"
  elif [ "$(cat /etc/fedora-release)" != "" ]; then
    OS="fedora"
  fi
fi

if [ "x$PLATFORM" != "xdebian" ]; then
  echo "This is not a raspberry PI."
  uname -a
  exit 2
fi

sudo apt-get -y update

sudo apt-get -y install python-pip build-essential cmake pkg-config

sudo apt-get -y install libjpeg8-dev libpng12-dev libatlas-base-dev libv4l-dev libopencv-dev python-opencv

pip install pynetworktables
pip install numpy
