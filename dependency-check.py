#! /usr/bin/python3

import sys
import re
import os
import textwrap
from glob import glob

# Global variables
progname    = "PROGRAM"
verbose     = False
package     = None
package_dir = None

suffix_re = re.compile(r"\.(h|cpp|([0-9]+\.)?t\.cpp)?$")
cpp03_re  = re.compile(r"_cpp03$")

include_pattern = r'^\s*#\s*include\s+["<](PKG_\w+).h[">]( *//.*\btesting\b)?'
include_re      = None

components = { }

def component_files(*paths):
    """Return a tuple of component files for the given path(s)"""
    for path in paths:
        component_path = suffix_re.sub('', path)
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
        self.error_count               = 0
        self.warning_count             = 0
        components[component_name] = self

    def __less__(self, other):
        return self.component_name < other.component_name

    def __str__(self):
        ret = f"Component {self.component_name}:\n";
        ret += f"    Level number = {self.component_level}, " +      \
            f"Test driver level number = {self.testonly_level}\n"

        if self.component_cycles:
            ret += "    Error: Dependency cycles detected:\n"
            for cycle in self.component_cycles:
                ret += self.format_cycle(cycle) + '\n'

        if self.excess_test_deps:
            ret += "    Warning: Undocumented test-only dependencies:\n"
            for dep in sorted(self.excess_test_deps):
                ret += "        " + dep + '\n'

        if self.testonly_cycles:
            ret += "    Warning: Test-only dependency cycles:\n"
            for cycle in self.testonly_cycles:
                ret += self.format_cycle(cycle) + '\n'

        if self.component_level < self.testonly_level:
            ret += "    Warning: test driver has larger level number " + \
                "than component\n"

        if self.false_test_deps:
            ret += "    Warning: dependencies incorrectly marked " + \
                "'for testing only':\n"
            for dep in sorted(self.false_test_deps):
                ret += "        " + dep + '\n'

        if self.error_count or self.warning_count:
            ret += (f"    {self.error_count} Errors, " +
                    f"{self.warning_count} Warnings\n")
        else:
            ret += "    No errors or warnings\n"

        return ret

    def format_cycle(self, cycle):
        cycle_str = ""
        for component, testdep in cycle:
            cycle_str += component.component_name
            cycle_str += " T-> " if testdep else " -> "
        cycle_str += cycle[0][0].component_name
        return '\n'.join(textwrap.wrap(cycle_str, width=79,
                                       initial_indent="        ",
                                       subsequent_indent="            ",
                                       break_long_words=False))

    def visit(self, path = tuple()):

        if self.visited: return

        if self.visiting:
            # Found a cycle
            self.record_cycle(path)
            return

        self.get_direct_deps()

        self.visiting = True

        # Note that our level is at least one more than the *test* level
        # (`testonly_level`) of components on which we depend, even when
        # traversing non-test dependencies.  That way, only level differences
        # corresponding to *this* component are reflected in the level
        # variables.
        level = 1
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

        self.count_errors_and_warnings()

        return

    def get_direct_deps(self):
        hdr_file, imp_file, *test_files = component_files(self.component_name)

        self.component_deps = self.get_file_deps(hdr_file).union(
            self.get_file_deps(imp_file, self.testonly_deps))
        for test_file in test_files:
            for inc in self.get_file_deps(test_file):
                if (inc not in self.component_deps and
                    inc not in self.testonly_deps):
                    self.testonly_deps.add(inc)
                    self.excess_test_deps.add(inc)
                    self.warning_count += 1
        self.false_test_deps = \
            self.testonly_deps.intersection(self.component_deps)
        self.testonly_deps   = \
            self.testonly_deps.difference(self.false_test_deps)

    def get_file_deps(self, file_name, testonly_deps = None):
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

    def record_cycle(self, path):
        # Find the start of the cycle in the path
        cycle_start = next((i for i in range(len(path)) if path[i][0] == self))
        cycle = path[cycle_start:]

        # Record the cycle in every component that participates in it, starting
        # with the ones starting with a test-only dependency.
        testonly = False
        for i in range(len(cycle)):
            component, testdep = cycle[i]
            if testdep:
                testonly = True  # Found at least one test-only dependedency
                component.testonly_cycles.add(cycle[i:]+cycle[:i])

        # If any deps are test-only stop here; do not report non-test-only
        # cycle for remaining components.
        if testonly: return

        for i in range(len(cycle)):
            (component, testdep) = cycle[i]
            component.component_cycles.add(cycle[i:]+cycle[:i])

    def count_errors_and_warnings(self):
        self.error_count   = 0
        self.warning_count = 0
        if self.component_cycles:                      self.error_count += 1
        if self.excess_test_deps:                      self.warning_count += 1
        if self.false_test_deps:                       self.warning_count += 1
        if self.testonly_cycles:                       self.warning_count += 1
        if self.component_level < self.testonly_level: self.warning_count += 1

def visit_by_name(component_name, path = tuple()):

    if component_name in components:
        component = components[component_name]
    else:
        component = component_stats(component_name)
    component.visit(path)
    return component

def usage(error_str = None):
    if error_str is not None:
        print(error_str, file=sys.stderr)
    print(f"Usage: {progname} [--help] [--verbose] " +
          "[component|package]...", file=sys.stderr)

def process_args(argv):
    global progname
    global verbose

    progname = os.path.basename(argv[0])
    cpt_args = []
    for arg in argv[1:]:
        if arg == "--help":
            usage()
            return None
        elif arg == "--verbose":
            verbose = True
            continue
        elif arg.startswith("-"):
            usage(f"Invalid option: {arg}")
            return None
        else:
            cpt_args.append(arg)

    if not cpt_args:
        usage()
        return None

    # TBD: Error handling for missing directories or components belongs below
    ret = []
    for arg in cpt_args:
        if os.path.isdir(arg):
            package_path  = arg
            mem_file_glob = os.path.join(package_path, "package", "*.mem")
            mem_file_list = glob(mem_file_glob)
            assert(1 == len(mem_file_list))
            with open(mem_file_list[0], 'r') as mem_file:
                mem_file_content = mem_file.read()
                mem_file_content = \
                    re.sub("#.*$", "", mem_file_content, re.MULTILINE)
                ret += map(lambda x: os.path.join(package_path, x),
                           re.findall(r"(\w+)", mem_file_content))
        else:
            ret.append(arg)

    return ret

if __name__ == "__main__":
    args = process_args(sys.argv)
    if args is None:
        exit(1)

    component_map = dict()
    for name in args:
        if name == "": continue
        component_path = cpp03_re.sub("", suffix_re.sub("", name))
        component_name = os.path.basename(component_path)
        component_map[component_name] = component_path

    total_error_count   = 0
    total_warning_count = 0
    original_dir = os.getcwd()
    for component_name, component_path in sorted(component_map.items()):

        if package != component_name.split('_')[0]:
            package_path = os.path.dirname(component_path)
            package      = component_name.split('_')[0]
            os.chdir(original_dir)
            if package_path:
                os.chdir(package_path)
            include_re = re.compile(include_pattern.replace("PKG", package),
                                    re.MULTILINE)

        component = visit_by_name(component_name)
        total_error_count   += component.error_count
        total_warning_count += component.warning_count
        if verbose or component.error_count > 0 or component.warning_count > 0:
            print(component)

    if total_error_count or total_warning_count:
        print(f"Total: {total_error_count} errors, " +
              f"{total_warning_count} warnings", file=sys.stderr)

    if total_error_count:
        exit(total_error_count)
