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

if [ "$OS" != "debian" ]; then
  echo "This is not a raspberry PI."
  uname -a
  exit 2
fi

echo "#!/bin/sh -e" > /etc/rc.local
find $PWD/scripts -name "auto_*.sh" -exec echo {}" &" >> /etc/rc.local \;
echo "exit 0" >> /etc/rc.local

chmod +x /etc/rc.local

./scripts/network_update.sh

exit 0
