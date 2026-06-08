import json
import requests
import os
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "intuyt:macro"
INPUT_FILE = "khan1.txt"
OUTPUT_FILE = "hiperontologia_final.json"
CHUNK_SIZE = 10000 

hiperontologia_total = {"dominio": "Matemáticas", "nodos": [], "hiperaristas": []}
nodos_vistos = set()

def limpiar_y_reparar_json(texto):
    texto = re.sub(r'```json\s*|\s*```', '', texto)
    inicio = texto.find('{')
    fin = texto.rfind('}') + 1
    if inicio != -1 and fin > inicio:
        return texto[inicio:fin]
    return texto

def procesar_fragmento(texto):
    # Prompt más estricto con el formato
    prompt = f"""Extrae conceptos matemáticos. 
RESPUESTA ÚNICAMENTE EN JSON. 
ESTRUCTURA: {{"nodos": [{{"id": "id", "label": "nombre", "desc": "definicion"}}], "hiperaristas": []}}
Texto: {texto[:2500]}"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_gpu": -1, "temperature": 0.1, "num_ctx": 8192}
    }
    
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=180)
        raw = r.json().get('response', '')
        return json.loads(limpiar_y_reparar_json(raw))
    except:
        return None

def main():
    global nodos_vistos
    fragmentos = 0
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} no encontrado.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        print("🚀 Extracción Inmune Iniciada (2x MI210X)...")
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk: break
            
            fragmentos += 1
            print(f"📦 Fragmento #{fragmentos}...", end="\r")
            
            res = procesar_fragmento(chunk)
            if res and isinstance(res, dict):
                # Obtener nodos de forma segura
                nodos_raw = res.get("nodos") or res.get("nodes") or []
                aristas = res.get("hiperaristas") or res.get("edges") or []
                
                if isinstance(nodos_raw, list):
                    for n in nodos_raw:
                        # Si el modelo mandó un diccionario (Correcto)
                        if isinstance(n, dict):
                            nid = n.get('id') or n.get('label')
                            if nid and nid not in nodos_vistos:
                                hiperontologia_total["nodos"].append(n)
                                nodos_vistos.add(nid)
                        # Si el modelo mandó un string (Bypass de error)
                        elif isinstance(n, str):
                            if n not in nodos_vistos:
                                node_obj = {"id": n.lower().replace(" ", "_"), "label": n, "desc": "Extraído como texto plano"}
                                hiperontologia_total["nodos"].append(node_obj)
                                nodos_vistos.add(n)

                if isinstance(aristas, list):
                    hiperontologia_total["hiperaristas"].extend(aristas)

                if fragmentos % 10 == 0:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
                        json.dump(hiperontologia_total, out, ensure_ascii=False, indent=2)
                    print(f"\n💾 Checkpoint #{fragmentos}: {len(nodos_vistos)} nodos acumulados.")

    # Guardado final
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        json.dump(hiperontologia_total, out, ensure_ascii=False, indent=2)
    print(f"\n✅ Proceso terminado. Total: {len(nodos_vistos)} nodos.")

if __name__ == "__main__":
    main()
