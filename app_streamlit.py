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
st.title("📈 Generador y Visualizador de Grafos Dirigidos (Estilo CLRS)")

with st.sidebar:
    st.header("⚙️ Parámetros")
    n = st.slider("Número de nodos", min_value=8, max_value=16, value=10, step=1)
    modo = st.radio("Modo", options=["Aleatorio", "Manual"], horizontal=True)
    layout = st.selectbox("Layout", options=["Capas (layers)", "Kamada–Kawai", "Anclado izquierda/derecha"], index=0)
    scale = st.slider("Escala (solo Kamada–Kawai)", 0.5, 5.0, 2.5, 0.1)
    seed = st.number_input("Semilla aleatoria (opcional)", value=42, step=1)
    st.caption("🎲 La semilla hace reproducible el grafo.")
    
    st.divider()
    st.caption("💡 **Modo Aleatorio**: Genera un grafo por capas estilo CLRS")
    st.caption("✏️ **Modo Manual**: Genera base aleatoria y reescribe 3 aristas específicas")

nodos = [str(i) for i in range(n)]
c1, c2 = st.columns(2)
with c1:
    fuente = st.selectbox("Nodo fuente", options=nodos, index=0, key="fuente_select")
with c2:
    sumidero = st.selectbox("Nodo sumidero", options=nodos, index=len(nodos) - 1, key="sumidero_select")

if fuente == sumidero:
    st.error("⚠️ La fuente y el sumidero deben ser diferentes.")
    st.stop()

manual_edges: List[Tuple[str, str, int]] = []
if modo == "Manual":
    st.subheader("✏️ Aristas manuales (reescribir/agregar)")
    st.info("📝 En modo manual, se genera un grafo aleatorio base y luego se reescriben o agregan estas 3 aristas.")
    
    for i in range(3):
        a, b, c = st.columns([1, 1, 1])
        with a:
            u = st.selectbox(f"Inicio {i+1}", options=nodos, key=f"u_{i}")
        with b:
            v = st.selectbox(f"Destino {i+1}", options=nodos, key=f"v_{i}")
        with c:
            cap = st.number_input(f"Capacidad {i+1}", min_value=1, max_value=99, value=10, step=1, key=f"cap_{i}")
        
        if u == v:
            st.warning(f"⚠️ Arista {i+1}: origen y destino no pueden ser iguales.", icon="⚠️")
        elif u == fuente and v == sumidero:
            st.warning(f"⚠️ Arista {i+1}: no se permite conexión directa fuente→sumidero.", icon="⚠️")
        else:
            manual_edges.append((u, v, int(cap)))

gen = st.button("🚀 Generar / Actualizar grafo", type="primary")

if "G" not in st.session_state:
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))

if gen:
    # Generar grafo base aleatorio
    st.session_state.G = generar_grafo_aleatorio(n, fuente, sumidero, seed=int(seed))
    
    if modo == "Manual" and manual_edges:
        # Reescribir/agregar las aristas manuales
        for (u, v, cap) in manual_edges:
            if u != v and not (u == fuente and v == sumidero):
                add_or_update_edge_no_bidirectional(st.session_state.G, u, v, cap)
        
        # Aplicar constraints finales
        enforce_constraints(st.session_state.G, fuente, sumidero)
        st.success(f"✅ Grafo generado con {len(manual_edges)} aristas manuales aplicadas.")

G: nx.DiGraph = st.session_state.G

# ====== MÉTRICAS ======
rep = generar_reporte(G, fuente, sumidero)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("🔵 Nodos", rep["n_nodos"])
m2.metric("➡️ Aristas", rep["n_aristas"])
m3.metric("🔗 Conectado", "✅ Sí" if rep["conectado"] else "❌ No")
m4.metric("📤 Cap. saliente fuente", rep["cap_sal_f"])
m5.metric("📥 Cap. entrante sumidero", rep["cap_ent_s"])

# ====== VALIDACIONES ======
with st.expander("🔍 Validaciones de constraints"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if not rep['in_en_fuente']:
            st.success("✅ Sin entrantes a fuente")
        else:
            st.error(f"❌ Entrantes a fuente: {rep['in_en_fuente']}")
    
    with col2:
        if not rep['out_en_sumidero']:
            st.success("✅ Sin salientes de sumidero")
        else:
            st.error(f"❌ Salientes de sumidero: {rep['out_en_sumidero']}")
    
    with col3:
        if not rep['conflictos']:
            st.success("✅ Sin aristas bidireccionales")
        else:
            st.error(f"❌ Pares bidireccionales: {rep['conflictos']}")

# ====== TABLA DE ARISTAS ======
with st.expander("📋 Aristas (u → v) [capacidad]"):
    st.dataframe(
        [{"Origen (u)": u, "Destino (v)": v, "Capacidad": c} for (u, v, c) in rep["edges"]],
        use_container_width=True, 
        hide_index=True
    )

# ====== VISUALIZACIÓN ======
st.subheader("🎨 Visualización del Grafo")
fig = draw_graph(G, fuente, sumidero, layout=layout, scale=scale)
st.pyplot(fig, clear_figure=True)

st.caption("💡 **Tip**: Usa el layout 'Capas (layers)' para ver la estructura por niveles estilo CLRS.")
