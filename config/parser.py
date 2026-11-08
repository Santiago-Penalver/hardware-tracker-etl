import json
import re
import os
from bs4 import BeautifulSoup
from .MultiT_config import TIENDAS, obtener_id_generico
from .utils import es_producto_valido, detectar_marca, categorizar_producto

def limpiar_precio(precio_raw):
    """Convierte strings de precio tipo '$ 150.999,00' en enteros puros (150999)."""
    if not precio_raw:
        return 0
    # Se elimina todo lo que no sea digito.
    numeros = re.sub(r"\D", "", precio_raw.split(",")[0])
    return int(numeros) if numeros else 0

def ruta_api(nombre_tienda, pages_raw, config_tienda):
    """Para casos de API (ej: Compra Gamer)"""
    productos = []
    keys = config_tienda.get("keys", {})

    for item in pages_raw:
        nombre = item.get(keys.get("titulo")) or item.get("nombre") or item.get("titulo") or ""
        precio = item.get(keys.get("precio_oferta")) or item.get(keys.get("precios_lista")) or 0
        sku_tienda = str(item.get(keys.get("id")) or item.get("id_producto") or item.get("id") or "")
        cat_slug = str(item.get(keys.get("categoria"), ""))

        nombre_slug = nombre.replace(" ", "_") if nombre else ""
        link = f"https://compragamer.com/producto/{nombre}_{sku_tienda}" if sku_tienda else ""

        if not nombre or nombre.isdigit() or not link or precio <= 0:
            continue

        if not es_producto_valido(nombre, precio):
            continue

        marca = detectar_marca(nombre)
        cat_limpia = categorizar_producto(nombre, cat_slug)

        productos.append({
            "tienda": nombre_tienda,
            "nombre": nombre,
            "precio": int(precio),
            "marca": marca,
            "categoria": cat_limpia,
            "link": link,
            "sku_tienda": sku_tienda
        })
    return productos

def ruta_html(nombre_tienda, pages_raw, config_tienda):
    """Para casos de HTML (ej: Mexx, Venex)."""

    selectors = config_tienda["selectors"]
    productos = []

    for item_page in pages_raw:
        cat_slug_original = item_page.get("categoria_slug", "")
        html_content = item_page.get("html", "")

        soup = BeautifulSoup(html_content, "lxml")
        cards = soup.select(selectors["card"])

        for card in cards:
            # Extracción raw de elementos
            tag_titulo = card.select_one(selectors["titulo"])
            nombre = tag_titulo.get_text(strip=True) if tag_titulo else None

            tag_precio = card.select_one(selectors["precio"])
            precio_raw = tag_precio.get_text(strip=True) if tag_precio else None
            precio = limpiar_precio(precio_raw)

            tag_link = card.select_one(selectors["link"])
            link = tag_link["href"] if tag_link and tag_link.get("href") else None

            # Normaliza la URL del link.
            if link and link.startswith("/"):
                host_base = "/".join(TIENDAS[nombre_tienda]["url_base"].split("/")[:3])
                link = f"{host_base}{link}"

            config_id = selectors.get("id")

            # Primera instancia: Si config_id es un string simple de selector (ej: ".card-description .pull-center").
            if isinstance(config_id, str):
                tag_id = card.select_one(config_id)
                sku_tienda = re.sub(r"\D", "", tag_id.get_text()) if tag_id else None
            # Segunda instancia: Si es el diccionario con metadatos (selector, attr, regex).
            elif isinstance(config_id, dict):
                sku_tienda = obtener_id_generico(card, config_id)
            else:
                sku_tienda = None

            sku_tienda = str(sku_tienda or "").strip()

            # Filtrado inicial
            if not nombre or nombre.isdigit() or not sku_tienda or not link or precio <= 0:
                continue

            # Filtrado de palabras excluyentes
            if not es_producto_valido(nombre, precio):
                continue

            # Filtrado universal con Utils (Marca y Categoría).
            marca = detectar_marca(nombre)
            categoria_global = categorizar_producto(nombre, cat_slug_original)

            productos.append({
                "tienda": nombre_tienda,
                "nombre": nombre,
                "precio": precio,
                "marca": marca,
                "categoria": categoria_global,
                "link": link,
                "sku_tienda": sku_tienda
            })

    return productos

def procesar_json(nombre_tienda):
    """Según la instancia y el tipo de página, realiza el filtro de alguna de las dos rutas correspondientes. Luego procede a guardar el JSON."""

    nombre_key = nombre_tienda.lower().replace(" ", "")
    # Busca la carpeta de los Json guardados.
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "json_download")

    if nombre_key not in TIENDAS:
        print(f"Error. La tienda '{nombre_tienda}' no está en la configuración.")
        return []

    config_tienda = TIENDAS[nombre_key]
    # Busca el archivo dentro de la carpeta.
    archivo_load = os.path.join(DATA_DIR, f"{nombre_tienda}_raw.json")
    if not os.path.exists(archivo_load):
        print(f"Archivo no encontrado: {archivo_load}")
        return []

    try:
        with open (archivo_load, "r", encoding="utf-8") as f:
            data_raw = json.load(f)
    except FileNotFoundError:
        print(f"Error. El archivo '{archivo_load}' no ha sido encontrado. Ejecuta downloader.py primero.")
        return []

    print(f"Procesando [{nombre_key.upper()}] desde '{archivo_load}'...")

    # Pequeño call al MultiT_config, acá orquesta la ruta del parseo.
    if config_tienda.get("tipo") == "json":
        productos = ruta_api(nombre_key, data_raw, config_tienda)
    else:
        productos = ruta_html(nombre_key, data_raw, config_tienda)

    print(f"[{nombre_key.upper()}] Finalizado. {len(productos)} productos válidos extraídos.\n")
    return productos

if __name__ == "__main__":
    # Muestra un producto para chequear el parser.
    prods_venex = procesar_json("venex")

    prods_mexx = procesar_json("mexx")

    prods_cgamer = procesar_json("compragamer")

    if prods_venex:
        print("📌 Ejemplo Venex procesado:")
        print(prods_venex[0])

    if prods_mexx:
        print("\n📌 Ejemplo Mexx procesado:")
        print(prods_mexx[0])

    if prods_cgamer:
        print("\n📌 Ejemplo Compra Gamer procesado:")
        print(prods_cgamer[0])