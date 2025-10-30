# file: src/layouts.py
from typing import Dict
import networkx as nx
import matplotlib.pyplot as plt

def _pos_fixed_left_right(G: nx.DiGraph, fuente: str, sumidero: str) -> Dict[str, tuple]:
    pos0 = {fuente: (0.0, 0.0), sumidero: (1.0, 0.0)}
    return nx.spring_layout(G, pos=pos0, fixed=[fuente, sumidero], seed=42, iterations=100)

def _pos_layers_from_source(G: nx.DiGraph, fuente: str) -> Dict[str, tuple]:
    dist = nx.single_source_shortest_path_length(G, fuente)
    maxd = max(dist.values()) if dist else 0
    for n in G.nodes():
        G.nodes[n]["subset"] = dist.get(n, maxd + 1)
    pos = nx.multipartite_layout(G, subset_key="subset")
    xs = [p[0] for p in pos.values()]
    minx, maxx = min(xs), max(xs); span = (maxx - minx) or 1.0
    for k, (x, y) in pos.items():
        pos[k] = ((x - minx) / span, y)
    return pos

def _pos_kamada_kawai(G: nx.DiGraph, scale: float = 1.5) -> Dict[str, tuple]:
    return nx.kamada_kawai_layout(G, scale=scale)

def draw_graph(G: nx.DiGraph, fuente: str, sumidero: str, layout: str = "fixed", *, scale: float = 1.5):
    if layout == "Capas (layers)":
        pos = _pos_layers_from_source(G, fuente)
    elif layout == "Kamada–Kawai":
        pos = _pos_kamada_kawai(G, scale=scale)
    else:
        pos = _pos_fixed_left_right(G, fuente, sumidero)

    edge_labels = nx.get_edge_attributes(G, 'capacity')
    colores = ["lightgreen" if n == fuente else "salmon" if n == sumidero else "skyblue" for n in G.nodes()]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=120)
    nx.draw(G, pos, with_labels=True, node_size=700, node_color=colores,
            font_size=11, font_weight='bold', arrows=True, width=1.5, ax=ax)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, label_pos=0.5, ax=ax)
    ax.set_title(f"Grafo | Fuente: {fuente} • Sumidero: {sumidero}")
    ax.axis('off')
    return fig


