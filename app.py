import random

import streamlit as st
import networkx as nx

from algorithms.bellman_ford import BellmanFordAlgorithm
from algorithms.diajkstra import DijkstraAlgorithm
from algorithms.kruskal import KruskalAlgorithm
from algorithms.max_flow import MaxFlowAlgorithm
from algorithms.prim import PrimAlgorithm
from visualization import render_html

st.set_page_config(page_title="Graph Visualizer", layout="wide")
st.title("🔍 ויזואליזר אינטראקטיבי לאלגוריתמים על גרפים")

ALGORITHMS = {
    "Dijkstra (Shortest Path)": DijkstraAlgorithm,
    "Bellman-Ford (Shortest Path)": BellmanFordAlgorithm,
    "Kruskal (MST)": KruskalAlgorithm,
    "Prim (MST)": PrimAlgorithm,
    "Max Flow (Dinic)": MaxFlowAlgorithm,
}

NEEDS_SOURCE_TARGET = {DijkstraAlgorithm, BellmanFordAlgorithm}
NEEDS_SOURCE_SINK = {MaxFlowAlgorithm}
NEEDS_SOURCE_ONLY = {PrimAlgorithm}

# Sidebar
st.sidebar.header("בקרת גרף")
algorithm_name = st.sidebar.selectbox("בחר אלגוריתם", list(ALGORITHMS.keys()))
algorithm_cls = ALGORITHMS[algorithm_name]


def reset_algorithm_steps():
    st.session_state.steps = None


# Session state לאחסון הגרף ומצב האלגוריתם
if "G" not in st.session_state:
    st.session_state.G = nx.Graph()
if "steps" not in st.session_state:
    st.session_state.steps = None
if st.session_state.get("last_algorithm") != algorithm_name:
    reset_algorithm_steps()
    st.session_state.last_algorithm = algorithm_name


col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("יצירת גרף")
    num_nodes = st.number_input("מספר קודקודים", min_value=2, max_value=50, value=12)
    if st.button("צור גרף אקראי"):
        G = nx.erdos_renyi_graph(num_nodes, 0.4, seed=42)
        for u, v in G.edges:
            G[u][v]["weight"] = random.randint(1, 10)
        st.session_state.G = G
        reset_algorithm_steps()
        st.success("גרף אקראי נוצר!")

    # אפשרות להוספת edges פשוטה
    node1 = st.text_input("Node 1", "A")
    node2 = st.text_input("Node 2", "B")
    weight = st.number_input("משקל (אופציונלי)", value=1)
    if st.button("הוסף קשת"):
        st.session_state.G.add_edge(node1, node2, weight=weight)
        reset_algorithm_steps()
        st.success(f"נוספה קשת {node1}-{node2}")

    nodes = list(st.session_state.G.nodes)

    st.subheader("הרצת אלגוריתם")
    if algorithm_cls is None:
        st.info(f"{algorithm_name} עדיין לא מומש.")
    elif not nodes:
        st.info("צריך גרף עם צמתים כדי להריץ אלגוריתם.")
    else:
        kwargs = {}
        if algorithm_cls in NEEDS_SOURCE_TARGET:
            source = st.selectbox("צומת מקור", nodes)
            target = st.selectbox("צומת יעד (אופציונלי)", ["(ללא)"] + nodes)
            kwargs = {"source": source, "target": None if target == "(ללא)" else target}
        elif algorithm_cls in NEEDS_SOURCE_SINK:
            source = st.selectbox("צומת מקור", nodes)
            sink = st.selectbox("צומת יעד", nodes, index=len(nodes) - 1)
            kwargs = {"source": source, "sink": sink}
        elif algorithm_cls in NEEDS_SOURCE_ONLY:
            source = st.selectbox("צומת התחלה", nodes)
            kwargs = {"source": source}

        if st.button("הרץ אלגוריתם"):
            algo = algorithm_cls(st.session_state.G, **kwargs)
            st.session_state.steps = list(algo.run())
            st.session_state.step_index = 0

current_step = None
with col2:
    st.subheader("ויזואליזציה")
    steps = st.session_state.steps
    if steps:
        step_index = st.session_state.get("step_index", 0)
        if st.button("לשלב הבא"):
            step_index = min(step_index + 1, len(steps) - 1)
        step_index = st.slider("שלב", 0, len(steps) - 1, step_index)
        st.session_state.step_index = step_index
        current_step = steps[step_index]
        st.write(current_step.description)
        if current_step.is_final and current_step.result is not None:
            st.json(current_step.result)

    if len(st.session_state.G.nodes) > 0:
        html_content = render_html(st.session_state.G, current_step)
        st.iframe(html_content, height=700)

# ריצה: streamlit run app.py
