#! /usr/bin/python3

import sys
import re
import os
from pprint import pprint
from component_files import ComponentFiles

package     = None
package_dir = None

suffix_re  = re.compile(r"(_cpp03)?\.(h|cpp|([0-9]+\.)?t\.cpp)?$")

include_pattern = r'^\s*#\s*include\s+["<](PKG_\w+).h[">]( *//.*\btesting\b)?'
include_re      = None

components = { }

class component_stats:

    def __init__(self, component_name):
        global components
        assert(component_name not in components)

        self.component_name            = component_name
        self.visiting                  = False
        self.visited                   = False
        self.component_deps            = set()
        self.testonly_deps             = set()
#       self.transitive_component_deps = set()
        self.excess_test_deps          = set()
        self.component_cycles          = set()
        self.testonly_cycles           = set()
        self.component_level           = 0     # excludes test driver
        self.testonly_level            = 0     # includes test driver
        components[component_name] = self

    def visit(self, path = tuple()):

        if self.visited: return

        if self.visiting:
            # Found a cycle
            cycle_start = path.index(self)
            cycle = path[cycle_start:]
            if cycle[1].component_name in self.testonly_deps:
                self.testonly_cycles.add(cycle)
            else:
                self.component_cycles.add(cycle)
                # Record cycle in all of the components within the cycle
                for i in range(1, len(cycle)):
                    cycle[i].component_cycles.add(cycle[i:]+cycle[0:i])
            return

        hdr_file, imp_file, *test_files = ComponentFiles(self.component_name)

        self.excess_test_deps = set()
        self.component_deps = self.get_direct_deps(hdr_file).union(
            self.get_direct_deps(imp_file, self.testonly_deps))
        for test_file in test_files:
            for inc in self.get_direct_deps(test_file):
                if (inc not in self.component_deps and
                    inc not in self.testonly_deps):
                    self.testonly_deps.add(inc)
                    self.excess_test_deps.add(inc)
        self.false_test_deps = \
            self.testonly_deps.intersection(self.component_deps)
        self.testonly_deps   = \
            self.testonly_deps.difference(self.false_test_deps)

        self.visiting = True

        # if component_name == "bslma_isstdallocator":
        #     print([ x.component_name for x in path + (self,) ])
        #     pprint(vars(self))

        level = 0
        for dependency_name in self.component_deps:
            dependency = visit_by_name(dependency_name, path + (self,))
            level = max(level, dependency.testonly_level + 1)
        self.component_level = level
        for dependency_name in self.testonly_deps:
            dependency = visit_by_name(dependency_name, path + (self,))
            level = max(level, dependency.testonly_level + 1)
        self.testonly_level = level

        self.visiting = False
        self.visited  = True

        return

    def get_direct_deps(self, file_name, testonly_deps = None):
        """Return a set of files `#include`d from `file_name`.  If
        `testonly_deps` is not None, segregate testing only includes into
        that set"""
        with open(file_name, 'r') as file:
            file_content = file.read()
            pkg_includes = include_re.findall(file_content)
            ret = set()
            for pkg_include in pkg_includes:
                inc_component = pkg_include[0]
                testonly      = pkg_include[1] != ""
                if inc_component == self.component_name:
                    continue
                elif inc_component.endswith("_cpp03"):
                    continue
                elif testonly_deps is None or not testonly:
                    ret.add(inc_component)
                else:
                    testonly_deps.add(inc_component)

        return ret


def visit_by_name(component_name, path = tuple()):

    if component_name in components:
        component = components[component_name]
    else:
        component = component_stats(component_name)
    component.visit(path)
    return component

def get_includes(file_name):
    component   = os.path.basename(component_path)
    package     = component.split('_')[0]
    pattern     = r'^\s*#\s*include\s+["<](' + package + '_\w+.h)[">]'
    with open(file_name, 'r') as file:
        file_content = file.read()
        pkg_includes = re.findall(pattern, file_content, re.MULTILINE)
        return { inc for inc in pkg_includes if not inc.endswith("_cpp03.h") }

def process_component(component_path):
    component_name = os.path.basename(component_path)
    component      = components[component_name]

    header      = component_path + ".h"
    imp         = component_path + ".cpp"
    test_driver = component_path + ".t.cpp"

    component_deps = get_includes(header).union(get_includes(imp))
    test_deps      = get_includes(test_driver)

    excess_deps = test_deps.difference(component_deps)
    if excess_deps:
        print(f"\nExcess test-driver dependencies for {component}:")
        for excess in sorted(list(excess_deps)):
            print(f"#include <{excess}>  // for testing only")

if __name__ == "__main__":
    component_set = set()
    for name in sys.argv[1:]:
        component_path = suffix_re.sub("", name)
        component_name = os.path.basename(component_path)

        if package is None:
            package_path = os.path.dirname(component_path)
            package      = component_name.split('_')[0]
            if package_path:
                os.chdir(package_path)
            include_re = re.compile(include_pattern.replace("PKG", package),
                                    re.MULTILINE)
        else:
            assert(package_path == os.path.dirname(component_path))
            assert(package      == component_name.split('_')[0])

        component_set.add(component_name)

    for component_name in component_set:
        visit_by_name(component_name)
    for component_name in component_set:
        print(components[component_name])
        pprint(vars(components[component_name]))
