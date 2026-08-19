import heapq
from typing import Any, Iterator, Optional

from .base import AlgorithmStep, Edge, EdgeState, GraphAlgorithm, Node, NodeState


class DijkstraAlgorithm(GraphAlgorithm):
    """Dijkstra's shortest-path algorithm, yielding one AlgorithmStep per node settled."""

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
        visited: set[Node] = set()

        node_states = {node: NodeState.UNVISITED for node in graph.nodes}
        node_states[source] = NodeState.FRONTIER
        node_labels: dict[Node, Any] = {node: "∞" for node in graph.nodes}
        node_labels[source] = 0

        index = 0
        yield AlgorithmStep(
            index=index,
            description=f"Initialize: distance[{source}] = 0, all others = ∞",
            node_states=dict(node_states),
            node_labels=dict(node_labels),
        )

        queue: list[tuple[float, Node]] = [(0, source)]

        while queue:
            dist, current = heapq.heappop(queue)
            if current in visited:
                continue
            visited.add(current)
            node_states[current] = NodeState.CURRENT
            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Visit {current} (distance = {dist})",
                node_states=dict(node_states),
                node_labels=dict(node_labels),
            )

            if current == target:
                break

            edge_states: dict[Edge, EdgeState] = {}
            for neighbor in graph.neighbors(current):
                if neighbor in visited:
                    continue
                weight = graph[current][neighbor].get("weight", 1)
                edge_states[(current, neighbor)] = EdgeState.CONSIDERING
                new_dist = dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    predecessors[neighbor] = current
                    node_labels[neighbor] = new_dist
                    node_states[neighbor] = NodeState.FRONTIER
                    heapq.heappush(queue, (new_dist, neighbor))

            node_states[current] = NodeState.VISITED
            index += 1
            yield AlgorithmStep(
                index=index,
                description=f"Relax edges from {current}",
                node_states=dict(node_states),
                edge_states=dict(edge_states),
                node_labels=dict(node_labels),
            )

        has_path_to_target = target is not None and (target == source or target in predecessors)

        path_edges: set[Edge] = set()
        result: Any
        if has_path_to_target:
            path = [target]
            while path[-1] != source:
                path.append(predecessors[path[-1]])
            path.reverse()
            path_edges = {(path[i], path[i + 1]) for i in range(len(path) - 1)}
            result = {"path": path, "distance": distances[target]}
        else:
            result = {"distances": distances}

        final_node_states = dict(node_states)
        final_edge_states: dict[Edge, EdgeState] = {}
        for u, v in path_edges:
            final_node_states[u] = NodeState.IN_RESULT
            final_node_states[v] = NodeState.IN_RESULT
            final_edge_states[(u, v)] = EdgeState.IN_RESULT

        index += 1
        yield AlgorithmStep(
            index=index,
            description=(
                f"Done: shortest path to {target} found"
                if has_path_to_target
                else "Done: all shortest distances computed"
            ),
            node_states=final_node_states,
            edge_states=final_edge_states,
            node_labels=dict(node_labels),
            is_final=True,
            result=result,
        )
