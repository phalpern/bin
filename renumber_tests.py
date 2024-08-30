#! /usr/bin/python3

# Usage: renumber_tests.py <filename>
#
# The specified file must be in the form of a BDE test driver. Tests are
# renumbered in decending order of appearance.  Negative-numbered tests are not
# renumbered.  The table of contents at the begining of the test plan is
# modified to correspond to the renumbering; if a test is removed, any
# reference to that test in the TOC is replaced with a blank testcase number.
#
# To delete or reorder tests in the test driver, simply edit the test driver as
# desired.  To insert a test case, assign it a short alphanumeric label
# starting with a letter, e.g., `case NEW: {`.  New test cases will be assigned
# numbers during renumbering.  You can add new test cases to the TOC using the
# invented tag(s).
#
# Before renumbering, a backup of the test driver is made with a filename
# ending in `.bak`.  It is recommended that you diff the original and the
# backup before committing.  Only one backup is created, so running this tool
# multiple times will overwrite older backups (except that, if the script makes
# no changes, no backups are created).

import sys
import os
import re

# Regular expressions, compiled for efficiency
c_comment_re   = re.compile(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', flags=re.DOTALL)
cpp_comment_re = re.compile(r'//.*')
main_re        = re.compile(r'^ *int *main\b')
switch_re      = re.compile(r'^ +switch *\(')
case_re        = re.compile(r'^ +case +([1-9A-Za-z][0-9A-Za-z]*) *:')
planitem_re    = re.compile(r'^// +\[ *([1-9A-Za-z][0-9A-Za-z]*)\]')

def remove_comments(code):
    """Remove comments from the specifed multiline `code` and return the same
    code without comments.  Line breaks are preserved so that there remains
    a 1:1 correspondence between lines in the input and lines in the output."""

    # Remove all multi-line comments, preserving line breaks
    code = c_comment_re.sub(lambda m: re.sub(r'[^\n]+', '', m[0]), code)
    # Replace all single-line comments with spaces
    code = cpp_comment_re.sub('', code)
    return code

def find_case_lines(code):
    """Return a list of tuples, `(line-index`, case-label)`, for each top-level
    case statement in the top-level switch statement within `main`.  The
    line-index is the index into the array of lines == one less than the line
    number.  The case-label is a string that contains either an integer (for an
    old test case) or an alphanumeric identifier (for a new test cast).  The
    returned tuples are sorted in increasing order of line index
    """

    cases = []
    lines = remove_comments(code).split('\n')

    in_main = False
    brace_depth    = 0   # Current depth of braces
    switch_nesting = 0   # To handle nested switches
    switch_depth   = 0   # Brace depth of current switch
    switch_stack   = [ ] # Stack of switch depths

    for lineidx, line in enumerate(lines):

        if brace_depth == 0 and main_re.match(line):
            in_main = True

        if not in_main:
            continue

        if switch_re.match(line):
            switch_stack.append(switch_depth) # Save old depth
            switch_depth = brace_depth  # Depth *before* switch
            switch_nesting += 1  # Increment nesting level

        # Only consider cases at the first switch level
        if switch_nesting == 1:
            case_match = case_re.match(line)
            if case_match:
                cases.append(( lineidx, case_match[1] ))

        # Count braces to determine scope
        brace_depth += line.count('{')
        closed_count = line.count('}')
        brace_depth -= closed_count

        if switch_nesting > 0 and closed_count > 0 and brace_depth <= switch_depth:
            switch_nesting -= 1
            switch_depth = switch_stack.pop()

        # Exit main if braces close up
        if closed_count > 0 and brace_depth <= 0:
            assert(switch_nesting == 0)
            return cases

def renumber_testcases(code, testcases):
    """Renumber the test cases in the specified `code` and return the result.
    The `testcases` parameter is a list of tuples, `(line-index`, case-label)`
    indicating the line index and case labels in the original `code`.  The
    returned string has two types of modifications with respect to `code`:

    1. The case labels are changed to strictly descending integers starting
       at `len(testcases)` and ending at `1`.
    2. Any comment near the top of the file begining with "// [ n]", where
       n is a testcase label is renumbered to correspond to the new case lable.

    Note that `testcases` is assumed to be sorted in ascending order by line
    number."""

    lines = code.split('\n')

    # Create a mapping of old testcase labels to new testcase labels
    testcase_map = {}
    new_testnum = len(testcases)
    for lineidx, old_caselabel in testcases:
        new_caselabel = str(new_testnum)
        testcase_map[old_caselabel] = new_caselabel
        new_testnum -= 1
    assert(0 == new_testnum)

    # Update testcase labels in test plan at top of file
    first_testline = testcases[0][0]  # Line index of first case
    for lineidx, line in enumerate(lines):
        if lineidx >= first_testline:
            break;
        planitem_m = planitem_re.match(line)
        if planitem_m:
            old_caselabel = planitem_m[1]
            new_caselabel = testcase_map.get(old_caselabel, "  ")
            if len(new_caselabel) < 2: new_caselabel = ' ' + new_caselabel
            line = planitem_re.sub(f"// [{new_caselabel}]", line)
            lines[lineidx] = line;

    # Update testcase labels in `main`
    for lineidx, old_caselabel in testcases:
        line = lines[lineidx]
        new_caselabel = testcase_map[old_caselabel]
        line = case_re.sub(f"      case {new_caselabel}:", line)
        lines[lineidx] = line;

    return '\n'.join(lines)

# Run on the first file
filename = sys.argv[1]

with open(filename, 'r') as file:
    # Remove comments before processing lines
    oldcode = file.read()

testcases = find_case_lines(oldcode)

newcode = renumber_testcases(oldcode, testcases)

if newcode == oldcode:
    print("No changes")
else:
    os.replace(filename, filename + ".bak")
    with open(filename, 'w') as file:
        file.write(newcode)
    print(f"Renumbering complete. Old file saved as {filename}.bak.")
