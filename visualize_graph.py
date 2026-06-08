import json
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def generar_grafo():
    with open("hiperontologia_final.json", 'r', encoding='utf-8') as f:
        datos = json.load(f)

    G = nx.Graph()
    
    # Agregar nodos
    for n in datos.get('nodos', []):
        if isinstance(n, dict):
            node_id = n.get('id') or n.get('label') or "unk"
            G.add_node(node_id, label=n.get('label', node_id))
        else:
            G.add_node(n, label=n)

    # Agregar aristas detectando source/target
    for a in datos.get('hiperaristas', []):
        u = a.get('source')
        v = a.get('target')
        if u and v:
            # Solo agregamos si ambos nodos existen (o los creamos sobre la marcha)
            G.add_edge(u, v)

    total_n = G.number_of_nodes()
    total_e = G.number_of_edges()
    print(f"📊 Grafo procesado: {total_n} nodos y {total_e} conexiones.")

    if total_e == 0:
        print("⚠️ Siguen sin detectarse conexiones. Revisa las llaves del JSON.")
        return

    # Con 10k nodos, un PNG será una mancha. Hacemos un plot pequeño de una muestra
    # o simplemente confirmamos el procesamiento.
    plt.figure(figsize=(12, 12))
    plt.title(f"Muestra de Hiperontología ({total_n} nodos)")
    # Solo dibujamos una parte si es gigante para no colapsar
    if total_n > 500:
        print("Submuestreando para la imagen estática...")
        nodos_muestra = list(G.nodes())[:500]
        subgrafo = G.subgraph(nodos_muestra)
        nx.draw(subgrafo, node_size=20, alpha=0.5)
    else:
        nx.draw(G, with_labels=False, node_size=30)
        
    plt.savefig("mapa_conceptos.png")
    print("✅ Imagen generada.")

if __name__ == "__main__":
    generar_grafo()
