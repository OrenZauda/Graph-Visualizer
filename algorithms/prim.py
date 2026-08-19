import heapq
from typing import Any, Iterator, Optional

from .base import AlgorithmStep, Edge, EdgeState, GraphAlgorithm, Node, NodeState


class PrimAlgorithm(GraphAlgorithm):
    """Prim's minimum-spanning-tree algorithm, yielding one AlgorithmStep per edge considered.

    Grows the tree from `source` (or the graph's first node if not given). If the graph is
    disconnected, restarts from an unvisited node in each remaining component, producing a
    maximum spanning forest just like KruskalAlgorithm.
    """

    def __init__(self, graph, source: Optional[Node] = None, **params: Any) -> None:
        super().__init__(graph, source=source, **params)
        self.source = source

    def run(self) -> Iterator[AlgorithmStep]:
        graph = self.graph
        nodes = list(graph.nodes)

        node_states = {node: NodeState.UNVISITED for node in graph.nodes}
        edge_states: dict[Edge, EdgeState] = {(u, v): EdgeState.UNVISITED for u, v in graph.edges()}

        def edge_key(a: Node, b: Node) -> Edge:
            return (a, b) if (a, b) in edge_states else (b, a)

        index = 0
        yield AlgorithmStep(
            index=index,
            description="Initialize: no nodes in the tree yet",
            node_states=dict(node_states),
            edge_states=dict(edge_states),
        )

        mst_edges: list[Edge] = []
        total_weight = 0
        in_tree: set[Node] = set()

        start_order = [self.source] if self.source is not None else []
        start_order += [n for n in nodes if n not in start_order]

        for start in start_order:
            if start in in_tree:
                continue

            in_tree.add(start)
            node_states[start] = NodeState.IN_RESULT
            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Add starting node {start} to the tree",
                node_states=dict(node_states),
                edge_states=dict(edge_states),
            )

            heap: list[tuple[float, Node, Node]] = []
            for neighbor in graph.neighbors(start):
                weight = graph[start][neighbor].get("weight", 1)
                heapq.heappush(heap, (weight, start, neighbor))

            while heap:
                weight, u, v = heapq.heappop(heap)
                if v in in_tree:
                    continue

                edge_states[edge_key(u, v)] = EdgeState.CONSIDERING
                index += 1
                yield AlgorithmStep(
                    index=index,
                    description=f"Consider edge {u}-{v} (weight={weight})",
                    node_states=dict(node_states),
                    edge_states=dict(edge_states),
                )

                in_tree.add(v)
                node_states[v] = NodeState.IN_RESULT
                edge_states[edge_key(u, v)] = EdgeState.IN_RESULT
                mst_edges.append((u, v))
                total_weight += weight

                for neighbor in graph.neighbors(v):
                    if neighbor not in in_tree:
                        neighbor_weight = graph[v][neighbor].get("weight", 1)
                        heapq.heappush(heap, (neighbor_weight, v, neighbor))

                index += 1
                yield AlgorithmStep(
                    index=index,
                    description=f"Accept edge {u}-{v}: adds {v} to the tree",
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
