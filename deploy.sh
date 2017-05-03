#!/bin/sh

FROMDIR="$PWD"
FOLDER="punkvision"
TMPDIR="/tmp/$FOLDER"

rm -rf $TMPDIR
mkdir -p $TMPDIR

cd $TMPDIR

mkdir -p $TMPDIR/src
mkdir -p $TMPDIR/configs

find $FROMDIR/src -name "*.py" -exec cp {} $TMPDIR/src \;
find $FROMDIR/configs -name "*.conf" -exec cp {} $TMPDIR/configs \;



cd $FROMDIR

rm *.tar*
echo "Tarring"


TARFILE="$FOLDER.tar.xz"

tar -C $TMPDIR/.. cfJ $TARFILE $FOLDER

exit

TARGET="$1"
SOURCES="$TARFILE"

if [ "$TARGET" = "" ]; then
    TARGET="pi@raspberrypi.local"
fi

HERECMD="scp -r $SOURCES $TARGET:~/Downloads ${2} ${3} ${4}"
EXECMD="tar xfv ~/$SOURCES"


echo "Running here: $HERECMD"
bash -c "$HERECMD" || echo "Failed on HOST"

echo "Running on raspi: $EXECMD"
ssh $TARGET "$EXECMD" || echo "Failed on TARGET"


