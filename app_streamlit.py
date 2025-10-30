# file: app_streamlit.py
"""
App Streamlit para generar y visualizar un grafo dirigido con capacidades.
Ejecuta:  streamlit run app_streamlit.py
"""
from typing import List, Tuple
import streamlit as st
import networkx as nx

from src.graph_core import (
    add_or_update_edge_no_bidirectional,
    enforce_constraints,
    generar_reporte,
    generar_grafo_aleatorio,
)
from src.layouts import draw_graph

st.set_page_config(page_title="Grafo con Capacidades", page_icon="📈", layout="wide")
st.title("📈 Generador y Visualizador de Grafos Dirigidos")

with st.sidebar:
    st.header("⚙️ Parámetros")
    n = st.slider("Número de nodos", min_value=8, max_value=16, value=10, step=1)
    modo = st.radio("Modo", options=["Aleatorio", "Manual"], horizontal=True)
    layout = st.selectbox("Layout", options=["Anclado izquierda/derecha", "Capas (layers)", "Kamada–Kawai"], index=2)
    scale = st.slider("Escala (solo Kamada–Kawai)", 0.5, 5.0, 2.0, 0.1)
    seed = st.number_input("Semilla aleatoria (opcional)", value=42, step=1)
    st.caption("La semilla hace reproducible el grafo.")

nodos = [str(i) for i in range(n)]
c1, c2 = st.columns(2)
with c1:
    fuente = st.selectbox("Nodo fuente", options=nodos, index=0, key="fuente_select")
with c2:
    sumidero = st.selectbox("Nodo sumidero", options=nodos, index=len(nodos) - 1, key="sumidero_select")

if fuente == sumidero:
    st.error("La fuente y el sumidero deben ser diferentes.")

manual_edges: List[Tuple[str, str, int]] = []
if modo == "Manual":
    st.subheader("➕ Aristas manuales (3)")
    st.caption("No se permiten aristas que involucren fuente/sumidero; capacidad > 0.")
    for i in range(3):
        a, b, c = st.columns([1, 1, 1])
        with a:
            u = st.selectbox(f"Inicio {i+1}", options=[x for x in nodos if x not in (fuente, sumidero)], key=f"u_{i}")
        with b:
            v = st.selectbox(f"Destino {i+1}", options=[x for x in nodos if x not in (fuente, sumidero)], key=f"v_{i}")
        with c:
            cap = st.number_input(f"Capacidad {i+1}", min_value=1, max_value=99, value=10, step=1, key=f"cap_{i}")
        if u != v:
            manual_edges.append((u, v, int(cap)))
        else:
            st.warning(f"Arista {i+1}: u y v no pueden ser iguales.", icon="⚠️")

gen = st.button("🚀 Generar / Actualizar grafo")

if "G" not in st.session_state:
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))

if gen:
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))
    if modo == "Manual":
        for (u, v, cap) in manual_edges:
            if (u in (fuente, sumidero)) or (v in (fuente, sumidero)):
                continue
            add_or_update_edge_no_bidirectional(st.session_state.G, u, v, cap)
        enforce_constraints(st.session_state.G, fuente, sumidero)

G: nx.DiGraph = st.session_state.G

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
    st.dataframe([{"u": u, "v": v, "capacidad": c} for (u, v, c) in rep["edges"]],
                 use_container_width=True, hide_index=True)

st.subheader("🔍 Visualización")
fig = draw_graph(G, fuente, sumidero, layout=layout, scale=scale)
st.pyplot(fig, clear_figure=True)

st.caption("Tip: Usa Kamada–Kawai con mayor 'Escala' para abrir el grafo cuando haya muchos nodos.")

