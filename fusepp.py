#!/usr/bin/env python

from __future__ import with_statement

import subprocess
import inspect
import os
import sys
import errno
import string
import shutil
import filecmp

import fuse

#from fuse import Fuse, FuseOSError


class Filesystem(fuse.Operations):
    def __init__(self, root):
        self.root = root

    # unused features
    access = None
    flush = None
    getattr = None
    getxattr = None
    listxattr = None
    open = None
    opendir = None
    read = None
    readdir = None
    release = None
    releasedir = None
    statfs = None

def main(mountpoint, root):
    fuse.FUSE(Filesystem(root), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
