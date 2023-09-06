#! /usr/local/bin/python3

import sys
import os.path as path
import shutil

for filename in sys.argv:
    (dir, base) = path.split(filename)
    if base[-4:] != ".mp3": continue
    # sortedDir = path.join(dir, "Sorted Podcasts")
    sortedDir = "/Volumes/K7"
    counterFilename = path.join(dir, "counter.txt");
    with open(counterFilename, "r+") as counterFile:
        count = int(counterFile.read())
        counterFile.seek(0)
        counterFile.write(str(count + 1))
    copyFilename = path.join(sortedDir, f"{count:0>3}.{base}",)
    shutil.copyfile(filename, copyFilename)
