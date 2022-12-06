# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.


"""Utils for diffing transport graphs"""


from collections import deque
from typing import Callable

import networkx as nx

from covalent._workflow.transport import _TransportGraph

_status_map = {1: True, -1: False}


def _invalidate_successors(A: nx.MultiDiGraph, node_statuses: dict, starting_node: int):
    nodes_to_invalidate = [starting_node]
    for node, successors in nx.bfs_successors(A, starting_node):
        for child in successors:
            nodes_to_invalidate.append(child)
    for node in nodes_to_invalidate:
        node_statuses[node] = -1


def _same_node(A: nx.MultiDiGraph, B: nx.MultiDiGraph, node: int):
    return A.nodes[node] == B.nodes[node]


def _same_edge_attributes(A: nx.MultiDiGraph, B: nx.MultiDiGraph, parent: int, node: int):
    return A.adj[parent][node] == B.adj[parent][node]


def max_cbms(
    A: nx.MultiDiGraph,
    B: nx.MultiDiGraph,
    node_cmp: Callable = _same_node,
    edge_cmp: Callable = _same_edge_attributes,
):
    """Computes a "maximum backward-maximal common subgraph" (cbms)

    Args:
        A: nx.MultiDiGraph
        B: nx.MultiDiGraph
        node_cmp: An optional function for comparing node attributes in A and B.
                  Defaults to testing for equality of the attribute dictionaries
        edge_cmp: An optional function for comparing the edges between two nodes.
                  Defaults to checking that the two sets of edges have the same attributes

    Returns: A_node_status, B_node_status, where each is a dictionary
        `{node: True/False}` where True means reusable.

    Performs a modified BFS of A and B.
    """

    A_node_status = {node_id: 0 for node_id in A.nodes}
    B_node_status = {node_id: 0 for node_id in B.nodes}
    print("A node status:", A_node_status)
    print("B node status:", B_node_status)

    virtual_root = -1

    if virtual_root in A.nodes or virtual_root in B.nodes:
        raise RuntimeError(f"Encountered forbidden node: {virtual_root}")

    assert virtual_root not in B.nodes

    nodes_to_visit = deque()
    nodes_to_visit.appendleft(virtual_root)

    # Add a temporary root
    A_parentless_nodes = [node for node, deg in A.in_degree() if deg == 0]
    B_parentless_nodes = [node for node, deg in B.in_degree() if deg == 0]
    for node_id in A_parentless_nodes:
        A.add_edge(virtual_root, node_id)

    for node_id in B_parentless_nodes:
        B.add_edge(virtual_root, node_id)

    # Assume inductively that predecessors subgraphs are the same;
    # this is satisfied for the root
    while nodes_to_visit:
        current_node = nodes_to_visit.pop()

        print(f"Visiting node {current_node}")
        for y in A.adj[current_node]:
            # Don't process already failed nodes
            if A_node_status[y] == -1:
                continue

            # Check if y is a valid child of current_node in B
            if y not in B.adj[current_node]:
                print(f"A: {y} not adjacent to node {current_node} in B")
                _invalidate_successors(A, A_node_status, y)
                continue

            if y in B.adj[current_node] and B_node_status[y] == -1:
                print(f"A: Node {y} is marked as failed in B")
                _invalidate_successors(A, A_node_status, y)
                continue

            # Compare edges
            if not edge_cmp(A, B, current_node, y):
                print(f"Edges between {current_node} and {y} differ")
                _invalidate_successors(A, A_node_status, y)
                _invalidate_successors(B, B_node_status, y)
                continue

            # Compare nodes
            if not node_cmp(A, B, y):
                print(f"Attributes of node {y} differ:")
                print(f"A[y] = {A.nodes[y]}")
                print(f"B[y] = {B.nodes[y]}")
                _invalidate_successors(A, A_node_status, y)
                _invalidate_successors(B, B_node_status, y)
                continue

            # Predecessors subgraphs of y are the same in A and B, so
            # enqueue y if it hasn't already been visited
            assert A_node_status[y] != -1
            if A_node_status[y] == 0:
                A_node_status[y] = 1
                B_node_status[y] = 1
                print(f"Enqueueing node {y}")
                nodes_to_visit.appendleft(y)

        # Prune children of current_node in B that aren't valid children in A
        for y in B.adj[current_node]:
            if B_node_status[y] == -1:
                continue
            if y not in A.adj[current_node]:
                print(f"B: {y} not adjacent to node {current_node} in A")
                _invalidate_successors(B, B_node_status, y)
                continue
            if y in A.adj[current_node] and B_node_status[y] == -1:
                print(f"B: Node {y} is marked as failed in A")
                _invalidate_successors(B, B_node_status, y)

    A.remove_node(-1)
    B.remove_node(-1)

    print("A node status:", A_node_status)
    print("B node status:", B_node_status)

    for k, v in A_node_status.items():
        A_node_status[k] = _status_map[v]
    for k, v in B_node_status.items():
        B_node_status[k] = _status_map[v]
    return A_node_status, B_node_status


# Default node comparison function for diffing transport graphs
def _cmp_name_and_pval(A: nx.MultiDiGraph, B: nx.MultiDiGraph, node: int):

    # Compare function names and parameter values

    name_A = A.nodes[node]["name"]
    name_B = B.nodes[node]["name"]

    if name_A != name_B:
        return False

    val_A = A.nodes[node].get("value", None)
    val_B = B.nodes[node].get("value", None)

    if val_A != val_B:
        return False

    return True


def compare_transport_graphs(tg_old: _TransportGraph, tg_new: _TransportGraph):
    A = tg_old.get_internal_graph_copy()
    B = tg_new.get_internal_graph_copy()
    status_A, status_B = max_cbms(A, B, _cmp_name_and_pval)
    return [k for k, v in status_A.items() if v]