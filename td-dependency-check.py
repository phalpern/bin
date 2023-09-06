#! /usr/bin/python3

import sys
import re
import os
import textwrap
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
        self.excess_test_deps          = set()
        self.false_test_deps           = set()
        self.component_cycles          = set()
        self.testonly_cycles           = set()
        self.component_level           = 0     # excludes test driver
        self.testonly_level            = 0     # includes test driver
        components[component_name] = self

    def __less__(self, other):
        return self.component_name < other.component_name

    def __str__(self):
        ret = f"Component {self.component_name}:\n";
        ret += f"    Level number = {self.component_level}, " +      \
            f" Test driver level number = {self.testonly_level}\n"

        errors = 0
        warnings = 0

        if self.component_cycles:
            errors += 1
            ret += "    Error: Dependency cycles detected:\n"
            for cycle in self.component_cycles:
                ret += self.format_cycle(cycle) + '\n'

        if self.excess_test_deps:
            errors += 1
            ret += "    Error: Undocumented test-only dependencies:\n"
            for dep in sorted(self.excess_test_deps):
                ret += "        " + dep + '\n'

        if self.testonly_cycles:
            warnings += 1
            ret += "    Warning: Test-only dependency cycles:\n"
            for cycle in self.testonly_cycles:
                ret += self.format_cycle(cycle) + '\n'

        if self.component_level < self.testonly_level:
            warnings += 1
            ret += "    Warning: test driver has larger level number " + \
                "than component\n"

        if self.false_test_deps:
            warnings += 1
            ret += "    Warning: dependencies incorrectly marked " + \
                "'for testing only':\n"
            for dep in sorted(self.false_test_deps):
                ret += "        " + dep + '\n'

        if errors or warnings:
            ret += f"    {errors} Errors, {warnings} Warnings\n"
        else:
            ret += "    No errors or warnings\n"

        return ret

    def format_cycle(self, cycle):
        cycle_str = ""
        for component, testdep in cycle:
            cycle_str += component.component_name
            cycle_str += " -T> " if testdep else " -> "
        cycle_str += cycle[0][0].component_name
        return '\n'.join(textwrap.wrap(cycle_str, width=79,
                                       initial_indent="        ",
                                       subsequent_indent="            ",
                                       break_long_words=False))


    def visit(self, path = tuple()):

        if self.visited: return

        if self.visiting:
            # Found a cycle
            cycle_start = next((i for i in range(len(path))
                                if path[i][0] == self))
            cycle = path[cycle_start:]
            self.record_cycle(cycle)
            return

        hdr_file, imp_file, *test_files = ComponentFiles(self.component_name)

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

        # Note that our level is at least one more than the *test* level
        # (`testonly_level`) of components on which we depend, even when
        # traversing non-test dependencies.  That way, only level differences
        # corresponding to *this* component are reflected in the level
        # variables.
        level = 0
        for dependency_name in self.component_deps:
            dependency = visit_by_name(dependency_name,
                                       path + ((self, False),))
            level = max(level, dependency.testonly_level + 1)
        self.component_level = level
        for dependency_name in self.testonly_deps:
            dependency = visit_by_name(dependency_name, path + ((self, True),))
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

    def record_cycle(self, cycle):
        # Record testonly cycles first.
        testonly = False
        for i in range(len(cycle)):
            component, testdep = cycle[i]
            if testdep:
                testonly = True  # Found at least one test-only dependedency
                component.testonly_cycles.add(cycle[i:]+cycle[:i])

        if testonly: return  # If any deps are test-only, don't record cycles
        for i in range(len(cycle)):
            (component, testdep) = cycle[i]
            component.component_cycles.add(cycle[i:]+cycle[:i])

def visit_by_name(component_name, path = tuple()):

    if component_name in components:
        component = components[component_name]
    else:
        component = component_stats(component_name)
    component.visit(path)
    return component

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
    for component_name in sorted(component_set):
        print(components[component_name])
        # pprint(vars(components[component_name]))
