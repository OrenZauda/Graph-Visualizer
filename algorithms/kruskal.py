from typing import Any, Iterator

import networkx as nx

from .base import AlgorithmStep, Edge, EdgeState, GraphAlgorithm, Node, NodeState


class _UnionFind:
    def __init__(self, nodes) -> None:
        self.parent = {node: node for node in nodes}
        self.size = {node: 1 for node in nodes}

    def find(self, node: Node) -> Node:
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, a: Node, b: Node) -> bool:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        return True


class KruskalAlgorithm(GraphAlgorithm):
    """Kruskal's minimum-spanning-tree algorithm, yielding one AlgorithmStep per edge considered."""

    def run(self) -> Iterator[AlgorithmStep]:
        graph = self.graph
        uf = _UnionFind(graph.nodes)

        edges = sorted(graph.edges(data=True), key=lambda e: e[2].get("weight", 1))

        node_states = {node: NodeState.UNVISITED for node in graph.nodes}
        edge_states: dict[Edge, EdgeState] = {(u, v): EdgeState.UNVISITED for u, v, _ in edges}

        index = 0
        yield AlgorithmStep(
            index=index,
            description=f"Sort {len(edges)} edges by weight",
            node_states=dict(node_states),
            edge_states=dict(edge_states),
        )

        mst_edges: list[Edge] = []
        total_weight = 0
        target_edges = graph.number_of_nodes() - nx.number_connected_components(graph)

        for u, v, data in edges:
            if len(mst_edges) == target_edges:
                break

            weight = data.get("weight", 1)
            edge_states[(u, v)] = EdgeState.CONSIDERING
            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Consider edge {u}-{v} (weight={weight})",
                node_states=dict(node_states),
                edge_states=dict(edge_states),
            )

            if uf.union(u, v):
                edge_states[(u, v)] = EdgeState.IN_RESULT
                node_states[u] = NodeState.IN_RESULT
                node_states[v] = NodeState.IN_RESULT
                mst_edges.append((u, v))
                total_weight += weight
                description = f"Accept edge {u}-{v}: connects two components"
            else:
                edge_states[(u, v)] = EdgeState.REJECTED
                description = f"Reject edge {u}-{v}: would create a cycle"

            index += 1
            yield AlgorithmStep(
                index=index,
                description=description,
                node_states=dict(node_states),
                edge_states=dict(edge_states),
            )

        index += 1
        yield AlgorithmStep(
            index=index,
            description=f"Done: MST has {len(mst_edges)} edges, total weight = {total_weight}",
            node_states=dict(node_states),
            edge_states=dict(edge_states),
            is_final=True,
            result={"edges": ",".join(f"{u}-{v}" for u, v in mst_edges), "total_weight": total_weight},
        )
