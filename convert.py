import json
import yaml

def txt_to_yaml_in_json(input_txt_path, output_json_path):
    print(f"Leyendo el archivo: {input_txt_path}...")
    
    # utf-8-sig elimina automáticamente los caracteres BOM invisibles de Windows
    try:
        with open(input_txt_path, 'r', encoding='utf-8-sig') as f:
            contenido = f.read().strip()
    except UnicodeDecodeError:
        # Si falla, intentamos leerlo como UTF-16 (típico de PowerShell)
        with open(input_txt_path, 'r', encoding='utf-16') as f:
            contenido = f.read().strip()

    # Recortamos estrictamente desde la primera llave '{' hasta la última '}'
    # Esto ignora cualquier texto o basura que se haya colado antes o después del JSON
    inicio = contenido.find('{')
    fin = contenido.rfind('}') + 1
    
    if inicio != -1 and fin != 0:
        contenido = contenido[inicio:fin]

    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError as e:
        print(f"Error parseando el .txt: {e}")
        print(f"\nTe muestro los primeros 100 caracteres que Python está viendo para debugear:")
        print(repr(contenido[:100]))
        return

    datos_compactos = {
        "dominio": datos.get("dominio_detectado", "Desconocido"),
        "nodos": [],
        "aristas": []
    }

    for nodo in datos.get("nodos", []):
        nodo_compacto = {
            "id": nodo.get("id"),
            "lbl": nodo.get("label"),
            "desc": nodo.get("descripcion")
        }
        datos_compactos["nodos"].append(nodo_compacto)

    for arista in datos.get("hiperaristas", []):
        arista_compacta = {
            "rel": arista.get("tipo_relacion"),
            "nodos": arista.get("nodos_involucrados"),
            "ctx": arista.get("contexto")
        }
        datos_compactos["aristas"].append(arista_compacta)

    yaml_string = yaml.dump(
        datos_compactos,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False
    )

    salida_json = {
        "documento": "hiperontologia_optimizada",
        "formato_payload": "yaml",
        "contexto_yaml": yaml_string
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(salida_json, f, ensure_ascii=False, indent=2)

    print(f"¡Éxito! Archivo guardado determinísticamente en: {output_json_path}")

if __name__ == "__main__":
    txt_to_yaml_in_json("khan1.txt", "khan1_optimizado.json")
