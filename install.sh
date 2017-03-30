#!/bin/bash

#if [ "$UID" -ne "0" ]; then
#    printf "ERROR: must be root\n"
#    sudo $0
#    exit $?
#fi

MACOSWHEEL="https://pypi.python.org/packages/16/24/4c0e3d4fc0bde3d7803e6b8f8748f749f569364aa44a891fc4c71ff22b85/opencv_python-3.2.0.6-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
TOWHEEL="opencv_python-3.2.0.6-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
GETPIP="https://bootstrap.pypa.io/get-pip.py"


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
  if [ "$(cat /etc/debian-release)" != "" ]; then
    OS="debian"
  elif [ "$(cat /etc/fedora-release)" != "" ]; then
    OS="fedora"
  fi
fi

test_module () {
  python -c "import $1" > /dev/null 2>&1
  rc=$?
  if [[ $rc != 0 ]]; then
    if [ "$2" = "ensurepip" ]; then
      curl $GETPIP -L > ./get-pip.py
      python ./get-pip.py
      exit $?
    elif [ "$2" != "" ]; then
      echo "installing pip module $2"
      pip install --upgrade --user $2;
    fi
    echo "pip module $1 not found"
  fi
}

test_module ensurepip

if [ "$OS" = "debian" ]; then
  apt install libopencv-dev python-opencv v4l-utils
elif [ "$OS" = "fedora" ]; then
  echo "fedora not tested"
  yum install python-pip
  yum install numpy opencv*
elif [ "$OS" = "mac" ]; then
  echo "NO GUI SUPPORT for macOS yet"
  test_module cv2 opencv-python
elif [ "$OS" = "bsd" ]; then
  echo "BSD? just compile it yourself; I can't help you"
else
  echo "$OS not supported"
fi

test_module networktables pynetworktables
test_module numpy numpy


