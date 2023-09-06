#! /usr/bin/env python3

# stdin = patch file
# stdout = patch file without _cpp03.* diffs

import sys
import re

doprint = True

diffStart = re.compile(r"^diff --git ")
diffStart_cpp03 = re.compile(r"^diff --git .*_cpp03\.")

for line in sys.stdin:
    if diffStart_cpp03.match(line):
        doPrint = False
    elif diffStart.match(line):
        doPrint = True
    if doPrint:
        print(line, end='')
