#! /usr/bin/python3

"""Find the standard headers with the specified file names.  This first version
uses gcc-11 in C++20 mode.  Future versions might allow versioning.

Usage: findstdhdr.py <header-name>..."""

import sys
import subprocess as sp
import re
import os

def usage(msg = None):
    if msg is not None:
        sys.stderr.write(msg)
    sys.stderr.write(f"Usage: {sys.argv[0]} <regex> <header>...")

if len(sys.argv) < 3:
    usage("Not enough command-line arguments")

# The header file name is the last command-line argument unless there is a "--"
# in the command line, in which case the header file is all of the arguments
# following the "--".  The grep arguments are all of the arguments up to the
# first header argument (excluding any "--").
if "--" in sys.argv:
    dd_index = sys.argv.index("--")
    grepargs = sys.argv[1:dd_index]
    headers  = sys.argv[dd_index+1:]
else:
    grepargs = sys.argv[1:-1]
    headers  = sys.argv[-1:]

tmpfilename = "/tmp/findstdhdr_dummy.cpp"

# Generate a temporary .cpp file having one '#include' line for each header
with open(tmpfilename, "w+") as cfile:
    for header in headers:
        cfile.write(f"#include <{header}>\n")

# Collect the full path names of the headers plus any headers they include,
# transitively.
cmpresult = sp.run(["g++-11", "-M", "-std=c++20", tmpfilename],
                   stdout=sp.PIPE).stdout.decode("ascii")

os.remove(tmpfilename)

# Split the output into separate header-file names to grep.  The first two
# words of output are an intro phrase and the name of the temporary file, so we
# discard those.
grepfiles = re.split(r'\s*\\?\s+', cmpresult)[2:]
if not grepfiles[-1]: grepfiles = grepfiles[:-1]

sp.run(["egrep"] + grepargs + grepfiles)
