import math
import os
import tempfile
from typing import Optional

import networkx as nx
from pyvis.network import Network

from algorithms.base import AlgorithmStep, EdgeState, NodeState

MIN_NODE_DISTANCE = 200
DISTANCE_LABEL_COLOR = "#2ecc71"
DISTANCE_LABEL_OFFSET = 48

NODE_COLORS = {
    NodeState.UNVISITED: "#97c2fc",
    NodeState.CURRENT: "#ffb703",
    NodeState.FRONTIER: "#8ecae6",
    NodeState.VISITED: "#adb5bd",
    NodeState.IN_RESULT: "#2a9d8f",
    NodeState.REJECTED: "#e63946",
}

EDGE_COLORS = {
    EdgeState.UNVISITED: "#848484",
    EdgeState.CONSIDERING: "#ffb703",
    EdgeState.IN_RESULT: "#2a9d8f",
    EdgeState.REJECTED: "#e63946",
    EdgeState.SATURATED: "#6a4c93",
}

EDGE_WIDTHS = {
    EdgeState.UNVISITED: 1,
    EdgeState.CONSIDERING: 2,
    EdgeState.IN_RESULT: 4,
    EdgeState.REJECTED: 1,
    EdgeState.SATURATED: 3,
}


def _compute_positions(graph: nx.Graph) -> dict:
    """Lay out nodes so that no two node circles overlap, regardless of graph size.
    Positions depend only on graph structure (not on the current step), so they stay
    fixed across an algorithm's animation."""
    n = max(graph.number_of_nodes(), 1)
    scale = 150 * math.sqrt(n)
    raw = nx.spring_layout(graph, seed=42, scale=scale)
    positions = {node: list(pos) for node, pos in raw.items()}

    nodes = list(positions)
    for _ in range(200):
        moved = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                dx = positions[b][0] - positions[a][0]
                dy = positions[b][1] - positions[a][1]
                dist = math.hypot(dx, dy)
                if dist < MIN_NODE_DISTANCE:
                    moved = True
                    if dist == 0:
                        dx, dy, dist = 1.0, 0.0, 1.0
                    push = (MIN_NODE_DISTANCE - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    positions[a][0] -= ux * push
                    positions[a][1] -= uy * push
                    positions[b][0] += ux * push
                    positions[b][1] += uy * push
        if not moved:
            break

    return positions


def build_network(graph: nx.Graph, step: Optional[AlgorithmStep] = None, height: str = "700px") -> Network:
    """Build a Pyvis Network from `graph`, optionally overlaying an AlgorithmStep's
    node/edge states and labels. With no step, everything renders as UNVISITED."""
    net = Network(height=height, width="100%", bgcolor="#222222", directed=graph.is_directed())

    positions = _compute_positions(graph)

    for node in graph.nodes:
        state = step.node_states.get(node, NodeState.UNVISITED) if step else NodeState.UNVISITED
        x, y = positions[node]
        net.add_node(
            node,
            label=str(node),
            color=NODE_COLORS[state],
            shape="circle",
            x=x,
            y=y,
            physics=False,
            font={"size": 30, "color": "white"},
        )

        if step and node in step.node_labels:
            net.add_node(
                f"__label_{node}",
                label=str(step.node_labels[node]),
                shape="text",
                x=x,
                y=y - DISTANCE_LABEL_OFFSET,
                physics=False,
                font={"size": 30, "color": DISTANCE_LABEL_COLOR},
            )

    for u, v, data in graph.edges(data=True):
        state = EdgeState.UNVISITED
        if step:
            state = step.edge_states.get((u, v), step.edge_states.get((v, u), EdgeState.UNVISITED))

        label = str(data["weight"]) if "weight" in data else ""
        if step:
            edge_label = step.edge_labels.get((u, v), step.edge_labels.get((v, u)))
            if edge_label is not None:
                label = str(edge_label)

        net.add_edge(
            u, v, label=label, color=EDGE_COLORS[state], width=EDGE_WIDTHS[state], font={"size": 30, "color": "white"}
        )

    return net


def render_html(graph: nx.Graph, step: Optional[AlgorithmStep] = None, height: str = "700px") -> str:
    """Render `graph` (with optional AlgorithmStep overlay) to a self-contained HTML string,
    suitable for st.components.v1.html()."""
    net = build_network(graph, step, height=height)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
    try:
        with open(tmp.name, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(tmp.name)
