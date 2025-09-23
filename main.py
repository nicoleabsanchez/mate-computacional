import networkx as nx
import matplotlib.pyplot as plt
import random
from collections import deque

# Función para solicitar el número de nodos
def solicitar_n():
    while True:
        try:
            n = int(input("Ingrese el número de nodos (entre 8 y 16): "))
            if 8 <= n <= 16:
                return n
            else:
                print("❌ Debe estar entre 8 y 16.")
        except ValueError:
            print("❌ Entrada inválida. Ingrese un número entero.")

# Función para elegir el modo de generación del grafo
def elegir_modo():
    while True:
        modo = input("¿Desea generar el grafo aleatoriamente o manualmente? (a/m): ").lower()
        if modo in ['a', 'm']:
            return modo
        print("❌ Opción inválida. Ingrese 'a' para aleatorio o 'm' para manual.")

# Función para pedir la fuente y el sumidero
def solicitar_fuente_sumidero(n):
    nodos_validos = {str(i) for i in range(n)}
    while True:
        fuente = input(f"Ingrese el nodo fuente (0 a {n-1}): ").strip()
        sumidero = input(f"Ingrese el nodo sumidero (0 a {n-1}, distinto de fuente): ").strip()
        
        if fuente in nodos_validos and sumidero in nodos_validos and fuente != sumidero:
            return fuente, sumidero
        print("❌ Fuente o sumidero inválido. Intente nuevamente.")

# Función para generar el grafo de manera aleatoria
def generar_grafo_aleatorio(n, fuente, sumidero):
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    # Fuente siempre es el nodo 0, sumidero es el nodo n-1
    # Fuente solo tiene aristas salientes (no puede recibir aristas)
    for _ in range(3):
        destino = str(random.choice([i for i in range(1, n-1)]))  # Excluir el sumidero
        G.add_edge(fuente, destino, capacity=random.randint(4, 15))

    # Sumidero siempre es el último nodo, agregar 3 aristas entrantes (no puede tener aristas salientes)
    for _ in range(3):
        origen = str(random.choice([i for i in range(0, n-1)]))  # Excluir el sumidero
        G.add_edge(origen, sumidero, capacity=random.randint(4, 15))

    # Los demás nodos, tener entre 1 o 2 aristas entrantes y salientes
    for node in range(1, n-1):
        num_entrantes = random.randint(1, 2)
        num_salientes = random.randint(1, 2)

        # Agregar aristas entrantes (sin involucrar fuente ni sumidero)
        for _ in range(num_entrantes):
            G.add_edge(str(random.choice([i for i in range(0, n-1) if i != node and i != fuente])), str(node), capacity=random.randint(4, 15))

        # Agregar aristas salientes (sin involucrar fuente ni sumidero)
        for _ in range(num_salientes):
            G.add_edge(str(node), str(random.choice([i for i in range(0, n-1) if i != node and i != sumidero])), capacity=random.randint(4, 15))

    # Asegurarnos de que la fuente y sumidero no estén conectados directamente
    if G.has_edge(fuente, sumidero):
        G.remove_edge(fuente, sumidero)
        
    # Eliminar aristas donde el destino sea el fuente
    for u, v in list(G.edges()):
        if v == fuente:
            G.remove_edge(u, v)

    # Eliminar aristas donde el origen sea el sumidero
    for u, v in list(G.edges()):
        if u == sumidero:
            G.remove_edge(u, v)
    
    return G

# Función para ingresar 3 aristas manualmente, evitando la fuente y sumidero
def ingresar_5_aristas_manualmente(n, fuente, sumidero):
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    aristas_fijas = []
    print("🔧 Ingrese 3 aristas que no involucren la fuente ni el sumidero:")
    for _ in range(3):
        while True:
            u = input(f"Ingrese el nodo de inicio (0 a {n-1}, distinto de fuente y sumidero): ").strip()
            v = input(f"Ingrese el nodo de destino (0 a {n-1}, distinto de fuente y sumidero): ").strip()
            if u != fuente and v != fuente and u != sumidero and v != sumidero:
                while True:
                    try:
                        cap = int(input(f"Capacidad para la arista {u} → {v}: "))
                        if cap > 0:
                            G.add_edge(u, v, capacity=cap)
                            aristas_fijas.append((u, v))
                            break
                        else:
                            print("❌ La capacidad debe ser mayor a 0.")
                    except ValueError:
                        print("❌ Entrada inválida. Ingrese un número entero.")
                break
            else:
                print("❌ Las aristas no pueden involucrar la fuente ni el sumidero.")
    return G, aristas_fijas

# Función para mostrar el grafo
def mostrar_grafo(G, fuente=None, sumidero=None):
    pos = nx.kamada_kawai_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'capacity')

    colores = []
    for n in G.nodes():
        if fuente is not None and n == fuente:
            colores.append('lightgreen')
        elif sumidero is not None and n == sumidero:
            colores.append('salmon')
        else:
            colores.append('skyblue')

    plt.figure(figsize=(10, 7), dpi=100)
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=700,
        node_color=colores,
        font_size=12,
        font_weight='bold',
        arrows=True,
        width=1.5,
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=10,
        label_pos=0.5
    )

    titulo = "Grafo Dirigido con Capacidades"
    if fuente is not None and sumidero is not None:
        titulo += f"  |  Fuente: {fuente}  •  Sumidero: {sumidero}"
    plt.title(titulo, fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def main():
    n = solicitar_n()
    modo = elegir_modo()

    # Fuente es siempre 0 y sumidero es siempre n-1
    fuente = "0"
    sumidero = str(n-1)
    print(f"✅ Fuente seleccionada: {fuente}")
    print(f"✅ Sumidero seleccionado: {sumidero}")

    if modo == 'a':
        grafo = generar_grafo_aleatorio(n, fuente, sumidero)
    else:
        grafo, aristas_fijas = ingresar_5_aristas_manualmente(n, fuente, sumidero)
        grafo_extra = generar_grafo_aleatorio(n, fuente, sumidero)
        for u, v, data in grafo_extra.edges(data=True):
            if not grafo.has_edge(u, v):
                grafo.add_edge(u, v, **data)

    mostrar_grafo(grafo, fuente=fuente, sumidero=sumidero)

if __name__ == "__main__":
    main()
