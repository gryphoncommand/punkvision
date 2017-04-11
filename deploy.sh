#!/bin/sh

FROMDIR="$PWD"
FOLDER="punkvision"
TMPDIR="/tmp/$FOLDER"

rm -rf $TMPDIR
mkdir -p $TMPDIR

cd $TMPDIR

echo $TMPDIR
cp -R $FROMDIR/* ./
echo $TMPDIR

rm -rf .git

find . -name "*.jpg" -delete
find . -name "*.png" -delete

rm *.tar*

cd ..

echo "Tarring"
tar cfJ $FOLDER.tar.xz $FOLDER

cd $FROMDIR

cp $TMPDIR/../$FOLDER.tar.xz $FOLDER.tar.xz

TAR="$FOLDER.tar.xz"

TARGET="$1"
#SOURCES=./src/
SOURCES="$FOLDER.tar.xz"

if [ "$TARGET" = "" ]; then
    TARGET="pi@raspberrypi.local"
fi
HERECMD="scp -r $SOURCES $TARGET:~/ ${2} ${3} ${4}"
EXECMD="tar xfv ~/$SOURCES"

echo "Running here: $HERECMD"
bash -c "$HERECMD" || echo "Failed"

echo "Running on raspi: $EXECMD"
ssh $TARGET "$EXECMD" || echo "Failed"


