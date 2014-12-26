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


def main(mountpoint, root):
    fuse.FUSE(Passthrough(root), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
