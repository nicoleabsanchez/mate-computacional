# file: src/graph_core.py
import random
from typing import List, Tuple, Dict, Optional
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
    """Aplica todas las restricciones del grafo de flujo"""
    # Eliminar arista directa fuente → sumidero
    if G.has_edge(fuente, sumidero):
        G.remove_edge(fuente, sumidero)
    
    # Eliminar aristas entrantes a la fuente
    for u in list(G.predecessors(fuente)):
        G.remove_edge(u, fuente)
    
    # Eliminar aristas salientes del sumidero
    for v in list(G.successors(sumidero)):
        G.remove_edge(sumidero, v)
    
    # Eliminar aristas bidireccionales (mantener solo una dirección)
    for u, v in list(nx.Graph(G).edges()):
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

def generar_grafo_aleatorio_clrs_style(
    n: int, 
    fuente: str, 
    sumidero: str, 
    seed: Optional[int] = None,
    edge_prob: float = 0.65,
    capacity_range: Tuple[int, int] = (4, 20),
) -> nx.DiGraph:
    """
    Genera un grafo dirigido estilo CLRS con estructura por capas.
    
    REGLAS:
    1. Las aristas SOLO van de una capa a la SIGUIENTE (capa i → capa i+1)
    2. TODOS los nodos de la PENÚLTIMA capa DEBEN conectarse al sumidero
    3. NUNCA conectar capas intermedias directamente al sumidero
    4. NO hay aristas bidireccionales
    5. NO hay aristas dentro de la misma capa
    """
    if seed is not None:
        random.seed(seed)
    
    if n < 3:
        raise ValueError("Se necesitan al menos 3 nodos (fuente, intermedio, sumidero)")
    
    G = nx.DiGraph()
    
    # Crear todos los nodos
    all_nodes = [str(i) for i in range(n)]
    G.add_nodes_from(all_nodes)
    
    # Nodos intermedios (excluir fuente y sumidero)
    intermediate = [node for node in all_nodes if node not in (fuente, sumidero)]
    
    if len(intermediate) == 0:
        # Caso especial: solo fuente y sumidero
        cap = random.randint(*capacity_range)
        G.add_edge(fuente, sumidero, capacity=cap)
        return G
    
    # Determinar número de capas basado en cantidad de nodos
    num_intermediate = len(intermediate)
    if num_intermediate <= 3:
        num_layers = 1
    elif num_intermediate <= 6:
        num_layers = 2
    elif num_intermediate <= 9:
        num_layers = 3
    else:
        num_layers = 4
    
    # Distribuir nodos intermedios en capas de forma balanceada
    layers: List[List[str]] = [[] for _ in range(num_layers)]
    random.shuffle(intermediate)
    
    for i, node in enumerate(intermediate):
        layer_idx = i % num_layers
        layers[layer_idx].append(node)
    
    # CREAR MAPEO: nodo → índice de capa
    node_to_layer: Dict[str, int] = {fuente: -1, sumidero: num_layers}
    for layer_idx, layer_nodes in enumerate(layers):
        for node in layer_nodes:
            node_to_layer[node] = layer_idx
    
    cap_min, cap_max = capacity_range
    
    # ====== PASO 1: CREAR CAMINO ======
    backbone_path = [fuente]
    for layer in layers:
        backbone_path.append(random.choice(layer))
    backbone_path.append(sumidero)
    
    # Crear aristas
    for i in range(len(backbone_path) - 1):
        u, v = backbone_path[i], backbone_path[i + 1]
        G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
    
    # ====== PASO 2: CONECTAR FUENTE A PRIMERA CAPA ======
    # Conectar TODOS los nodos de la primera capa con la fuente
    for v in layers[0]:
        if not G.has_edge(fuente, v):
            G.add_edge(fuente, v, capacity=random.randint(cap_min, cap_max))
    
    # ====== PASO 3: CONECTAR CAPAS CONSECUTIVAS (SOLO i → i+1) ======
    # REGLA: Solo conectar capa i con capa i+1 (NO saltar capas)
    for i in range(len(layers) - 1):
        layer_current = layers[i]
        layer_next = layers[i + 1]
        
        for u in layer_current:
            # Cada nodo debe tener al menos una conexión a la siguiente capa
            has_connection = False
            for v in layer_next:
                if G.has_edge(u, v):
                    has_connection = True
                    break
            
            # Si no tiene conexión, crear al menos una
            if not has_connection:
                v = random.choice(layer_next)
                G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
            
            # Agregar más conexiones con probabilidad
            for v in layer_next:
                if not G.has_edge(u, v) and random.random() < edge_prob:
                    G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
    
    # ====== PASO 4: CONECTAR PENÚLTIMA CAPA AL SUMIDERO ======
    # REGLA CRÍTICA: TODOS los nodos de la última capa DEBEN conectarse al sumidero
    for u in layers[-1]:
        if not G.has_edge(u, sumidero):
            G.add_edge(u, sumidero, capacity=random.randint(cap_min, cap_max))
    
    # ====== PASO 5: ELIMINAR CONEXIONES INVÁLIDAS ======
    # Eliminar cualquier conexión de capas intermedias al sumidero
    edges_to_remove = []
    for u, v in G.edges():
        layer_u = node_to_layer.get(u, -1)
        layer_v = node_to_layer.get(v, num_layers)
        
        # Si v es el sumidero y u NO está en la penúltima capa, ELIMINAR
        if v == sumidero and layer_u != num_layers - 1:
            edges_to_remove.append((u, v))
        
        # Si la arista no va a la capa inmediatamente siguiente, ELIMINAR
        # (excepto fuente→capa0 y penúltima→sumidero)
        elif layer_v != layer_u + 1:
            edges_to_remove.append((u, v))
    
    for u, v in edges_to_remove:
        G.remove_edge(u, v)
    
    # ====== PASO 6: VERIFICAR CONECTIVIDAD Y RESTAURAR SI ES NECESARIO ======
    if not nx.has_path(G, fuente, sumidero):
        # Restaurar
        for i in range(len(backbone_path) - 1):
            u, v = backbone_path[i], backbone_path[i + 1]
            if not G.has_edge(u, v):
                G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
    
    # ====== PASO 7: APLICAR CONSTRAINTS FINALES ======
    enforce_constraints(G, fuente, sumidero)
    
    # ====== PASO 8: VALIDACIÓN FINAL ======
    # Asegurar que TODOS los nodos de la penúltima capa estén conectados al sumidero
    for u in layers[-1]:
        if not G.has_edge(u, sumidero):
            G.add_edge(u, sumidero, capacity=random.randint(cap_min, cap_max))
    
    # Verificar que NO haya aristas inválidas
    for u, v in list(G.edges()):
        layer_u = node_to_layer.get(u, -1)
        layer_v = node_to_layer.get(v, num_layers)
        
        # Aristas válidas:
        # 1. fuente → capa 0
        # 2. capa i → capa i+1 (para i < num_layers-1)
        # 3. capa num_layers-1 → sumidero
        
        is_valid = False
        
        if u == fuente and layer_v == 0:
            is_valid = True
        elif v == sumidero and layer_u == num_layers - 1:
            is_valid = True
        elif layer_v == layer_u + 1 and 0 <= layer_u < num_layers - 1:
            is_valid = True
        
        if not is_valid:
            G.remove_edge(u, v)
    
    # Verificación final de conectividad
    if not nx.has_path(G, fuente, sumidero):
        for i in range(len(backbone_path) - 1):
            u, v = backbone_path[i], backbone_path[i + 1]
            if not G.has_edge(u, v):
                G.add_edge(u, v, capacity=random.randint(cap_min, cap_max))
    
    return G


def generar_grafo_aleatorio(n: int, fuente: str, sumidero: str, seed: int | None = None) -> nx.DiGraph:
    """
    Wrapper que usa el estilo CLRS.
    """
    return generar_grafo_aleatorio_clrs_style(
        n=n,
        fuente=fuente,
        sumidero=sumidero,
        seed=seed,
        edge_prob=0.65,
        capacity_range=(4, 20)
    )
