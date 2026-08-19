from collections import defaultdict, deque
from typing import Any, Iterator

from .base import AlgorithmStep, Edge, EdgeState, GraphAlgorithm, Node, NodeState


class MaxFlowAlgorithm(GraphAlgorithm):
    """Dinic's max-flow algorithm, yielding one AlgorithmStep per BFS phase and augmenting path."""

    def __init__(self, graph, source: Node, sink: Node, **params: Any) -> None:
        super().__init__(graph, source=source, sink=sink, **params)
        self.source = source
        self.sink = sink

    def run(self) -> Iterator[AlgorithmStep]:
        graph = self.graph
        source = self.source
        sink = self.sink

        original_edges = list(graph.edges())
        edge_set = set(original_edges)

        def canonical(a: Node, b: Node) -> Edge:
            return (a, b) if (a, b) in edge_set else (b, a)

        edge_capacity: dict[Edge, float] = {}
        capacity: dict[Node, dict[Node, float]] = defaultdict(dict)
        for u, v, data in graph.edges(data=True):
            weight = data.get("weight", 1)
            edge_capacity[(u, v)] = weight
            capacity[u][v] = capacity[u].get(v, 0) + weight
            if graph.is_directed():
                capacity[v].setdefault(u, 0)
            else:
                capacity[v][u] = capacity[v].get(u, 0) + weight

        net_flow: dict[Edge, float] = {e: 0 for e in original_edges}

        def push_flow(a: Node, b: Node, amount: float) -> None:
            capacity[a][b] -= amount
            capacity[b][a] += amount
            key = canonical(a, b)
            if key == (a, b):
                net_flow[key] += amount
            else:
                net_flow[key] -= amount

        neighbors = {u: list(capacity[u].keys()) for u in graph.nodes}

        node_states = {node: NodeState.UNVISITED for node in graph.nodes}
        node_states[source] = NodeState.CURRENT
        node_states[sink] = NodeState.FRONTIER
        edge_states: dict[Edge, EdgeState] = {e: EdgeState.UNVISITED for e in original_edges}
        edge_labels: dict[Edge, Any] = {e: f"0/{edge_capacity[e]}" for e in original_edges}

        index = 0
        yield AlgorithmStep(
            index=index,
            description=f"Initialize residual capacities from edge weights (source={source}, sink={sink})",
            node_states=dict(node_states),
            edge_states=dict(edge_states),
            edge_labels=dict(edge_labels),
        )

        max_flow_value = 0.0
        phase = 0

        while source != sink:
            level = {node: -1 for node in graph.nodes}
            level[source] = 0
            queue = deque([source])
            while queue:
                u = queue.popleft()
                for v in neighbors[u]:
                    if capacity[u][v] > 1e-9 and level[v] == -1:
                        level[v] = level[u] + 1
                        queue.append(v)

            phase += 1
            for node in graph.nodes:
                if node == source:
                    node_states[node] = NodeState.CURRENT
                elif level[node] != -1:
                    node_states[node] = NodeState.FRONTIER if node == sink else NodeState.VISITED
                else:
                    node_states[node] = NodeState.UNVISITED

            index += 1
            if level[sink] == -1:
                yield AlgorithmStep(
                    index=index,
                    description=f"BFS phase {phase}: sink {sink} is unreachable, no augmenting path left",
                    node_states=dict(node_states),
                    edge_states=dict(edge_states),
                    edge_labels=dict(edge_labels),
                )
                break

            yield AlgorithmStep(
                index=index,
                description=f"BFS phase {phase}: build level graph from {source}, sink reached at level {level[sink]}",
                node_states=dict(node_states),
                edge_states=dict(edge_states),
                edge_labels=dict(edge_labels),
            )

            it: dict[Node, int] = defaultdict(int)

            while True:
                path = [source]
                found = False
                while path:
                    u = path[-1]
                    if u == sink:
                        found = True
                        break
                    advanced = False
                    while it[u] < len(neighbors[u]):
                        v = neighbors[u][it[u]]
                        if level.get(v, -1) == level[u] + 1 and capacity[u][v] > 1e-9:
                            path.append(v)
                            advanced = True
                            break
                        it[u] += 1
                    if not advanced:
                        level[u] = -1
                        path.pop()

                if not found:
                    break

                bottleneck = min(capacity[a][b] for a, b in zip(path, path[1:]))
                for a, b in zip(path, path[1:]):
                    push_flow(a, b, bottleneck)
                    key = canonical(a, b)
                    edge_labels[key] = f"{abs(net_flow[key])}/{edge_capacity[key]}"
                    if abs(net_flow[key]) >= edge_capacity[key] - 1e-9:
                        edge_states[key] = EdgeState.SATURATED
                    else:
                        edge_states[key] = EdgeState.CONSIDERING

                max_flow_value += bottleneck
                index += 1
                path_str = "-".join(str(n) for n in path)
                yield AlgorithmStep(
                    index=index,
                    description=f"Augment along {path_str}: push {bottleneck} units (total flow = {max_flow_value})",
                    node_states=dict(node_states),
                    edge_states=dict(edge_states),
                    edge_labels=dict(edge_labels),
                )

        final_node_states = dict(node_states)
        final_edge_states = dict(edge_states)
        for e in original_edges:
            if abs(net_flow[e]) > 1e-9:
                final_edge_states[e] = EdgeState.IN_RESULT
                final_node_states[e[0]] = NodeState.IN_RESULT
                final_node_states[e[1]] = NodeState.IN_RESULT
        final_node_states[source] = NodeState.CURRENT
        final_node_states[sink] = NodeState.FRONTIER

        index += 1
        yield AlgorithmStep(
            index=index,
            description=f"Done: max flow from {source} to {sink} = {max_flow_value}",
            node_states=final_node_states,
            edge_states=final_edge_states,
            edge_labels=dict(edge_labels),
            is_final=True,
            result={"max_flow": max_flow_value},
        )
