import json
import os
import re

def limpiar_texto(texto):
    """Limpia cadenas para crear IDs perfectos (snake_case sin símbolos)"""
    if not isinstance(texto, str):
        return "unknown"
    # Remover todo lo que no sea alfanumérico, espacio o guion
    texto = re.sub(r'[^\w\s-]', '', texto)
    return texto.lower().strip().replace(" ", "_").replace("-", "_")

def cargar_json_robusto(ruta):
    """Intenta cargar el JSON y, si falla, aplica primeros auxilios al texto."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON corrupto o incompleto detectado ({e}). Intentando reparación de emergencia...")
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # 1. Limpiar comas huérfanas antes de llaves/corchetes de cierre
            contenido = re.sub(r',\s*([}\]])', r'\1', contenido)
            
            # 2. Balancear corchetes y llaves (útil si el archivo se cortó a medias)
            llaves_abiertas = contenido.count('{') - contenido.count('}')
            corchetes_abiertos = contenido.count('[') - contenido.count(']')
            
            if corchetes_abiertos > 0: contenido += '\n]' * corchetes_abiertos
            if llaves_abiertas > 0: contenido += '\n}' * llaves_abiertas
            
            return json.loads(contenido)
        except Exception as e_reparacion:
            print(f"❌ Imposible reparar el JSON de forma automática: {e_reparacion}")
            return None

def assemble():
    INPUT_FILE = "hiperontologia_final.json"
    OUTPUT_FILE = "protoagi_kernel.json"

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No se encuentra {INPUT_FILE}.")
        return

    print("🛡️ Iniciando ensamble ULTRA-ROBUSTO del Kernel...")
    
    raw_data = cargar_json_robusto(INPUT_FILE)
    if not raw_data:
        return

    clean_nodes = {}
    clean_edges = []
    nodos_descartados = 0
    aristas_descartadas = 0
    
    # Tolerancia a cambios de idioma o estructura del LLM
    lista_nodos = raw_data.get('nodos') or raw_data.get('nodes') or raw_data.get('concepts') or []
    lista_aristas = raw_data.get('hiperaristas') or raw_data.get('edges') or raw_data.get('links') or raw_data.get('relations') or []

    if not isinstance(lista_nodos, list): lista_nodos = []
    if not isinstance(lista_aristas, list): lista_aristas = []

    print(f"🧬 Procesando y unificando {len(lista_nodos)} posibles conceptos...")
    for n in lista_nodos:
        try:
            if isinstance(n, dict):
                raw_id = str(n.get('id') or n.get('label') or n.get('name') or "")
                desc = str(n.get('desc') or n.get('descripcion') or n.get('definition') or "")
                label = str(n.get('label') or n.get('name') or raw_id)
            elif isinstance(n, str):
                raw_id, desc, label = n, "", n
            else:
                nodos_descartados += 1
                continue
            
            if not raw_id:
                nodos_descartados += 1
                continue

            norm_id = limpiar_texto(raw_id)
            if not norm_id:
                nodos_descartados += 1
                continue
            
            if norm_id not in clean_nodes:
                clean_nodes[norm_id] = {
                    "id": norm_id,
                    "label": label.strip().capitalize(),
                    "definitions": set(),
                    "mentions": 0
                }
            
            if desc and desc.lower() not in ['none', 'null', '', 'undefined']:
                clean_nodes[norm_id]["definitions"].add(desc.strip())
            clean_nodes[norm_id]["mentions"] += 1
            
        except Exception:
            nodos_descartados += 1

    print(f"🔗 Procesando {len(lista_aristas)} posibles conexiones...")
    seen_links = set()
    for a in lista_aristas:
        try:
            u, v = None, None
            if isinstance(a, dict):
                u = a.get('source') or a.get('from') or a.get('origen')
                v = a.get('target') or a.get('to') or a.get('destino')
                if not (u and v):
                    lista = a.get('nodos_involucrados') or a.get('nodos') or a.get('nodes')
                    if isinstance(lista, list) and len(lista) > 1:
                        u, v = lista[0], lista[1]
            elif isinstance(a, list) and len(a) > 1:
                u, v = a[0], a[1]

            if u and v:
                u_norm = limpiar_texto(str(u))
                v_norm = limpiar_texto(str(v))
                
                # Evitar huérfanos y auto-referencias
                if u_norm in clean_nodes and v_norm in clean_nodes and u_norm != v_norm:
                    link_id = tuple(sorted((u_norm, v_norm)))
                    if link_id not in seen_links:
                        clean_edges.append({"source": u_norm, "target": v_norm})
                        seen_links.add(link_id)
                else:
                    aristas_descartadas += 1
            else:
                aristas_descartadas += 1
        except Exception:
            aristas_descartadas += 1

    # Empaquetado Final
    final_output = {
        "metadata": {
            "domain": "Mathematics (ProtoAGI Extracted)",
            "total_nodes": len(clean_nodes),
            "total_edges": len(clean_edges)
        },
        "ontology": {
            "nodes": [
                {
                    "id": k,
                    "label": v["label"],
                    "definitions": list(v["definitions"]),
                    "relevance_score": v["mentions"]
                } 
                for k, v in clean_nodes.items()
            ],
            "edges": clean_edges
        }
    }

    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ KERNEL ENSAMBLADO EXITOSAMENTE: {OUTPUT_FILE}")
    print(f"📊 Conceptos únicos e íntegros: {len(clean_nodes)}")
    print(f"📊 Relaciones válidas consolidadas: {len(clean_edges)}")
    print(f"🗑️  Ruido descartado: {nodos_descartados} nodos fantasmas, {aristas_descartadas} aristas rotas")
    print("="*60)

if __name__ == "__main__":
    assemble()
