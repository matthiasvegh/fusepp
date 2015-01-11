#!/usr/bin/env bash

PROJECTNAME="fusepp"
MAJOR=0
MINOR=1
PACKAGEREV=1

PACKAGENAME="${PROJECTNAME}_${MAJOR}.${MINOR}-${PACKAGEREV}"

BUILDDIR=".build/$PACKAGENAME"
mkdir -p "$BUILDDIR"

mkdir -p "$BUILDDIR/usr"
mkdir -p "$BUILDDIR/usr/local"
mkdir -p "$BUILDDIR/usr/local/bin"
mkdir -p "$BUILDDIR/usr/local/include"

cp ./fusepp.py "$BUILDDIR/usr/local/bin"
cp ./include/fusepp.hpp "$BUILDDIR/usr/local/include"


mkdir -p "$BUILDDIR/DEBIAN"
cat > "$BUILDDIR/DEBIAN/control" <<End-of-message
Package: fusepp
Version: 0.1-1
Section: devel
Priority: optional
Architecture: i386
Depends: python (>= 2.7.0), python-psutil, python-fuse
Maintainer: Matthias Vegh matyas.vegh@gmail.com
Description: fusepp
 Read-only preprocessed filesystem for C/C++

End-of-message


cd "./.build"
dpkg-deb --build "$PACKAGENAME"
