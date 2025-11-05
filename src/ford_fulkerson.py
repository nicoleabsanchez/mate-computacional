# file: src/ford_fulkerson.py
"""
Implementación del algoritmo Ford-Fulkerson para encontrar el flujo máximo
en una red de flujo representada como nx.DiGraph.
"""
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Set
import networkx as nx


class FordFulkerson:
    """
    Implementa el algoritmo Ford-Fulkerson usando BFS (Edmonds-Karp).
    """
    
    def __init__(self, G: nx.DiGraph, fuente: str, sumidero: str):
        """
        Inicializa el algoritmo con un grafo NetworkX.
        
        Args:
            G: Grafo dirigido con atributo 'capacity' en las aristas
            fuente: Nodo fuente
            sumidero: Nodo sumidero
        """
        self.G_original = G.copy()
        self.fuente = fuente
        self.sumidero = sumidero
        
        # Crear grafo residual (matriz de adyacencia)
        self.nodes = list(G.nodes())
        self.node_to_idx = {node: idx for idx, node in enumerate(self.nodes)}
        self.idx_to_node = {idx: node for node, idx in self.node_to_idx.items()}
        
        n = len(self.nodes)
        self.residual = [[0] * n for _ in range(n)]
        
        # Inicializar capacidades en el grafo residual
        for u, v, data in G.edges(data=True):
            u_idx = self.node_to_idx[u]
            v_idx = self.node_to_idx[v]
            capacity = data.get('capacity', 0)
            self.residual[u_idx][v_idx] = capacity
        
        # Almacenar flujo en cada arista
        self.flow: Dict[Tuple[str, str], int] = {}
        for u, v in G.edges():
            self.flow[(u, v)] = 0
        
        self.max_flow_value = 0
        self.augmenting_paths: List[List[str]] = []
        
        # Corte mínimo
        self.min_cut_S: Set[str] = set()  # Grupo S (contiene fuente)
        self.min_cut_T: Set[str] = set()  # Grupo T (contiene sumidero)
        self.cut_edges: List[Tuple[str, str]] = []  # Aristas del corte
        self.cut_capacity: int = 0
    
    def bfs(self, source_idx: int, sink_idx: int, parent: List[int]) -> bool:
        """
        Búsqueda en anchura (BFS) para encontrar un camino aumentante.
        
        Returns:
            True si existe un camino de la fuente al sumidero
        """
        n = len(self.residual)
        visited = [False] * n
        queue = deque([source_idx])
        visited[source_idx] = True
        
        while queue:
            u = queue.popleft()
            
            for v in range(n):
                # Si no ha sido visitado y hay capacidad residual
                if not visited[v] and self.residual[u][v] > 0:
                    visited[v] = True
                    parent[v] = u
                    queue.append(v)
                    
                    # Si llegamos al sumidero, retornamos True
                    if v == sink_idx:
                        return True
        
        return False
    
    def find_max_flow(self) -> int:
        """
        Ejecuta el algoritmo Ford-Fulkerson y retorna el flujo máximo.
        """
        source_idx = self.node_to_idx[self.fuente]
        sink_idx = self.node_to_idx[self.sumidero]
        n = len(self.residual)
        
        parent = [-1] * n
        max_flow = 0
        
        # Mientras exista un camino aumentante
        while self.bfs(source_idx, sink_idx, parent):
            # Encontrar la capacidad mínima en el camino encontrado
            path_flow = float('inf')
            s = sink_idx
            path_indices = []
            
            while s != source_idx:
                path_indices.append(s)
                path_flow = min(path_flow, self.residual[parent[s]][s])
                s = parent[s]
            path_indices.append(source_idx)
            path_indices.reverse()
            
            # Convertir índices a nombres de nodos
            path_nodes = [self.idx_to_node[idx] for idx in path_indices]
            self.augmenting_paths.append(path_nodes)
            
            # Actualizar capacidades residuales
            v = sink_idx
            while v != source_idx:
                u = parent[v]
                self.residual[u][v] -= path_flow
                self.residual[v][u] += path_flow
                v = parent[v]
            
            max_flow += path_flow
        
        self.max_flow_value = max_flow
        self._compute_flow()
        self._compute_min_cut()
        return max_flow
    
    def _compute_flow(self) -> None:
        """
        Calcula el flujo en cada arista original basándose en el grafo residual.
        """
        for u, v in self.G_original.edges():
            u_idx = self.node_to_idx[u]
            v_idx = self.node_to_idx[v]
            
            # El flujo es la capacidad original menos la capacidad residual
            original_capacity = self.G_original[u][v].get('capacity', 0)
            residual_capacity = self.residual[u_idx][v_idx]
            flow = original_capacity - residual_capacity
            
            self.flow[(u, v)] = flow
    
    def _compute_min_cut(self) -> None:
        """
        Calcula el corte mínimo usando BFS en el grafo residual final.
        Teorema: El corte mínimo corresponde a las aristas saturadas que separan
        los nodos alcanzables desde la fuente de los no alcanzables.
        """
        source_idx = self.node_to_idx[self.fuente]
        n = len(self.residual)
        
        # BFS para encontrar todos los nodos alcanzables desde la fuente
        visited = [False] * n
        queue = deque([source_idx])
        visited[source_idx] = True
        reachable_indices = {source_idx}
        
        while queue:
            u = queue.popleft()
            for v in range(n):
                if not visited[v] and self.residual[u][v] > 0:
                    visited[v] = True
                    reachable_indices.add(v)
                    queue.append(v)
        
        # Grupo S: nodos alcanzables desde la fuente
        self.min_cut_S = {self.idx_to_node[idx] for idx in reachable_indices}
        
        # Grupo T: nodos NO alcanzables (incluye sumidero)
        self.min_cut_T = set(self.nodes) - self.min_cut_S
        
        # Encontrar aristas del corte (de S a T en el grafo original)
        self.cut_edges = []
        self.cut_capacity = 0
        
        for u, v, data in self.G_original.edges(data=True):
            if u in self.min_cut_S and v in self.min_cut_T:
                capacity = data.get('capacity', 0)
                self.cut_edges.append((u, v))
                self.cut_capacity += capacity
    
    def get_min_cut_info(self) -> Dict[str, any]:
        """
        Retorna información del corte mínimo.
        """
        return {
            'grupo_S': sorted(list(self.min_cut_S), key=lambda x: int(x)),
            'grupo_T': sorted(list(self.min_cut_T), key=lambda x: int(x)),
            'aristas_corte': self.cut_edges,
            'capacidad_corte': self.cut_capacity,
            'num_nodos_S': len(self.min_cut_S),
            'num_nodos_T': len(self.min_cut_T),
        }
    
    def get_flow_details(self) -> List[Dict[str, any]]:
        """
        Retorna detalles del flujo en cada arista.
        
        Returns:
            Lista de diccionarios con información de cada arista
        """
        details = []
        for u, v, data in self.G_original.edges(data=True):
            capacity = data.get('capacity', 0)
            flow = self.flow.get((u, v), 0)
            utilization = (flow / capacity * 100) if capacity > 0 else 0
            
            # Verificar si es arista del corte
            is_cut_edge = (u, v) in self.cut_edges
            
            details.append({
                'origen': u,
                'destino': v,
                'capacidad': capacity,
                'flujo': flow,
                'residual': capacity - flow,
                'utilizacion': f"{utilization:.1f}%",
                'saturada': '🔴 Sí' if flow == capacity else '⚪ No',
                'corte': '✂️ Sí' if is_cut_edge else ''
            })
        
        # Ordenar por origen y destino
        details.sort(key=lambda x: (int(x['origen']), int(x['destino'])))
        return details
    
    def get_summary(self) -> Dict[str, any]:
        """
        Retorna un resumen del análisis de flujo máximo.
        """
        total_capacity_out = sum(
            self.G_original[self.fuente][v].get('capacity', 0) 
            for v in self.G_original.successors(self.fuente)
        )
        
        total_capacity_in = sum(
            self.G_original[u][self.sumidero].get('capacity', 0) 
            for u in self.G_original.predecessors(self.sumidero)
        )
        
        saturated_edges = sum(
            1 for (u, v), flow in self.flow.items() 
            if flow == self.G_original[u][v].get('capacity', 0) and flow > 0
        )
        
        return {
            'flujo_maximo': self.max_flow_value,
            'capacidad_salida_fuente': total_capacity_out,
            'capacidad_entrada_sumidero': total_capacity_in,
            'aristas_saturadas': saturated_edges,
            'total_aristas': len(self.flow),
            'caminos_aumentantes': len(self.augmenting_paths),
            'eficiencia_fuente': f"{(self.max_flow_value / total_capacity_out * 100):.1f}%" if total_capacity_out > 0 else "N/A",
            'eficiencia_sumidero': f"{(self.max_flow_value / total_capacity_in * 100):.1f}%" if total_capacity_in > 0 else "N/A",
        }
    
    def get_augmenting_paths(self) -> List[str]:
        """
        Retorna los caminos aumentantes encontrados en formato legible.
        """
        paths = []
        for i, path in enumerate(self.augmenting_paths, 1):
            path_str = " → ".join(path)
            paths.append(f"Camino {i}: {path_str}")
        return paths


def calcular_flujo_maximo(G: nx.DiGraph, fuente: str, sumidero: str) -> FordFulkerson:
    """
    Función auxiliar para calcular el flujo máximo.
    
    Args:
        G: Grafo dirigido con capacidades
        fuente: Nodo fuente
        sumidero: Nodo sumidero
    
    Returns:
        Objeto FordFulkerson con los resultados
    """
    ff = FordFulkerson(G, fuente, sumidero)
    ff.find_max_flow()
    return ff
