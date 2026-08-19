# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

An interactive graph-algorithm visualizer built with Streamlit, NetworkX, and Pyvis. The UI (`app.py`) is in Hebrew (RTL text), letting a user build a graph interactively (random Erdős–Rényi generation or manual edge entry) and select an algorithm — Dijkstra (shortest path), Kruskal (MST), Max Flow (Edmonds-Karp) — to run against it, rendered via Pyvis network graphs embedded in the Streamlit page.

The project is at an early/skeleton stage: `app.py` currently contains all logic inline (graph state in `st.session_state.G`, direct Pyvis rendering) and only picks the algorithm in the sidebar without yet dispatching to a real implementation. `graph_utils.py`, `visualization.py`, and every file under `algorithms/` (`base.py`, `diajkstra.py`, `kruskal.py`, `max_flow.py`, `bipartite_matching.py`) are currently empty placeholders being fleshed out.

Current focus: designing the **unified "algorithm step" contract** in `algorithms/base.py` — the shared interface each algorithm implementation will emit (e.g. one record per algorithm iteration) so the visualizer can render any algorithm's progress the same way, rather than each algorithm module building its own ad hoc output.

## Commands

Environment: a `venv/` (Python 3.14) already exists at the repo root.

```bash
source venv/bin/activate
pip install -r requirements.txt   # streamlit, networkx, pyvis, matplotlib, plotly, etc.

streamlit run app.py              # launch the app (default: http://localhost:8501)
```

No test suite, linter, or formatter is configured yet in this repo.

## Architecture notes

- **`app.py`** — Streamlit entry point. Owns UI layout and the graph's session state (`st.session_state.G`, an `nx.Graph`). Currently builds the Pyvis `Network` directly from `st.session_state.G` and renders it via a temp HTML file (`net.save_graph` → read back → `st.components.v1.html`).
- **`algorithms/`** — intended to hold one module per algorithm, each implementing the shared step contract defined in `base.py` so `app.py` can drive any algorithm through a common step/animate loop. Note `diajkstra.py` is misspelled (missing the interface plug-in for it doesn't exist yet in `app.py`).
- **`graph_utils.py`** — intended home for graph construction/manipulation helpers (currently empty; graph creation logic still lives inline in `app.py`).
- **`visualization.py`** — intended home for Pyvis rendering logic (currently empty; rendering still lives inline in `app.py`).

When implementing a new algorithm, conform to whatever step contract lands in `algorithms/base.py` rather than returning bespoke shapes per algorithm — the whole point of the contract is that `app.py`/`visualization.py` only need to know how to render one shape.
