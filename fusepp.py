#!/usr/bin/env python

from __future__ import with_statement

import subprocess
import inspect
import os
import sys
import stat
import errno
import string
import shutil
import tempfile
import filecmp
import threading
from _threading_local import local
import psutil
import time

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

    def getextraargs(self, pid):
        process = psutil.Process(pid)
        args = process.cmdline()

        extraargs = ''

        index = 0
        length = len(args)
        while index < length:
            arg = args[index]
            if arg.startswith('-D') or arg.startswith('-I') or arg.startswith('-isystem'):
                extraargs += ' ' + arg + args[index+1]
                index = index+1
            index = index+1

        return extraargs

    def _runcommand(self, path, output=None, extraargs=''):
        if output is None:
            output = tempfile.mkstemp()[1]

        cmd_template = string.Template('g++ -P -E -xc++ $extraargs $input -o $output 2>$error')

        fullpath = self._getrealpath(path)

        cmd = cmd_template.substitute(output=output, error='/dev/null', input=fullpath, extraargs=extraargs)
        subprocess.call(cmd, shell=True)

        return os.lstat(output).st_size

    def _getnewfd(self, path, pid):
        with self._rwlock:
            nextavailable = _max(self._openfds.keys()) +1
            self._openfds[nextavailable] = tempfile.mkstemp()
            name = self._openfds[nextavailable][1]
            self._openfiles[path] = nextavailable

        extraargs = self.getextraargs(pid)
        self._runcommand(path, name, extraargs)
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
        answer = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

        if stat.S_ISREG(answer['st_mode']):
            size = self._runcommand(path)
            answer['st_size'] = size

        return answer

    def statfs(self, path):
        stv = os.statvfs(self._getrealpath(path))
        answer =  dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
        return answer

    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(self._getrealpath(path))

    def open(self, path, fi):
        # Run command and return fd to it
        pid = fuse.fuse_get_context()[2]
        fd = self._getnewfd(path, pid)

        fi.fh = fd
        fi.direct_io = True
        # No OS caching allowed, all reads must go through us

    def release(self, path, fi):
        fh = fi.fh
        with self._rwlock:
            assert(self._openfiles[path] == fh)
            os.remove(self._openfds[fh][1])
            del self._openfds[fh]
            del self._openfiles[path]

    def read(self, path, size, offset, fi):
        fh = fi.fh
        assert(self._openfiles[path] == fh)
        fd = os.open(self._openfds[fh][1], os.O_RDONLY)
        os.lseek(fd, offset, os.SEEK_SET)
        buf = os.read(fd, size)
        os.close(fd)
        return buf

    # unused features
    access = None
    flush = None
    getxattr = None
    listxattr = None
    opendir = None
    releasedir = None

def main(mountpoint, root):
    fuse.FUSE(Filesystem(root), mountpoint, raw_fi=True, foreground=True)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main(sys.argv[2], sys.argv[1])
