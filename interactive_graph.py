import json
from pyvis.network import Network

def draw_interactive():
    with open("hiperontologia_final.json", 'r', encoding='utf-8') as f:
        datos = json.load(f)

    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")
    net.toggle_physics(False) 

    # Nodos
    for n in datos.get('nodos', []):
        nid = n.get('id') or n.get('label') if isinstance(n, dict) else str(n)
        net.add_node(nid, label=nid, size=10)

    # Aristas (Lógica idéntica al visualizador)
    for a in datos.get('hiperaristas', []):
        if isinstance(a, dict):
            u, v = a.get('source'), a.get('target')
            if not (u and v):
                lista = a.get('nodos_involucrados') or a.get('nodos')
                if isinstance(lista, list) and len(lista) > 1:
                    u, v = lista[0], lista[1]
            if u and v:
                try: net.add_edge(u, v)
                except: pass
        elif isinstance(a, list) and len(a) > 1:
            try: net.add_edge(a[0], a[1])
            except: pass

    net.save_graph("grafo_interactivo.html")
    print(f"✅ Grafo interactivo listo con {len(net.nodes)} nodos.")

if __name__ == "__main__":
    draw_interactive()
