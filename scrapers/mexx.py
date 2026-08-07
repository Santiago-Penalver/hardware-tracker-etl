import requests
import builtins
from bs4 import BeautifulSoup
import sqlite3
import time
import random
from datetime import datetime
from fake_useragent import UserAgent
from utils import es_producto_valido, detectar_marca, categorizar_producto


# Diccionario de rubros de Mexx
CATEGORIAS = {
    "motherboards": "Motherboards",
    "procesadores": "Procesadores",
    "memorias-ram": "Memorias Ram",
    "almacenamiento": "Almacenamiento",
    "placas-de-video": "Placas de Video",
    "fuentes-de-poder": "Fuentes de Poder",
    "gabinetes": "Gabinetes",
    "refrigeracion-pc": "Refrigeración PC",
    "combos-actualizacion-pc": "Combos Actualización",
    "teclados,-mouses-y-pads": "Teclados y Mouses",
    "auriculares-y-microfonos-": "Audio y Microfonos",
    "parlantes-y-audio": "Audio y Microfonos",
    "monitores": "Monitores"
}


def actualizar_mexx():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contador = 0
    ua = UserAgent()
    session = requests.Session()

    conexion = sqlite3.connect("hardware_tracker.db")
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios_lista (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            precio REAL,
            marca TEXT,
            fecha TEXT,
            categoria TEXT,
            tienda TEXT
        )
    """)
    cursor.execute("DELETE FROM precios_lista WHERE tienda = 'Mexx'")

    # Bucle principal por categoría
    for rubro, nombre_cat in CATEGORIAS.items():
        print(f"\n=== Iniciando la extracción de la categoría: {nombre_cat} ===")
        num_pagina = 1

        while True:
            url_completa = f"https://www.mexx.com.ar/productos-rubro/{rubro}/?pagina={num_pagina}"
            print(f"Extrayendo información de {url_completa}...")

            # User Agents dinámicos para que no nos bloqueen el acceso
            headers = {
                "User-Agent": ua.random,
                "Accept-Language": "es-ES,es;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

            try:
                respuesta = session.get(url_completa, headers=headers, timeout=10)

                if respuesta.status_code == 200:
                    # lmxl es mas rápido que html.parser. En vez de una hora, tardo 5 o 6 min como mucho.
                    soup = BeautifulSoup(respuesta.text, "lxml")
                    productos_lista = soup.select("div[class*='card-ecommerce']")

                    if not productos_lista:
                        print(f"No se encontraron más productos en {nombre_cat}. Pasando a la siguiente categoría.")
                        break

                    for prod in productos_lista:
                        tag_name = prod.find("h4") or prod.find(class_=lambda x: x and 'title' in x)
                        tag_price = prod.find("h3") or prod.find(class_=lambda x: x and 'price' in x)

                        if tag_name and tag_price:

                            nombre = tag_name.text.strip()
                            precio_real = tag_price.text.replace("$", "").replace(".", "").replace(",", ".").strip()

                            try:
                                precio = builtins.float(precio_real)
                            except ValueError:
                                precio = 0.0

                            # 1. Validamos que sea un producto útil
                            if not es_producto_valido(nombre, precio):
                                continue

                            # 2. Detectamos la marca (utilizando la función modularizada en utils.py)
                            marca = detectar_marca(nombre)

                            categoria = categorizar_producto(nombre_producto=nombre, categoria_original=nombre_cat)

                            cursor.execute(
                                "INSERT INTO precios_lista (nombre, precio, marca, fecha, categoria, tienda) VALUES (?, ?, ?, ?, ?, ?)",
                                (nombre, precio, marca, fecha_hoy, categoria, "Mexx")
                            )
                            contador += 1
                            print(f"Guardado {nombre[:40]}... | ${precio} [{marca} - {categoria}]")

                    conexion.commit()

                    # Pausa optimizada, utilizando sólo una vez, en vez de las dos veces de antes
                    tiempo_espera = random.uniform(2.5, 4.0)
                    time.sleep(tiempo_espera)

                elif respuesta.status_code == 403:
                    print("El servidor rechazó la conexión (403 Forbidden).")
                    conexion.close()
                    return False
                elif respuesta.status_code == 404:
                    print("Servidor no encontrado (404 Not found).")
                    break
                else:
                    print(f"Error de conexión con el servidor. Código de estado: {respuesta.status_code}")
                    conexion.close()
                    return False

            except Exception as e:
                print(f"Error en el scraper (Mexx): {e}")
                conexion.close()
                return False

            num_pagina += 1

    conexion.close()
    print(f"\n¡Se actualizaron {contador} productos de Mexx en la base de datos!")
    return True


if __name__ == '__main__':
    print("Iniciando el script manualmente...")
    actualizar_mexx()