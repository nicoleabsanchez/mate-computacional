# path: examples/random_flow_graph_clrs_style.py
from __future__ import annotations
import random
from typing import Dict, Tuple, Optional, List
import networkx as nx
import matplotlib.pyplot as plt

Node = int
Pos = Dict[Node, Tuple[float, float]]

def generate_layered_flow_graph(
    seed: Optional[int] = 42,
    num_layers: int = 3,
    nodes_per_layer: Tuple[int, int] = (2, 3),
    edge_prob: float = 0.7,
    capacity_range: Tuple[int, int] = (4, 20),
) -> nx.DiGraph:
    if seed is not None:
        random.seed(seed)
    if num_layers < 1:
        raise ValueError("num_layers debe ser >= 1 (capas internas).")

    G = nx.DiGraph()
    source = 0
    G.add_node(source, kind="source")

    layers: List[List[int]] = []
    next_id = 1
    for _ in range(num_layers):
        k = random.randint(*nodes_per_layer)
        layer_nodes = list(range(next_id, next_id + k))
        for u in layer_nodes:
            G.add_node(u, kind="inner")
        layers.append(layer_nodes)
        next_id += k

    sink = next_id
    G.add_node(sink, kind="sink")

    cap_min, cap_max = capacity_range
    if cap_min < 1 or cap_max < cap_min:
        raise ValueError("capacity_range inválido.")

    for v in layers[0]:
        if random.random() < max(0.4, edge_prob):
            G.add_edge(source, v, capacity=random.randint(cap_min, cap_max))

    for layer_a, layer_b in zip(layers[:-1], layers[1:]):
        any_added = False
        for u in layer_a:
            for v in layer_b:
                if random.random() < edge_prob:
                    G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
                    any_added = True
        if not any_added:
            u = random.choice(layer_a)
            v = random.choice(layer_b)
            G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))

    for u in layers[-1]:
        if random.random() < max(0.4, edge_prob):
            G.add_edge(u, sink, capacity=random.randint(cap_min, cap_max))

    try:
        has_path = any(nx.all_simple_paths(G, source=source, target=sink))
    except nx.NetworkXNoPath:
        has_path = False

    if not has_path:
        path = [source] + [random.choice(L) for L in layers] + [sink]
        for a, b in zip(path, path[1:]):
            if not G.has_edge(a, b):
                G.add_edge(a, b, capacity=random.randint(cap_min, cap_max))
    return G


def layered_positions(G: nx.DiGraph, x_gap: float = 1.6, y_gap: float = 1.2) -> Pos:
    source = [n for n, d in G.nodes(data=True) if d.get("kind") == "source"][0]
    sink = [n for n, d in G.nodes(data=True) if d.get("kind") == "sink"][0]
    top = list(nx.topological_sort(G))
    by_rank: Dict[int, List[int]] = {}
    for n in top:
        if n == source:
            rank = 0
        elif n == sink:
            rank = 10**9  # sentinel
        else:
            preds = list(G.predecessors(n))
            # Nota: simple ranking por predecesores para estabilidad visual.
            rank = 1 + max((next((k for k, vals in by_rank.items() if p in vals), 0) for p in preds), default=0)
        by_rank.setdefault(rank, []).append(n)

    ordered_keys = sorted(k for k in by_rank.keys() if k not in (0, 10**9))
    layers = [[source]] + [by_rank[k] for k in ordered_keys] + [[sink]]

    pos: Pos = {}
    for i, layer in enumerate(layers):
        h = (len(layer) - 1) * y_gap
        for j, n in enumerate(layer):
            pos[n] = (i * x_gap, j * y_gap - h / 2.0)
    return pos


def draw_flow_graph(
    G: nx.DiGraph,
    pos: Optional[Pos] = None,
    node_size: int = 1400,
    font_size: int = 12,
    arrow_size: int = 30,      # ↑ punta más grande
    arrow_style: str = "-|>",  # ↑ “cabecita” visible
    margin: float = 18.0,      # ↑ separa la punta del borde del nodo
    with_caps: bool = True,
    highlight_source_sink: bool = True,
    figsize: Tuple[int, int] = (9, 4),
    save_path: Optional[str] = None,
) -> None:
    if pos is None:
        pos = layered_positions(G)

    plt.figure(figsize=figsize)
    ax = plt.gca()
    ax.set_axis_off()

    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_shape="o", linewidths=1.2)
    nx.draw_networkx_labels(G, pos, labels={n: str(n) for n in G.nodes()}, font_size=font_size)

    # Flechas con punta visible
    nx.draw_networkx_edges(
        G,
        pos,
        arrows=True,
        arrowstyle=arrow_style,
        arrowsize=arrow_size,
        width=1.6,
        connectionstyle="arc3,rad=0.0",
        min_source_margin=margin,   # ← clave para que no se “meta” bajo el nodo
        min_target_margin=margin,   # ← idem
    )

    if with_caps:
        edge_lbls = {(u, v): d.get("capacity", "") for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_lbls, font_size=font_size)

    if highlight_source_sink:
        s = [n for n, d in G.nodes(data=True) if d.get("kind") == "source"]
        t = [n for n, d in G.nodes(data=True) if d.get("kind") == "sink"]
        nx.draw_networkx_nodes(G, pos, nodelist=s, node_size=int(node_size * 1.15), linewidths=2.0)
        nx.draw_networkx_nodes(G, pos, nodelist=t, node_size=int(node_size * 1.15), linewidths=2.0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=220)
    plt.show()


def demo():
    G = generate_layered_flow_graph(seed=7, num_layers=3, nodes_per_layer=(2, 3), edge_prob=0.8, capacity_range=(1, 20))
    pos = layered_positions(G)
    draw_flow_graph(G, pos)


if __name__ == "__main__":
    demo()
