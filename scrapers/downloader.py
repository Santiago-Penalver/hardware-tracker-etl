import sys
import time
import json
import os
import requests
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.logger import config_logger
from config.MultiT_config import TIENDAS

logger = config_logger("downloader")
ua = UserAgent()

@retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True
)

def secure_petition(url, headers):
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    return res

def descargar_categorias(nombre_tienda, slug, cfg):

    headers = {
        "User-Agent": ua.random
    }

    htmls_categoria = []
    pagina = 1
    links_firma = set()
    MAX_PAGES = 30
    
    logger.info(f"Iniciando descarga completa de: [{nombre_tienda.upper()}] -> '{slug}'...\n")
        
    while pagina <= MAX_PAGES:

        url = cfg["url_base"].format(slug=slug, pagina=pagina)

        try:
            res = secure_petition(url, headers=headers)
            
            soup = BeautifulSoup(res.text, "lxml")
            items = soup.select(cfg["selectors"]["card"])
                
            # Primera instancia: Si no hay productos, corta.
            if not items:
                logger.info(f"Final de categoría. (Página {pagina} vacía)")
                break

            links_pagina = set()
            for item in items:
                link_tag = item.select_one(cfg["selectors"]["link"])
                if link_tag and link_tag.get("href"):
                    links_pagina.add(link_tag["href"])
            
            # Segunda instancia: En casos de desastres como Venex, si la página es igual a la anterior debido a fallbacks o bugs. Corta. (ej: si la pagina 15 es idéntica a la 14).
            # O si después de la página 1, la web nos pateó de nuevo exactamente a los productos de la página 1.
            if links_pagina and links_pagina.issubset(links_firma):
                logger.info(f"Final de categoría. [{nombre_tienda.upper()}] '{slug}' (Redirección / Repetición)")
                break
            
            # Guardado de la "firma" para comparar en la próxima página.
            links_firma.update(links_pagina)

            # Guardado del HTML
            htmls_categoria.append({
                "tienda": nombre_tienda,
                "categoria_slug": slug,
                "pagina": pagina,
                "html": res.text
            })
            
            pagina += 1
            time.sleep(0.2)
                
        except Exception as e:
            logger.error(f"Exception en [{nombre_tienda.upper()}] '{slug}' (Pág {pagina}): {e}")
            break
            
    return htmls_categoria

def sitio_api(cfg):
    headers = {"User-Agent": ua.random}
    logger.info("Iniciando descarga de API Compra Gamer...")
    try:
        res = secure_petition(cfg["url_api"], headers=headers)
        # Devuelve el payload del JSON para ser guardado.
        return res.json()
    except Exception as e:
        logger.error(f"Error descargando Compra Gamer: {e}")
    return []

def descargar_tienda_multithread(nombre_tienda, max_workers=8):
    """Lanza hilos en paralelo para descargar todas las categorías de una tienda."""
    if nombre_tienda not in TIENDAS:
        logger.warning(f"❌ La tienda '{nombre_tienda}' no existe en el config.")
        return

    # Para evitar desorden, se guarda en una carpeta llamada "json_download".
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "json_download")
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{nombre_tienda}_raw.json")

    cfg = TIENDAS[nombre_tienda]
    inicio_page = time.time()

    try:
        ## CASO 1: TIENDAS API / JSON (Compra Gamer)
        if cfg.get("tipo") == "json":
            data = sitio_api(cfg)
            if not data:
                raise ValueError("La API devolvió datos nulos.")
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            fin_page = time.time()
            logger.info(f"\n⚡ [{nombre_tienda.upper()}] Completado en {fin_page - inicio_page:.2f} segundos.")
            logger.info(f"💾 Guardado en '{filepath}'.\n")

        ## CASO 2: TIENDAS HTML (Mexx, Venex)
        else:
            htmls_totales = []
            logger.info(f"⚡ Iniciando descarga paralela de [{nombre_tienda.upper()}] con {max_workers} hilos...\n")

            # Usamos ThreadPoolExecutor para procesar múltiples categorías simultáneamente
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Reparte un hilo por cada categoría para hacerlo en simultáneo.
                futures = {
                    executor.submit(descargar_categorias, nombre_tienda, slug, cfg): slug 
                    for slug in cfg["categorias"]
                }

                # Recolecta los resultados a medida que va terminando.
                for future in as_completed(futures):
                    slug = futures[future]
                    try:
                        resultado = future.result()
                        htmls_totales.extend(resultado)
                        logger.info(f"Categoría '{slug}' lista ({len(resultado)} páginas).")
                    except Exception as e:
                        logger.error(f"Excepción grave en categoría '{slug}': {e}")

                if not htmls_totales:
                    raise ValueError ("No se pudo descargar HTML en ninguna categoría.")

                # Guardado único al finalizar todos los hilos.
        
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(htmls_totales, f, ensure_ascii=False)

                    fin_page = time.time()
                    logger.info(f"\n🎉 [{nombre_tienda.upper()}] Completado en {fin_page - inicio_page:.2f} segundos.")
                    logger.info(f"💾 Guardado en '{filepath}'.\n")

    except Exception as e:
        logger.error(f"Fallo crítico en el proceso de {nombre_tienda}: {e}")

        if os.path.exists(filepath):
            logger.warning(f"[FALLBACK] Se utilizará el último caché disponible para '{nombre_tienda}' en '{filepath}'.")
        else:
            logger.error(f"[FALLBACK] No existe caché previo para '{nombre_tienda}'.")

if __name__ == "__main__":
    for tienda in TIENDAS.keys():
        descargar_tienda_multithread(tienda, max_workers=8)