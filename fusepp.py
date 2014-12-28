#!/usr/bin/env python

from __future__ import with_statement

import subprocess
import inspect
import os
import sys
import errno
import string
import shutil
import tempfile
import filecmp
import threading

import fuse

#from fuse import Fuse, FuseOSError

def _max(iterable):
    """
    Max is zero, even if iterable is empty

    >>> _max([])
    0
    >>> _max([5])
    5
    >>> _max([1, 2])
    2
    """
    try:
        return max(iterable)
    except ValueError:
        return 0


class Filesystem(fuse.Operations):
    def __init__(self, root):
        self.root = root
        self._rwlock = threading.Lock()
        self._openfds = dict()
        self._openfiles = dict()

    def _getnewfd(self, path):
        with self._rwlock:
            nextavailable = _max(self._openfds.keys()) +1
            self._openfds[nextavailable] = tempfile.mkstemp()
            self._openfiles[path] = nextavailable
            return nextavailable

    def _getrealpath(self, path):
        """
        Get true path for proxy requests

        >>> fs=Filesystem('/foo')
        >>> fs._getrealpath('/bar')
        '/foo/bar'
        >>> fs._getrealpath('/')
        '/foo/'
        """
        return os.path.join(self.root, path[1:])

    def getattr(self, path, fh=None):
        st = os.lstat(self._getrealpath(path))
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def statfs(self, path):
        stv = os.statvfs(self._getrealpath(path))
        return dict((key, gettattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_avail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(self._getrealpath(path))

    def open(self, path, flags):
        # Run command and return fd to it
        fd = self._getnewfd(path)
        return fd

    def release(self, path, fh):
        with self._rwlock:
            assert(self._openfiles[path] == fh)
            # remove tmp
            del self._openfds[fh]
            del self._openfiles[path]

    # unused features
    access = None
    flush = None
    getxattr = None
    listxattr = None
    opendir = None
    read = None
    releasedir = None

def main(mountpoint, root):
    fuse.FUSE(Filesystem(root), mountpoint, foreground=True)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main(sys.argv[2], sys.argv[1])
