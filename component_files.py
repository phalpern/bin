#! /usr/bin/python3

import sys
import re
import os

component_re = re.compile(r'\.(h|cpp|([0-9]+\.)?t\.cpp)?$')

def ComponentFiles(*paths):
    """Return a tuple of component files for the given path(s)"""
    for path in paths:
        component_path = component_re.sub('', path)
        files = [ component_path + ".h", component_path + ".cpp" ]
        if os.path.exists(component_path + ".0.t.cpp"):
            # Has numbered tests
            files.append(component_path + ".0.t.cpp")
        else:
            # Does not have numbered test files
            files.append(component_path + ".t.cpp")
            return tuple(files)
        test_num = 1
        while True:
            test_path = component_path + '.' + str(test_num) + ".t.cpp"
            if os.path.exists(test_path):
                files.append(test_path)
                test_num += 1
            else:
                break
        return tuple(files)

if __name__ == "__main__":
    for file in sys.argv[1:]:
        for cpt_file in ComponentFiles(file):
            print(cpt_file + ' ', end='')
