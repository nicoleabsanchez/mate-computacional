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

def generar_grafo_aleatorio(n, excluidas=None):
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    max_aristas = n * (n - 1)
    min_aristas = n
    num_aristas = random.randint(min_aristas, int(1.5 * n))

    if excluidas is None:
        excluidas = set()

    excluidas_bidireccionales = set(frozenset((u, v)) for u, v in excluidas)

    while G.number_of_edges() < num_aristas:
        u, v = random.sample(nodos, 2)
        par = frozenset((u, v))
        if not G.has_edge(u, v) and par not in excluidas_bidireccionales:
            capacidad = random.randint(10, 30)
            G.add_edge(u, v, capacity=capacidad)
            excluidas_bidireccionales.add(par)

    return G

def ingresar_5_aristas_manualmente(n):
    G = nx.DiGraph()
    nodos = [str(i) for i in range(n)]
    G.add_nodes_from(nodos)

    aristas_fijas = [("0", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "5")]
    print("🔧 Ingrese la capacidad para las siguientes 5 aristas:")

    for u, v in aristas_fijas:
        while True:
            try:
                cap = int(input(f"Capacidad para la arista {u} → {v}: "))
                if cap > 0:
                    G.add_edge(u, v, capacity=cap)
                    break
                else:
                    print("❌ La capacidad debe ser mayor a 0.")
            except ValueError:
                print("❌ Entrada inválida. Ingrese un número entero.")
    return G, set(aristas_fijas)

def mostrar_grafo(G):
    pos = nx.kamada_kawai_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'capacity')

    plt.figure(figsize=(10, 7), dpi=100)
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=700,
        node_color='skyblue',
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
    plt.title("Grafo Dirigido con Capacidades", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# --- MAIN ---
def main():
    n = solicitar_n()
    modo = elegir_modo()

    if modo == 'a':
        grafo = generar_grafo_aleatorio(n)
    else:
        grafo, aristas_fijas = ingresar_5_aristas_manualmente(n)
        grafo_extra = generar_grafo_aleatorio(n, excluidas=aristas_fijas | set(grafo.edges()))

        for u, v, data in grafo_extra.edges(data=True):
            if not grafo.has_edge(u, v):
                grafo.add_edge(u, v, **data)

    mostrar_grafo(grafo)

if __name__ == "__main__":
    main()
