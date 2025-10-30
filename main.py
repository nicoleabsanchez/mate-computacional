# file: app_streamlit.py
"""
App Streamlit para generar y visualizar un grafo dirigido con capacidades.
Ejecuta:  streamlit run app_streamlit.py
Requisitos: pip install streamlit networkx matplotlib
"""

from __future__ import annotations
import random
from typing import Tuple, Optional, List, Dict

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

# ---------------- Utilidades núcleo (reusadas) ----------------

def add_or_update_edge_no_bidirectional(G: nx.DiGraph, u: str, v: str, capacity: int) -> None:
    """Evita bucles y bidireccionalidad; sobrescribe capacidad si existe."""
    if u == v:
        return
    if G.has_edge(v, u):
        G.remove_edge(v, u)
    if G.has_edge(u, v):
        G[u][v]["capacity"] = capacity
    else:
        G.add_edge(u, v, capacity=capacity)

def enforce_constraints(G: nx.DiGraph, fuente: str, sumidero: str) -> None:
    """Sin fuente←*, sin sumidero→*, sin fuente→sumidero, sin pares bidireccionales."""
    if G.has_edge(fuente, sumidero):
        G.remove_edge(fuente, sumidero)
    for u in list(G.predecessors(fuente)):
        G.remove_edge(u, fuente)
    for v in list(G.successors(sumidero)):
        G.remove_edge(sumidero, v)
    for u, v in nx.Graph(G).edges():
        if G.has_edge(u, v) and G.has_edge(v, u):
            G.remove_edge(v, u)

def _pares_bidireccionales(G: nx.DiGraph) -> List[Tuple[str, str]]:
    pares = []
    for u, v in nx.Graph(G).edges():
        if G.has_edge(u, v) and G.has_edge(v, u):
            pares.append((u, v))
    return pares

def generar_reporte(G: nx.DiGraph, fuente: str, sumidero: str) -> Dict[str, object]:
    conectado = nx.has_path(G, fuente, sumidero)
    in_f = G.in_degree(fuente); out_f = G.out_degree(fuente)
    in_s = G.in_degree(sumidero); out_s = G.out_degree(sumidero)
    cap_sal_f = sum(G[u][v].get("capacity", 0) for u, v in G.out_edges(fuente))
    cap_ent_s = sum(G[u][v].get("capacity", 0) for u, v in G.in_edges(sumidero))
    conflictos = _pares_bidireccionales(G)
    tiene_in_en_fuente = list(G.in_edges(fuente))
    tiene_out_en_sumidero = list(G.out_edges(sumidero))
    edges_list = [(u, v, d.get("capacity", 0)) for u, v, d in G.edges(data=True)]
    edges_list.sort(key=lambda e: (int(e[0]), int(e[1])))
    return {
        "n_nodos": G.number_of_nodes(),
        "n_aristas": G.number_of_edges(),
        "conectado": conectado,
        "in_f": in_f, "out_f": out_f, "in_s": in_s, "out_s": out_s,
        "cap_sal_f": cap_sal_f, "cap_ent_s": cap_ent_s,
        "conflictos": conflictos,
        "in_en_fuente": tiene_in_en_fuente,
        "out_en_sumidero": tiene_out_en_sumidero,
        "edges": edges_list,
    }

def generar_grafo_aleatorio(n: int, fuente: str, sumidero: str, seed: int | None = None) -> nx.DiGraph:
    if seed is not None:
        random.seed(seed)
    G = nx.DiGraph()
    G.add_nodes_from([str(i) for i in range(n)])

    # 3 salientes desde la fuente
    for _ in range(3):
        destino = str(random.choice([i for i in range(1, n-1)]))
        add_or_update_edge_no_bidirectional(G, fuente, destino, random.randint(4, 15))
    # 3 entrantes al sumidero
    for _ in range(3):
        origen = str(random.choice([i for i in range(0, n-1)]))
        add_or_update_edge_no_bidirectional(G, origen, sumidero, random.randint(4, 15))
    # Entre intermedios
    for node in range(1, n-1):
        # Forzamos 1 entrante y 1 saliente para conectividad básica
        origen = str(random.choice([i for i in range(0, n-1) if i != node and str(i) != fuente]))
        add_or_update_edge_no_bidirectional(G, origen, str(node), random.randint(4, 15))
        destino = str(random.choice([i for i in range(0, n-1) if i != node and str(i) != sumidero]))
        add_or_update_edge_no_bidirectional(G, str(node), destino, random.randint(4, 15))

    enforce_constraints(G, fuente, sumidero)
    return G

# ---------------- Posicionamiento (izquierda/derecha) ----------------

def _pos_fixed_left_right(G: nx.DiGraph, fuente: str, sumidero: str) -> Dict[str, tuple]:
    """Ancla fuente (x≈0) y sumidero (x≈1); spring_layout para el resto."""
    pos0 = {fuente: (0.0, 0.0), sumidero: (1.0, 0.0)}
    return nx.spring_layout(G, pos=pos0, fixed=[fuente, sumidero], seed=42, iterations=100)

