# file: src/layouts.py
from typing import Dict, List
import networkx as nx
import matplotlib.pyplot as plt

def _pos_fixed_left_right(G: nx.DiGraph, fuente: str, sumidero: str) -> Dict[str, tuple]:
    pos0 = {fuente: (0.0, 0.0), sumidero: (1.0, 0.0)}
    return nx.spring_layout(G, pos=pos0, fixed=[fuente, sumidero], seed=42, iterations=100)

def _pos_layers_from_source(G: nx.DiGraph, fuente: str, sumidero: str) -> Dict[str, tuple]:
    """
    Layout estilo CLRS con capas bien definidas basadas en distancia desde fuente.
    """
    try:
        dist = nx.single_source_shortest_path_length(G, fuente)
    except:
        dist = {fuente: 0}
    
    # Organizar nodos por capa
    layers: Dict[int, List[str]] = {}
    max_dist = 0
    
    for node in G.nodes():
        if node == fuente:
            layer = 0
        elif node == sumidero:
            continue
        else:
            layer = dist.get(node, max_dist + 1)
        
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(node)
        max_dist = max(max_dist, layer)
    
    # Sumidero en la última capa
    final_layer = max_dist + 1
    layers[final_layer] = [sumidero]
    
    # Crear posiciones
    pos = {}
    x_spacing = 2.5  # Espaciado horizontal
    y_spacing = 1.8  # Espaciado vertical
    
    for layer_num in sorted(layers.keys()):
        nodes_in_layer = layers[layer_num]
        num_nodes = len(nodes_in_layer)
        
        x = layer_num * x_spacing
        
        if num_nodes == 1:
            y_positions = [0.0]
        else:
            total_height = (num_nodes - 1) * y_spacing
            y_positions = [i * y_spacing - total_height / 2 for i in range(num_nodes)]
        
        for node, y in zip(nodes_in_layer, y_positions):
            pos[node] = (x, y)
    
    return pos

def _pos_kamada_kawai(G: nx.DiGraph, scale: float = 1.5) -> Dict[str, tuple]:
    return nx.kamada_kawai_layout(G, scale=scale)

def draw_graph(G: nx.DiGraph, fuente: str, sumidero: str, layout: str = "Capas (layers)", *, scale: float = 1.5):
    """
    Dibuja el grafo con estilo CLRS mejorado.
    """
    if layout == "Capas (layers)":
        pos = _pos_layers_from_source(G, fuente, sumidero)
    elif layout == "Kamada–Kawai":
        pos = _pos_kamada_kawai(G, scale=scale)
    else:
        pos = _pos_fixed_left_right(G, fuente, sumidero)

    edge_labels = nx.get_edge_attributes(G, 'capacity')
    colores = ["lightgreen" if n == fuente else "salmon" if n == sumidero else "skyblue" for n in G.nodes()]

    fig, ax = plt.subplots(figsize=(14, 9), dpi=120)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(
        G, pos, 
        node_size=1400, 
        node_color=colores,
        edgecolors='black',
        linewidths=2.5,
        ax=ax
    )
    
    # Etiquetas de nodos
    nx.draw_networkx_labels(
        G, pos, 
        font_size=13, 
        font_weight='bold',
        ax=ax
    )
    
    # Aristas con flechas visibles (estilo CLRS)
    nx.draw_networkx_edges(
        G, pos,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=28,
        width=2.2,
        edge_color='#333333',
        connectionstyle='arc3,rad=0.08',
        min_source_margin=22,
        min_target_margin=22,
        ax=ax
    )
    
    # Etiquetas de capacidades
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=edge_labels, 
        font_size=11,
        font_weight='bold',
        label_pos=0.5,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="gray", alpha=0.9, linewidth=1),
        ax=ax
    )
    
    ax.set_title(f"Grafo de Flujo | Fuente: {fuente} • Sumidero: {sumidero}", 
                 fontsize=17, fontweight='bold', pad=20)
    ax.axis('off')
    plt.tight_layout()
    return fig
