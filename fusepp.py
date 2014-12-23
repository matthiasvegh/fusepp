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


class Passthrough(fuse.Operations):
    def __init__(self, root):
        self.root = root

    # Helpers
    # =======

    def _runcommandn(self, count, cmd_template, base):
        subprocess.call(cmd_template.substitute(input=os.path.join(self.root, base)), shell=True)

        shutil.copy(os.path.join(self.root, base), "/tmp/.output")
        for iteration in range(count):
            subprocess.call("cat /tmp/.output", shell=True)
            shutil.move("/tmp/.output", "/tmp/.output2")
            cmd = cmd_template.substitute(input="/tmp/.output2")
            p = subprocess.Popen(cmd, shell=True)
            out, err = p.communicate()
            print p.returncode
            if p.returncode != 0:
                subprocess.call("cat /tmp/.error", shell=True)
                return "/tmp/.error"

        return "/tmp/.output"


    def _runcommandtillsame(self, cmd_template, base):
        subprocess.call(cmd_template.substitute(input=os.path.join(self.root, base)), shell=True)

        while self._arefilessame('/tmp/.output', '/tmp/.output2'):
            subprocess.call("cat /tmp/.output", shell=True)
            shutil.move("/tmp/.output", "/tmp/.output2")
            cmd = cmd_template.substitute(input="/tmp/.output2")
            subprocess.call(cmd, shell=True)

    def _arefilessame(self, left, right):
        return filecmp.cmp(left, right)

    def runcommand(self, path):
        cmd_template= string.Template("gcc -P -E -xc++-header $input -o - > /tmp/.output 2>/tmp/.error")
        if path.find("@@@@") == -1:
            return os.path.join(self.root, path)

        partial = path.rfind("@@@@")
        base = os.path.join(self.root, path[partial+5:])

        returnvalue = "/tmp/.output"

        if "@@@@@" in path:
            self._runcommandtillsame(cmd_template, base)
            return returnvalue

        count = path.count("/@@@@")

        return self._runcommandn(count, cmd_template, base)


    def getrealpath(self, path):
        return self._full_path(path[5:])

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise fuse.FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        if path.startswith("/@@@@"):
            full_path = self.getrealpath(path)
        else:
            full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        if path.startswith("/@@@@"):
            path = path[6:]
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if path == '/':
            dirents.append('@@@@')
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        if path.startswith("/@@@@"):
            full_path = self.runcommand(path)
            print "fp: ", full_path
            subprocess.call("cat /tmp/.error", shell=True)
            return os.open(full_path, flags)
        else:
            full_path = self._full_path(path)
            return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    fuse.FUSE(Passthrough(root), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])