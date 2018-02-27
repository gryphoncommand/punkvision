#!/bin/sh
# auto_nothing.sh

# test autostarting script

VPL_PATH="/home/pi/projects/vpl"
PUNKVISION_PATH="/home/pi/projects/punkvision"
LOG_FILE="/home/pi/punkvision.log"
CAM_ID="0"



export PYTHONPATH=$PYTHONPATH:$VPL_PATH

# you normally keep this


echo started at $(date +"%T") > $LOG_FILE


wait_file() {
  local file="$1"; shift
  local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout

  until test $((wait_seconds--)) -eq 0 -o -f "$file" ; do sleep 1; done

  ((++wait_seconds))
}


wait_file "/dev/video$CAM_ID" 15 || {
    echo "failed to load camera file (/dev/video$CAM_ID) within 15 seconds" >> $LOG_FILE
    exit 0
}

$VPL_PATH/utils/reset_lifecam.sh "/dev/video$CAM_ID"

# example of what to put
/usr/bin/env python3 $PUNKVISION_PATH/src/punk.py --source $CAM_ID --size 320 240 --stream 5802 --printinfo 2>&1 >> $LOG_FILE &

MY_PID=$!

echo "PID is $MY_PID" >> $LOG_FILE

exit 0

