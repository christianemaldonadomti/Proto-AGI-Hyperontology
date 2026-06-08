import json
import requests
import os
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "intuyt:macro" # Puedes cambiarlo si tienes un modelo más rápido para tareas zero-shot
INPUT_FILE = "hiperontologia_final.json"
OUTPUT_FILE = "protoagi_kernel_semantico.json"
BATCH_SIZE = 50 # Cuántos conceptos enviamos a Ollama por petición

def obtener_mapeo_semantico(lista_conceptos):
    """Pide a Ollama que agrupe traducciones y sinónimos en IDs canónicos."""
    prompt = f"""
Actúa como un experto en ontologías matemáticas bilingüe (Inglés/Español).
Se te proporcionará una lista de conceptos extraídos. Tu tarea es normalizarlos.
Identifica sinónimos y traducciones (ej. "Suma", "Addition", "adición") y asígnales un ÚNICO 'Canonical_ID' en inglés y en formato snake_case (ej. "addition").

RESPONDE ÚNICAMENTE CON UN OBJETO JSON plano donde la llave es el concepto original y el valor es el Canonical_ID.
Ejemplo: {{"Suma": "addition", "Addition": "addition", "Triángulo rectángulo": "right_triangle"}}

Conceptos a procesar:
{json.dumps(lista_conceptos, ensure_ascii=False)}
"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_gpu": -1, "temperature": 0.0, "num_ctx": 4096} # Temp 0.0 para máximo determinismo
    }
    
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        raw_resp = r.json().get('response', '')
        # Limpieza rápida por si el LLM pone markdown
        clean_resp = re.sub(r'```json\s*|\s*```', '', raw_resp)
        return json.loads(clean_resp)
    except Exception as e:
        print(f"  [!] Error en el lote de Ollama: {e}")
        return {}

def assemble_semantic():
    if not os.path.exists(INPUT_FILE):
        print("❌ Archivo base no encontrado.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        # Carga tolerante (asumiendo que el JSON está bien formado por los scripts anteriores)
        raw_data = json.load(f)

    print("🧠 Iniciando Ensamble Semántico asistido por LLM...")

    # 1. Recopilar todos los conceptos crudos
    nodos_raw = raw_data.get('nodos', []) + raw_data.get('nodes', [])
    etiquetas_unicas = set()
    diccionario_nodos_originales = {} # Para conservar descripciones

    for n in nodos_raw:
        if isinstance(n, dict):
            lbl = str(n.get('label') or n.get('id') or "").strip()
            desc = n.get('desc') or n.get('descripcion') or ""
        else:
            lbl = str(n).strip()
            desc = ""
        
        if lbl:
            etiquetas_unicas.add(lbl)
            if lbl not in diccionario_nodos_originales:
                diccionario_nodos_originales[lbl] = {"desc": set(), "mentions": 0}
            if desc:
                diccionario_nodos_originales[lbl]["desc"].add(desc)
            diccionario_nodos_originales[lbl]["mentions"] += 1

    lista_etiquetas = list(etiquetas_unicas)
    total_etiquetas = len(lista_etiquetas)
    print(f"📊 Encontrados {total_etiquetas} conceptos en crudo. Iniciando mapeo semántico por lotes...")

    # 2. Procesamiento por lotes con Ollama
    mapeo_global = {}
    for i in range(0, total_etiquetas, BATCH_SIZE):
        lote = lista_etiquetas[i : i + BATCH_SIZE]
        print(f"  Enviando lote {i//BATCH_SIZE + 1}/{(total_etiquetas//BATCH_SIZE)+1} a las MI210X...", end="\r")
        
        resultado_lote = obtener_mapeo_semantico(lote)
        
        # Si Ollama falla en un lote, usamos un fallback determinista
        for original in lote:
            mapeo_global[original] = resultado_lote.get(original, original.lower().replace(" ", "_"))
            
    print("\n✅ Mapeo semántico completado.")

    # 3. Ensamblar la nueva red usando los IDs canónicos
    nodos_canonic = {}
    
    # Fusionar nodos basados en el mapeo
    for original, data in diccionario_nodos_originales.items():
        canonical_id = mapeo_global.get(original)
        if not canonical_id: continue
        
        if canonical_id not in nodos_canonic:
            nodos_canonic[canonical_id] = {
                "id": canonical_id,
                "label": canonical_id.replace("_", " ").capitalize(), # Etiqueta representativa
                "aliases": set(),
                "definitions": set(),
                "mentions": 0
            }
        
        # Guardar el término original como alias para búsquedas futuras
        if original.lower() != canonical_id.replace("_", " ").lower():
            nodos_canonic[canonical_id]["aliases"].add(original)
            
        nodos_canonic[canonical_id]["definitions"].update(data["desc"])
        nodos_canonic[canonical_id]["mentions"] += data["mentions"]

    # Reconstruir Aristas
    aristas_canonic = []
    seen_edges = set()
    aristas_raw = raw_data.get('hiperaristas', []) + raw_data.get('edges', [])
    
    for a in aristas_raw:
        u, v = None, None
        if isinstance(a, dict):
            u = a.get('source') or a.get('from')
            v = a.get('target') or a.get('to')
        elif isinstance(a, list) and len(a) > 1:
            u, v = a[0], a[1]

        if u and v:
            # Traducir los extremos de la arista usando el mapeo
            u_canonic = mapeo_global.get(str(u).strip())
            v_canonic = mapeo_global.get(str(v).strip())
            
            if u_canonic and v_canonic and u_canonic != v_canonic:
                edge_id = tuple(sorted((u_canonic, v_canonic)))
                if edge_id not in seen_edges:
                    aristas_canonic.append({"source": u_canonic, "target": v_canonic})
                    seen_edges.add(edge_id)

    # 4. Exportar
    final_output = {
        "metadata": {
            "domain": "Mathematics (Semantic Kernel)",
            "total_nodes": len(nodos_canonic),
            "total_edges": len(aristas_canonic)
        },
        "ontology": {
            "nodes": [
                {
                    "id": k,
                    "label": v["label"],
                    "aliases": list(v["aliases"]),
                    "definitions": list(v["definitions"]),
                    "relevance_score": v["mentions"]
                } for k, v in nodos_canonic.items()
            ],
            "edges": aristas_canonic
        }
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n🚀 KERNEL SEMÁNTICO LISTO: {OUTPUT_FILE}")
    print(f"  Nodos reducidos de {total_etiquetas} a {len(nodos_canonic)} entidades únicas.")

if __name__ == "__main__":
    assemble_semantic()
