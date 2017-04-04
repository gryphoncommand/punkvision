#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
# make sure there is an '&' after each command so it doesn't stall

export PUNKVISION=/home/pi/punkvision

# Camera 0, and 1
/usr/bin/env python ${PUNKVISION}/src/punk.py --source /dev/video0 --stream 5802 --config ${PUNKVISION}/configs/test.conf &
#/usr/bin/env python ${PUNKVISION}/src/punk.py --source /dev/video1 --stream 5803 --config ${PUNKVISION}/configs/SMR-gearpeg.conf &

#Use this for serial connection to arduino UNO
#/usr/bin/env python ${PUNKVISION}/leds/interface.py --serial /dev/ttyACM0 &

#Use this for ethernet connection to arduino Ethernet
#/usr/bin/env python ${PUNKVISION}/leds/interface.py &

#Reads from lidar
#/usr/bin/env python ${PUNKVISION}/src/lidar.py --publish &

exit 0
