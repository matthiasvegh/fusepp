fusepp
======

A fuse based filesystem for abusing the C preprocessor.

Purpose
-------
Traditionally, the C preprocessor is limited in what it can do, many techniques that can be found in dynamic languages and C++ template metaprograms would be nice to have in preprocessor metaprograms, but simply cannot be done.
Consider:
```
#define prepareC \
#define C 1

prepareC
C
```
Passing this through the C preprocessor will result in something like the following:
```
# 1 "mountpoints/b"
# 1 "<command-line>"
# 1 "mountpoints/b"



 #define C 1
 C
```
This is clearly not what we wanted, what we would have liked was something like this:
```
# 1 "mountpoints/b"
# 1 "<command-line>"
# 1 "mountpoints/b"



 #define C 1
 C
# 1 "<stdin>"
# 1 "<command-line>"
# 1 "<stdin>"
# 1 "mountpoints/b"
# 1 "<command-line>"
# 1 "mountpoints/b"




 1
```
That is, we want to rerun the preprocessor on demand, but we don't really want to change our build-system just to account for some esoteric programming technique.

Solution
--------
One thing the C preprocessor will do for us, is copy files into its buffer, not only this, it will also preprocess the file it copied.
We could alter the example above by rewriting it as follows:
```
#define prepareC \
#include "preparation_for_C"

prepareC
C
```
with "preparation-for-c" being:
```
#define C 1
```
This still isn't ideal, but the filesystem from which we include could generate the included file we need. This project explores this possibility.

Usage
-----
Simply run as `./fusepp.py MOUNTPOINT PROXYDIRECTORY` where MOUNTPOINT is where you would like the filesystem to be visible, and PROXYDIRECTORY is the underlying filesystem
