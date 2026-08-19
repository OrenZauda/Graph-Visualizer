from typing import Any, Iterator, Optional

from .base import AlgorithmStep, Edge, EdgeState, GraphAlgorithm, Node, NodeState


def _extract_cycle(start: Node, predecessors: dict[Node, Node]) -> Optional[list[Node]]:
    """Walk predecessor pointers from `start` back to itself.

    Returns the cycle's nodes, or None if the chain doesn't close within the walk
    (shouldn't happen once `start` has been confirmed to sit on a cycle).
    """
    cycle = [start]
    node = predecessors.get(start)
    while node is not None and node != start:
        if node in cycle:
            return None
        cycle.append(node)
        node = predecessors.get(node)
    return cycle if node == start else None


class BellmanFordAlgorithm(GraphAlgorithm):
    """Bellman-Ford shortest-path algorithm, yielding one AlgorithmStep per relaxation pass.

    Unlike Dijkstra, this tolerates negative edge weights and can detect a negative cycle
    reachable from the source.
    """

    def __init__(self, graph, source: Node, target: Optional[Node] = None, **params: Any) -> None:
        super().__init__(graph, source=source, target=target, **params)
        self.source = source
        self.target = target

    def run(self) -> Iterator[AlgorithmStep]:
        graph = self.graph
        source = self.source
        target = self.target

        distances: dict[Node, float] = {node: float("inf") for node in graph.nodes}
        distances[source] = 0
        predecessors: dict[Node, Node] = {}

        node_states = {node: NodeState.UNVISITED for node in graph.nodes}
        node_states[source] = NodeState.FRONTIER
        node_labels: dict[Node, Any] = {node: "∞" for node in graph.nodes}
        node_labels[source] = 0

        directed_edges: list[tuple[Node, Node, float]] = []
        for u, v, data in graph.edges(data=True):
            weight = data.get("weight", 1)
            directed_edges.append((u, v, weight))
            if not graph.is_directed():
                directed_edges.append((v, u, weight))

        index = 0
        yield AlgorithmStep(
            index=index,
            description=f"Initialize: distance[{source}] = 0, all others = ∞",
            node_states=dict(node_states),
            node_labels=dict(node_labels),
        )

        num_nodes = graph.number_of_nodes()

        for iteration in range(1, num_nodes):
            edge_states: dict[Edge, EdgeState] = {}
            any_update = False
            for u, v, weight in directed_edges:
                # An undirected edge is stored as two opposite directed edges (see
                # above). Relaxing v via u right after u's own distance was set by
                # this very edge (from v) would just walk back over it — that's not
                # a real path, so don't let it masquerade as one.
                if not graph.is_directed() and predecessors.get(u) == v:
                    continue
                edge_states[(u, v)] = EdgeState.CONSIDERING
                if distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    predecessors[v] = u
                    node_labels[v] = distances[v]
                    node_states[v] = NodeState.FRONTIER
                    any_update = True

            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Pass {iteration}: relax all edges" + ("" if any_update else " (no changes)"),
                node_states=dict(node_states),
                edge_states=dict(edge_states),
                node_labels=dict(node_labels),
            )

            if not any_update:
                break

        # A node still relaxable after num_nodes - 1 passes sits on (or downstream of) a
        # negative cycle reachable from source. Reconstruct the actual cycle from
        # predecessor pointers instead of trusting a single relaxable edge: an undirected
        # edge is stored as two opposite directed edges (see above), so bouncing back and
        # forth across ONE edge would otherwise look like a valid 2-node cycle. A real
        # cycle needs at least 3 distinct nodes when the graph is undirected — 2 would mean
        # reusing that same edge twice, not a genuine cycle.
        cycle_nodes: set[Node] = set()
        for u, v, weight in directed_edges:
            if distances[u] + weight >= distances[v] - 1e-9:
                continue

            probe_predecessors = dict(predecessors)
            probe_predecessors[v] = u

            start = v
            for _ in range(num_nodes):
                start = probe_predecessors.get(start, start)

            cycle = _extract_cycle(start, probe_predecessors)
            if cycle and (graph.is_directed() or len(cycle) >= 3):
                cycle_nodes.update(cycle)

        negative_cycle = bool(cycle_nodes)

        affected: set[Node] = set()
        if negative_cycle:
            adjacency: dict[Node, list[Node]] = {}
            for u, v, _ in directed_edges:
                adjacency.setdefault(u, []).append(v)

            affected = set(cycle_nodes)
            queue = list(cycle_nodes)
            while queue:
                u = queue.pop()
                for v in adjacency.get(u, []):
                    if v not in affected:
                        affected.add(v)
                        queue.append(v)

            for node in affected:
                distances[node] = float("-inf")
                node_labels[node] = "-∞"
                node_states[node] = NodeState.REJECTED

            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Negative cycle detected: distance is -∞ for {sorted(affected, key=str)}",
                node_states=dict(node_states),
                node_labels=dict(node_labels),
                result={"negative_cycle": True, "affected_nodes": sorted(affected, key=str)},
            )

        has_path_to_target = (
            target is not None
            and target not in affected
            and (target == source or target in predecessors)
        )
        target_affected = target is not None and target in affected

        path_edges: set[Edge] = set()
        result: Any
        if has_path_to_target:
            path = [target]
            while path[-1] != source:
                path.append(predecessors[path[-1]])
            path.reverse()
            path_edges = {(path[i], path[i + 1]) for i in range(len(path) - 1)}
            result = {"path": path, "distance": distances[target]}
        elif target_affected:
            result = {"path": None, "distance": float("-inf"), "negative_cycle": True}
        else:
            result = {"distances": distances}
            if negative_cycle:
                result["negative_cycle"] = True

        final_node_states = dict(node_states)
        final_edge_states: dict[Edge, EdgeState] = {}
        for u, v in path_edges:
            final_node_states[u] = NodeState.IN_RESULT
            final_node_states[v] = NodeState.IN_RESULT
            final_edge_states[(u, v)] = EdgeState.IN_RESULT

        if has_path_to_target:
            description = f"Done: shortest path to {target} found"
        elif target_affected:
            description = f"Done: {target} is reachable from a negative cycle — distance is -∞"
        else:
            description = "Done: all shortest distances computed"

        index += 1
        yield AlgorithmStep(
            index=index,
            description=description,
            node_states=final_node_states,
            edge_states=final_edge_states,
            node_labels=dict(node_labels),
            is_final=True,
            result=result,
        )
