import networkx as nx
import matplotlib.pyplot as plt
import random

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

def elegir_modo():
    while True:
        modo = input("¿Desea generar el grafo aleatoriamente o manualmente? (a/m): ").lower()
        if modo in ['a', 'm']:
            return modo
        print("❌ Opción inválida. Ingrese 'a' para aleatorio o 'm' para manual.")

def solicitar_fuente_sumidero(n):
    """Pide y valida vértice fuente y sumidero distintos dentro de [0, n-1]."""
    nodos_validos = {str(i) for i in range(n)}
    while True:
        fuente = input(f"Ingrese el nodo fuente (0 a {n-1}): ").strip()
        sumidero = input(f"Ingrese el nodo sumidero (0 a {n-1}, distinto de fuente): ").strip()
        
        if fuente in nodos_validos and sumidero in nodos_validos and fuente != sumidero:
            return fuente, sumidero
        print("❌ Fuente o sumidero inválido. Intente nuevamente.")

def generar_grafo_aleatorio(n, fuente, sumidero):
    """Genera un grafo asegurando que la fuente no tenga aristas entrantes y el sumidero no tenga aristas salientes."""
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    max_aristas = n * (n - 1)
    min_aristas = n
    num_aristas = random.randint(min_aristas, int(1.5 * n))

    excluidas_bidireccionales = set()

    while G.number_of_edges() < num_aristas:
        u, v = random.sample(nodos, 2)

        # Verificamos que la fuente no tenga aristas entrantes
        if u == fuente or v == fuente:
            if u == fuente and G.in_degree(v) == 0:
                capacidad = random.randint(10, 30)
                G.add_edge(u, v, capacity=capacidad)
            elif v == fuente and G.in_degree(u) == 0:
                capacidad = random.randint(10, 30)
                G.add_edge(v, u, capacity=capacidad)

        # Verificamos que el sumidero no tenga aristas salientes
        elif u == sumidero or v == sumidero:
            if u == sumidero and G.out_degree(v) == 0:
                capacidad = random.randint(10, 30)
                G.add_edge(u, v, capacity=capacidad)
            elif v == sumidero and G.out_degree(u) == 0:
                capacidad = random.randint(10, 30)
                G.add_edge(v, u, capacity=capacidad)
        else:
            capacidad = random.randint(10, 30)
            G.add_edge(u, v, capacity=capacidad)

    return G

def ingresar_5_aristas_manualmente(n, fuente, sumidero):
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    # Pedimos solo 3 aristas que no involucren al fuente ni sumidero
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

def mostrar_grafo(G, fuente=None, sumidero=None):
    pos = nx.kamada_kawai_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'capacity')

    # Colores (fuente=verde, sumidero=rojo, otros=celeste)
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

    # Pedir fuente y sumidero antes de generar el grafo
    fuente, sumidero = solicitar_fuente_sumidero(n)
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
