#! /usr/bin/python3
#
# Find cycles within a package.
#
# Usage for package bxxyyy:
#   cd groups/bxx/bxxyyy
#   component_cycles.py *.h *.cpp

import sys
import re

def normalize_cycle(cycle):
    """Takes the 'cycle' list and normalize it such that it starts with the lowest-valued node name."""
    if not cycle:
        return []

    # Find the index of the lowest-valued string in the list
    lowest_string_index = cycle.index(min(cycle))

    cycle_start = cycle[lowest_string_index]
    cycle =  cycle[lowest_string_index:] + cycle[:lowest_string_index]
    cycle.append(cycle_start)
    return cycle

def find_cycles(graph):
    def dfs(node, visited, path):
        visited[node] = True
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor == node:
                continue  # Ignore single-node cycles
            elif neighbor in path:  # Cycle found
                cycle_start = path.index(neighbor)
                cycle = normalize_cycle(path[cycle_start:])
                cycles.add(tuple(cycle))
            elif not visited.get(neighbor, False):
                dfs(neighbor, visited, path)

        path.pop()
        visited[node] = False

    cycles = set()
    visited = {}

    for node in graph.keys():
        if not visited.get(node, False):
            dfs(node, visited, [])

    return cycles

def build_dependency_graph(cpp_files):
    include_pattern = re.compile(r'^\s*#\s*include\s+["<](\w+)\.h[">]',
                                 re.MULTILINE)

    components_dict = {}

    for file_name in cpp_files:
        with open(file_name, 'r') as file:
            file_content = file.read()
            component_name = file_name.split('.')[0]

            referenced_components = \
                set(include_pattern.findall(file_content))

            if component_name not in components_dict:
                components_dict[component_name] = set()

            components_dict[component_name].update(referenced_components)

    return components_dict

if __name__ == "__main__":
    dep_graph = build_dependency_graph(sys.argv)

    cycles_found = find_cycles(dep_graph)
    if cycles_found:
        print("Cycles found:")
        for cycle in sorted(list(cycles_found)):
            print(" -> ".join(cycle))
    else:
        print("No cycles found in the dependency graph.")
