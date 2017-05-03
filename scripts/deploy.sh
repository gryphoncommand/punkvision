#!/bin/sh

FROMDIR="$PWD"
FOLDER="punkvision"
TMPDIR="/tmp/$FOLDER"

rm -rf $TMPDIR
mkdir -p $TMPDIR

cd $TMPDIR

mkdir -p $TMPDIR/src
mkdir -p $TMPDIR/scripts
mkdir -p $TMPDIR/configs

# copy en masse these files
find $FROMDIR/src -name "*.py" -exec cp {} $TMPDIR/src \;
find $FROMDIR/scripts -name "*.sh" -exec cp {} $TMPDIR/scripts \;
find $FROMDIR/configs -name "*.conf" -exec cp {} $TMPDIR/configs \;

# some additional files
cp $FROMDIR/README.md $TMPDIR/README.md
cp $FROMDIR/TE.AM $TMPDIR/TE.AM
cp $FROMDIR/R.PI $TMPDIR/R.PI

cd $FROMDIR

rm *.tar*
echo "Tarring"


TARFILE="$FOLDER.tar.xz"

tar cfJ $TARFILE  -C $TMPDIR/.. $FOLDER


TARGET="$1"
SOURCES="$TARFILE"

if [ "$TARGET" = "" ]; then
    TARGET="pi@raspberrypi.local"
fi

HERECMD="scp -r $SOURCES $TARGET:~/Downloads ${2} ${3} ${4}"

echo "You may be prompted for passwords"

echo "Running here: $HERECMD"
bash -c "$HERECMD" || echo "Failed on HOST"


