# file: src/graph_core.py
import random
from typing import List, Tuple, Dict
import networkx as nx

def add_or_update_edge_no_bidirectional(G: nx.DiGraph, u: str, v: str, capacity: int) -> None:
    if u == v:
        return
    if G.has_edge(v, u):
        G.remove_edge(v, u)
    if G.has_edge(u, v):
        G[u][v]["capacity"] = capacity
    else:
        G.add_edge(u, v, capacity=capacity)

def enforce_constraints(G: nx.DiGraph, fuente: str, sumidero: str) -> None:
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
    pares: List[Tuple[str, str]] = []
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

    for _ in range(3):
        destino = str(random.choice([i for i in range(1, n-1)]))
        add_or_update_edge_no_bidirectional(G, fuente, destino, random.randint(4, 15))
    for _ in range(3):
        origen = str(random.choice([i for i in range(0, n-1)]))
        add_or_update_edge_no_bidirectional(G, origen, sumidero, random.randint(4, 15))
    for node in range(1, n-1):
        origen = str(random.choice([i for i in range(0, n-1) if i != node and str(i) != fuente]))
        add_or_update_edge_no_bidirectional(G, origen, str(node), random.randint(4, 15))
        destino = str(random.choice([i for i in range(0, n-1) if i != node and str(i) != sumidero]))
        add_or_update_edge_no_bidirectional(G, str(node), destino, random.randint(4, 15))

    enforce_constraints(G, fuente, sumidero)
    return G 


