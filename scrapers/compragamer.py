import sqlite3
import requests
from datetime import datetime
from fake_useragent import UserAgent
from utils import es_producto_valido, detectar_marca, categorizar_producto

def actualizar_compragamer():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contador = 0
    ua = UserAgent()
    url_api = "https://static.compragamer.com/productos"
    
    headers = {
        "User-Agent": ua.random,
        "Referer": "https://compragamer.com/"
    }
    
    print("=== Iniciando la extracción filtrada de Compra Gamer ===")
    try:
        respuesta = requests.get(url_api, headers=headers, timeout=15)
        if respuesta.status_code == 200:
            productos = respuesta.json()
            
            conexion = sqlite3.connect("hardware_tracker.db")
            cursor = conexion.cursor()
            
            cursor.execute("DELETE FROM precios_lista WHERE tienda = 'Compra Gamer'")
            
            for prod in productos:
                nombre = prod.get("nombre", "").strip()
                if not nombre:
                    continue
                    
                precio_raw = prod.get("precioEspecial") or prod.get("precioLista") or 0
                try:
                    precio = float(precio_raw)
                except (ValueError, TypeError):
                    precio = 0.0
                    
                # Validaciones y Filtros usando Utils
                if not es_producto_valido(nombre, precio):
                    continue
                    
                marca = detectar_marca(nombre)
                categoria_raw = prod.get("categoria", "")
                categoria = categorizar_producto(nombre, categoria_raw)
                
                cursor.execute("""
                    INSERT INTO precios_lista (nombre, precio, marca, fecha, categoria, tienda)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nombre, precio, marca, fecha_hoy, categoria, "Compra Gamer"))
                
                contador += 1
                print(f"Guardado {nombre[:40]}... | ${precio} [{marca} - {categoria}]")
                
            conexion.commit()
            conexion.close()
            print(f"\n=== Se actualizaron {contador} productos de Compra Gamer ===")
            return True
            
    except Exception as e:
        print(f"Error en el scraper (Compra Gamer): {e}")
        return False

if __name__ == "__main__":
    actualizar_compragamer()