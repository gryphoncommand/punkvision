#!/bin/sh
# auto_nothing.sh

# test autostarting script

export PYTHONPATH=$PYTHONPATH:/home/pi/projects/vpl

# you normally keep this


echo started at $(date +"%T") > /home/pi/punkvision.log


# example of what to put
/usr/bin/env python3 /home/pi/projects/punkvision/src/punk.py --source 0 --size 320 240 --stream 5802 --printinfo 2>&1 >> /home/pi/punkvision.log &

MY_PID=$!

echo "PID is $MY_PID" >> /home/pi/punkvision.log


exit 0

