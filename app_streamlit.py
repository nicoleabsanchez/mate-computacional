# file: app_streamlit.py
"""
App Streamlit para generar y visualizar un grafo dirigido con capacidades.
Ejecuta:  streamlit run app_streamlit.py
"""
from typing import List, Tuple
import streamlit as st
import networkx as nx
import pandas as pd

from src.graph_core import (
    add_or_update_edge_no_bidirectional,
    enforce_constraints,
    generar_reporte,
    generar_grafo_aleatorio,
)
from src.layouts import draw_graph, draw_graph_with_min_cut
from src.ford_fulkerson import calcular_flujo_maximo

st.set_page_config(page_title="Problema del Flujo Máximo", page_icon="📈", layout="wide")
st.title("Problema del Flujo Máximo")

with st.sidebar:
    st.header("⚙️ Parámetros")
    n = st.slider("Número de nodos", min_value=8, max_value=16, value=10, step=1)
    modo = st.radio("Modo", options=["Aleatorio", "Manual"], horizontal=True)
    
    # Valores fijos (no modificables por el usuario)
    layout = "Capas (layers)"  # Fijo
    scale = 2.5  # Fijo
    seed = 42  # Fijo
    
    st.divider()
    st.caption("💡 **Modo Aleatorio**")
    st.caption("✏️ **Modo Manual**")

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
    st.subheader("✏️ Aristas manuales")
    
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

# ====== FORD-FULKERSON ======
st.divider()
st.header("🌊 Análisis de Flujo Máximo (Ford-Fulkerson)")

if rep["conectado"]:
    # Calcular flujo máximo
    ff = calcular_flujo_maximo(G, fuente, sumidero)
    summary = ff.get_summary()
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Flujo Máximo", summary['flujo_maximo'], 
                  help="Cantidad máxima de flujo que puede pasar de la fuente al sumidero")
    with col2:
        st.metric("🔴 Aristas Saturadas", f"{summary['aristas_saturadas']}/{summary['total_aristas']}", 
                  help="Aristas que están utilizando su capacidad máxima")
    with col3:
        st.metric("📊 Eficiencia Fuente", summary['eficiencia_fuente'], 
                  help="Porcentaje de capacidad de salida utilizada")
    with col4:
        st.metric("🔄 Caminos Aumentantes", summary['caminos_aumentantes'], 
                  help="Número de caminos encontrados por el algoritmo")
    
    # ====== TEOREMA DEL CORTE MÍNIMO ======
    st.divider()
    st.header("✂️ Teorema del Corte Mínimo (Max-Flow Min-Cut)")
    
    min_cut_info = ff.get_min_cut_info()
    
    st.info(f"""
    **Teorema de Ford-Fulkerson (1956)**: El valor del flujo máximo es igual a la capacidad del corte mínimo.
    
    - **Flujo Máximo**: {summary['flujo_maximo']} unidades
    - **Capacidad del Corte Mínimo**: {min_cut_info['capacidad_corte']} unidades
    - ✅ **Verificación**: Flujo Máximo = Capacidad del Corte Mínimo
    """)
    
    # Mostrar grupos del corte
    col_s, col_t = st.columns(2)
    
    with col_s:
        st.subheader("🔵 Grupo S (Lado de la Fuente)")
        st.write(f"**Nodos ({min_cut_info['num_nodos_S']}):**")
        st.code(", ".join(min_cut_info['grupo_S']))
        st.caption("Nodos alcanzables desde la fuente en el grafo residual")
    
    with col_t:
        st.subheader("🟠 Grupo T (Lado del Sumidero)")
        st.write(f"**Nodos ({min_cut_info['num_nodos_T']}):**")
        st.code(", ".join(min_cut_info['grupo_T']))
        st.caption("Nodos NO alcanzables desde la fuente en el grafo residual")
    
    # Aristas del corte
    st.subheader("✂️ Aristas del Corte Mínimo")
    st.write(f"**Total: {len(min_cut_info['aristas_corte'])} aristas | Capacidad total: {min_cut_info['capacidad_corte']} unidades**")
    
    cut_edges_data = []
    for u, v in min_cut_info['aristas_corte']:
        cap = G[u][v].get('capacity', 0)
        flow = ff.flow.get((u, v), 0)
        cut_edges_data.append({
            'Origen (S)': u,
            'Destino (T)': v,
            'Capacidad': cap,
            'Flujo': flow,
            'Estado': '🔴 Saturada' if flow == cap else '⚪ Parcial'
        })
    
    if cut_edges_data:
        df_cut = pd.DataFrame(cut_edges_data)
        st.dataframe(df_cut, use_container_width=True, hide_index=True)
    
    st.caption("💡 **Nota**: Las aristas del corte son aquellas que van del Grupo S al Grupo T. Estas aristas determinan el cuello de botella de la red.")
    
    # Detalles de flujo por arista
    st.divider()
    st.subheader("📋 Flujo por Arista")
    flow_details = ff.get_flow_details()
    df_flow = pd.DataFrame(flow_details)
    
    st.dataframe(
        df_flow,
        use_container_width=True,
        hide_index=True,
        column_config={
            "origen": st.column_config.TextColumn("Origen (u)", width="small"),
            "destino": st.column_config.TextColumn("Destino (v)", width="small"),
            "capacidad": st.column_config.NumberColumn("Capacidad", width="small"),
            "flujo": st.column_config.NumberColumn("Flujo", width="small"),
            "residual": st.column_config.NumberColumn("Residual", width="small"),
            "utilizacion": st.column_config.TextColumn("Utilización", width="small"),
            "saturada": st.column_config.TextColumn("Saturada", width="small"),
            "corte": st.column_config.TextColumn("Corte", width="small"),
        }
    )
    
    # Caminos aumentantes
    with st.expander("🛤️ Caminos Aumentantes Encontrados"):
        paths = ff.get_augmenting_paths()
        if paths:
            for path in paths:
                st.text(path)
        else:
            st.info("No se encontraron caminos aumentantes (el grafo ya está en flujo máximo)")
    
