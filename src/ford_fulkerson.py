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
    Implementa el algoritmo Ford-Fulkerson clásico usando DFS.
    """
    
    MAX_NODES = 16  # Límite máximo de nodos
    MAX_ITERATIONS = 10000  # Límite de iteraciones para evitar loops infinitos
    
    def __init__(self, G: nx.DiGraph, fuente: str, sumidero: str):
        """
        Inicializa el algoritmo con un grafo NetworkX.
        
        Args:
            G: Grafo dirigido con atributo 'capacity' en las aristas
            fuente: Nodo fuente
            sumidero: Nodo sumidero
            
        Raises:
            ValueError: Si el grafo tiene más de MAX_NODES nodos
            ValueError: Si la fuente o sumidero no están en el grafo
            ValueError: Si la fuente y sumidero son el mismo nodo
            ValueError: Si hay capacidades negativas o no numéricas
        """
        # Validar número de nodos
        if len(G.nodes()) > self.MAX_NODES:
            raise ValueError(f"El grafo tiene {len(G.nodes())} nodos, el máximo permitido es {self.MAX_NODES}")
        
        # Validar que fuente y sumidero existen
        if fuente not in G.nodes():
            raise ValueError(f"La fuente '{fuente}' no existe en el grafo")
        if sumidero not in G.nodes():
            raise ValueError(f"El sumidero '{sumidero}' no existe en el grafo")
        
        # Validar que fuente y sumidero son diferentes
        if fuente == sumidero:
            raise ValueError("La fuente y el sumidero deben ser nodos diferentes")
        
        # Validar capacidades
        for u, v, data in G.edges(data=True):
            capacity = data.get('capacity', 0)
            if not isinstance(capacity, (int, float)):
                raise ValueError(f"La capacidad de la arista ({u}, {v}) debe ser numérica, no {type(capacity).__name__}")
            if capacity < 0:
                raise ValueError(f"La capacidad de la arista ({u}, {v}) no puede ser negativa: {capacity}")
        
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
    
    def dfs(self, current_idx: int, sink_idx: int, visited: Set[int], parent: List[int], depth: int = 0) -> bool:
        """
        Búsqueda en profundidad (DFS) para encontrar un camino aumentante.
        
        Args:
            current_idx: Índice del nodo actual
            sink_idx: Índice del sumidero
            visited: Conjunto de nodos ya visitados
            parent: Array de padres para reconstruir el camino
            depth: Profundidad actual de la recursión
        
        Returns:
            True si existe un camino del nodo actual al sumidero
            
        Raises:
            RecursionError: Si la profundidad excede el número de nodos (ciclo detectado)
        """
        # Protección contra recursión infinita
        if depth > len(self.residual):
            raise RecursionError(f"Profundidad de recursión excedida ({depth} > {len(self.residual)}). Posible ciclo en el grafo.")
        
        # Si llegamos al sumidero, encontramos un camino
        if current_idx == sink_idx:
            return True
        
        visited.add(current_idx)
        
        # Explorar todos los vecinos
        for v in range(len(self.residual)):
            # Si no ha sido visitado y hay capacidad residual
            if v not in visited and self.residual[current_idx][v] > 0:
                parent[v] = current_idx
                
                # Recursivamente buscar desde el vecino
                if self.dfs(v, sink_idx, visited, parent, depth + 1):
                    return True
        
        return False
    
    def find_max_flow(self) -> int:
        """
        Ejecuta el algoritmo Ford-Fulkerson clásico (con DFS) y retorna el flujo máximo.
        
        Returns:
            Flujo máximo encontrado
            
        Raises:
            RuntimeError: Si el algoritmo no converge después de MAX_ITERATIONS
            ValueError: Si se encuentra un flujo negativo o inválido
        """
        source_idx = self.node_to_idx[self.fuente]
        sink_idx = self.node_to_idx[self.sumidero]
        n = len(self.residual)
        
        max_flow = 0
        iterations = 0
        
        # Mientras exista un camino aumentante (encontrado con DFS)
        while True:
            iterations += 1
            
            # Protección contra loops infinitos
            if iterations > self.MAX_ITERATIONS:
                raise RuntimeError(
                    f"El algoritmo no convergió después de {self.MAX_ITERATIONS} iteraciones. "
                    f"Esto puede ocurrir con capacidades irracionales o grafos problemáticos. "
                    f"Flujo parcial alcanzado: {max_flow}"
                )
            
            parent = [-1] * n
            visited = set()
            
            # Buscar camino aumentante con DFS
            try:
                if not self.dfs(source_idx, sink_idx, visited, parent):
                    break  # No hay más caminos aumentantes
            except RecursionError as e:
                raise RuntimeError(f"Error en DFS después de {iterations} iteraciones: {e}")
            
            # Encontrar la capacidad mínima en el camino encontrado
            path_flow = float('inf')
            s = sink_idx
            path_indices = []
            
            while s != source_idx:
                path_indices.append(s)
                if parent[s] == -1:
                    raise ValueError(f"Camino inválido: nodo {self.idx_to_node[s]} no tiene padre")
                path_flow = min(path_flow, self.residual[parent[s]][s])
                s = parent[s]
            path_indices.append(source_idx)
            path_indices.reverse()
            
            # Validar que el flujo es positivo
            if path_flow <= 0 or path_flow == float('inf'):
                raise ValueError(f"Flujo inválido en iteración {iterations}: {path_flow}")
            
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
        
        # Grupo S: nodos desde la fuente | izquierda
        self.min_cut_S = {self.idx_to_node[idx] for idx in reachable_indices}
        
        # Grupo T: nodos al sumidero | derecha
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
        Retorna resumen del análisis de flujo máximo.
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
        
    Raises:
        ValueError: Si los parámetros son inválidos
        RuntimeError: Si el algoritmo no converge
    """
    try:
        ff = FordFulkerson(G, fuente, sumidero)
        ff.find_max_flow()
        return ff
    except ValueError as e:
        raise ValueError(f"Error en los datos de entrada: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Error durante la ejecución del algoritmo: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado: {type(e).__name__}: {e}")
