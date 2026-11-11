# Graph Algorithms Visualizer

An interactive web app for watching classic graph algorithms run **step by step**.
Build a graph, pick an algorithm, and move through its execution one step at a time. Nodes and edges are colored by their current state (visiting, in the frontier, part of the result, rejected, and so on).

Built with **Python**, **Streamlit**, **NetworkX** and **Pyvis**.

🔗 **Live demo:** _add your Streamlit Cloud link here_

---

## Features

- **Build a graph:** generate a random weighted graph (Erdős–Rényi) or add edges by hand with custom weights.
- **Run an algorithm:** choose source/target/sink nodes where the algorithm needs them.
- **Step through execution:** use the "next step" button or the slider to move forward and back through the algorithm's progress.
- **See the result:** the final step shows the algorithm's output (path and distance, MST edges and total weight, max-flow value).

## Supported algorithms

| Algorithm | Problem | Step granularity |
|---|---|---|
| **Dijkstra** | Single-source shortest path (non-negative weights) | One step per node settled |
| **Bellman-Ford** | Single-source shortest path, detects negative cycles | One step per relaxation pass |
| **Kruskal** | Minimum spanning tree / forest (Union-Find) | One step per edge considered |
| **Prim** | Minimum spanning tree / forest (priority queue) | One step per edge considered |
| **Max Flow (Dinic)** | Maximum flow from source to sink (edge weights = capacities) | One step per BFS phase and augmenting path |

## Getting started

Requires Python 3.10+.

```bash
git clone https://github.com/OrenZauda/Graph-Visualizer.git
cd Graph-Visualizer

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
Graph-Visualizer/
├── app.py              # Streamlit UI: graph building, algorithm selection, step navigation
├── visualization.py    # Renders the graph and the current step with Pyvis
├── graph_utils.py      # Graph helper functions
└── algorithms/
    ├── base.py         # Shared step contract: AlgorithmStep, NodeState, EdgeState, GraphAlgorithm
    ├── diajkstra.py    # Dijkstra
    ├── bellman_ford.py # Bellman-Ford
    ├── kruskal.py      # Kruskal
    ├── prim.py         # Prim
    └── max_flow.py     # Dinic's max flow
```

## How it works

Every algorithm subclasses `GraphAlgorithm` (in `algorithms/base.py`) and implements `run()` as a **generator** that yields one `AlgorithmStep` at a time. Each step holds:

- a short `description` of what just happened
- `node_states` / `edge_states`: the state of each node and edge (e.g. `CURRENT`, `FRONTIER`, `VISITED`, `IN_RESULT`, `REJECTED`, `SATURATED`)
- `node_labels` / `edge_labels`: values to display (e.g. current distances, `flow/capacity`)
- on the last step, `is_final=True` and the algorithm's `result`

Because every algorithm returns the same step format, the UI and the renderer don't need any algorithm-specific code. Adding a new algorithm means writing one new `GraphAlgorithm` subclass and registering it in `app.py`. See [`algorithms/README.md`](algorithms/README.md) for details.