else:
    st.warning("⚠️ No se puede calcular el flujo máximo porque no hay conexión entre fuente y sumidero.")

# ====== VALIDACIONES ======
st.divider()
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
st.divider()
st.header("🎨 Visualización del Grafo")

# Grafo original (sin corte)
st.subheader("📊 Grafo Original")
fig1 = draw_graph(G, fuente, sumidero, layout=layout, scale=scale)
st.pyplot(fig1, clear_figure=True)

# Grafo con corte mínimo (si hay conexión)
if rep["conectado"]:
    st.divider()
    st.subheader("✂️ Grafo con Corte Mínimo")
    st.caption("🔴 **Aristas rojas gruesas**: Aristas del corte mínimo | 🔵 **Grupo S**: Nodos azules | 🟠 **Grupo T**: Nodos naranjas")
    
    min_cut_info = ff.get_min_cut_info()
    fig2 = draw_graph_with_min_cut(
        G, 
        fuente, 
        sumidero, 
        set(min_cut_info['grupo_S']),
        set(min_cut_info['grupo_T']),
        min_cut_info['aristas_corte'],
        layout=layout, 
        scale=scale
    )
    st.pyplot(fig2, clear_figure=True)
    
    st.success(f"""
    ✅ **Interpretación del Corte**:
    - La línea roja punteada divide el grafo en dos grupos
    - **Grupo S** ({min_cut_info['num_nodos_S']} nodos): Contiene la fuente y todos los nodos alcanzables desde ella
    - **Grupo T** ({min_cut_info['num_nodos_T']} nodos): Contiene el sumidero y los nodos no alcanzables
    - Las **{len(min_cut_info['aristas_corte'])} aristas rojas** representan el cuello de botella de la red
    - La capacidad total del corte ({min_cut_info['capacidad_corte']}) es igual al flujo máximo ({summary['flujo_maximo']})
    """)