def _pos_layers_from_source(G: nx.DiGraph, fuente: str) -> Dict[str, tuple]:
    """Capas por distancia dirigida desde la fuente (multipartite_layout)."""
    dist = nx.single_source_shortest_path_length(G, fuente)
    maxd = max(dist.values()) if dist else 0
    for n in G.nodes():
        G.nodes[n]["subset"] = dist.get(n, maxd + 1)
    pos = nx.multipartite_layout(G, subset_key="subset")  # capas en eje X
    xs = [p[0] for p in pos.values()]
    minx, maxx = min(xs), max(xs)
    span = (maxx - minx) or 1.0
    for k in pos:
        x, y = pos[k]
        pos[k] = ((x - minx) / span, y)
    return pos

def _draw_graph(G: nx.DiGraph, fuente: str, sumidero: str, layout: str):
    if layout == "Capas (layers)":
        pos = _pos_layers_from_source(G, fuente)
    else:
        pos = _pos_fixed_left_right(G, fuente, sumidero)

    edge_labels = nx.get_edge_attributes(G, 'capacity')
    colores = []
    for n in G.nodes():
        if n == fuente: colores.append('lightgreen')   # por visibilidad de roles
        elif n == sumidero: colores.append('salmon')
        else: colores.append('skyblue')

    fig, ax = plt.subplots(figsize=(9, 6), dpi=120)
    nx.draw(G, pos, with_labels=True, node_size=700, node_color=colores,
            font_size=11, font_weight='bold', arrows=True, width=1.5, ax=ax)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, label_pos=0.5, ax=ax)
    ax.set_title(f"Grafo | Fuente: {fuente} • Sumidero: {sumidero}")
    ax.axis('off')
    st.pyplot(fig, clear_figure=True)

# ---------------- UI (Streamlit) ----------------

st.set_page_config(page_title="Grafo con Capacidades", page_icon="📈", layout="wide")
st.title("📈 Generador y Visualizador de Grafos Dirigidos")

with st.sidebar:
    st.header("⚙️ Parámetros")
    n = st.slider("Número de nodos", min_value=8, max_value=16, value=10, step=1)
    modo = st.radio("Modo", options=["Aleatorio", "Manual"], horizontal=True)
    layout = st.selectbox("Layout", options=["Anclado izquierda/derecha", "Capas (layers)"], index=0)
    seed = st.number_input("Semilla aleatoria (opcional)", value=42, step=1)
    st.caption("La semilla hace reproducible el grafo.")

nodos = [str(i) for i in range(n)]
col_fs1, col_fs2 = st.columns(2)
with col_fs1:
    fuente = st.selectbox("Nodo fuente", options=nodos, index=0, key="fuente_select")
with col_fs2:
    sumidero = st.selectbox("Nodo sumidero", options=nodos, index=len(nodos) - 1, key="sumidero_select")

if fuente == sumidero:
    st.error("La fuente y el sumidero deben ser diferentes.")

# Aristas manuales (3)
manual_edges: List[Tuple[str, str, int]] = []
if modo == "Manual":
    st.subheader("➕ Aristas manuales (3)")
    st.caption("No se permiten aristas que involucren fuente/sumidero; capacidad > 0.")
    for i in range(3):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            u = st.selectbox(f"Inicio {i+1}", options=[x for x in nodos if x not in (fuente, sumidero)],
                             key=f"u_{i}")
        with c2:
            v = st.selectbox(f"Destino {i+1}", options=[x for x in nodos if x not in (fuente, sumidero)],
                             key=f"v_{i}")
        with c3:
            cap = st.number_input(f"Capacidad {i+1}", min_value=1, max_value=99, value=10, step=1, key=f"cap_{i}")
        if u != v:
            manual_edges.append((u, v, cap))
        else:
            st.warning(f"Arista {i+1}: u y v no pueden ser iguales.", icon="⚠️")

# Botón generar/actualizar
gen = st.button("🚀 Generar / Actualizar grafo")

# Estado persistente
if "G" not in st.session_state:
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))

if gen:
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))
    if modo == "Manual":
        for (u, v, cap) in manual_edges:
            if (u in (fuente, sumidero)) or (v in (fuente, sumidero)):
                continue
            add_or_update_edge_no_bidirectional(st.session_state.G, u, v, int(cap))
        enforce_constraints(st.session_state.G, fuente, sumidero)

G: nx.DiGraph = st.session_state.G

# Reporte
rep = generar_reporte(G, fuente, sumidero)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Nodos", rep["n_nodos"])
m2.metric("Aristas", rep["n_aristas"])
m3.metric("Conectado fuente→sumidero", "Sí" if rep["conectado"] else "No")
m4.metric("Cap. saliente fuente", rep["cap_sal_f"])
m5.metric("Cap. entrante sumidero", rep["cap_ent_s"])

with st.expander("Validaciones de constraints"):
    st.write(f"- Entrantes a fuente: {'OK' if not rep['in_en_fuente'] else '❌ ' + str(rep['in_en_fuente'])}")
    st.write(f"- Salientes de sumidero: {'OK' if not rep['out_en_sumidero'] else '❌ ' + str(rep['out_en_sumidero'])}")
    st.write(f"- Pares bidireccionales: {'OK' if not rep['conflictos'] else '❌ ' + str(rep['conflictos'])}")

with st.expander("Aristas (u → v) [capacidad]"):
    st.dataframe(
        [{"u": u, "v": v, "capacidad": c} for (u, v, c) in rep["edges"]],
        use_container_width=True, hide_index=True
    )

st.subheader("🔍 Visualización")
_draw_graph(G, fuente, sumidero, layout)

st.caption("Tip: Cambia la semilla y el layout para explorar distintas configuraciones.")
# --- END OF FILE ---