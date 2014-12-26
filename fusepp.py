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

    def _getrealpath(self, path):
        """
        >>> fs=Filesystem('/foo')
        >>> fs._getrealpath('/bar')
        '/foo/bar'
        """
        return os.path.join(self.root, path[1:])

    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(self._getrealpath(path))

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
    import doctest
    doctest.testmod()
    main(sys.argv[2], sys.argv[1])
