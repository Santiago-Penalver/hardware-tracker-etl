import re

TIENDAS = {
    "venex": {
        "url_base": "https://www.venex.com.ar/{slug}?limit=96&page={pagina}",
        "categorias": [
            "componentes-de-pc",
            "pc-de-escritorio",
            "monitores",
            "perifericos",
            "notebooks",
            "conectividad-y-redes",
            "impresion-y-scanners",
            "almacenamiento-portatil",
            "televisores-y-tv-box",
            "camaras-ip",
            "estabilizadores-ups-y-zapatillas"
        ],
        "selectors": {
            "card": ".product-box",
            "titulo": ".product-box-title a",
            "precio": ".product-box-price",
            "link": ".product-box-title a[href]",
           "id": {
                "selector": ".product-box-title a[onclick]",
                "attr": "onclick",
                "regex": r'"id":"(\d+)"'
            }
        }
    },
    "mexx": {
        "url_base": "https://www.mexx.com.ar/productos-rubro/{slug}/?pagina={pagina}",
        "categorias": [
            "notebooks",
            "placas-de-video",
            "monitores",
            "pcs-all-in-one-",
            "gabinetes",
            "impresoras-y-plotters",
            "pcs-mini-",
            "fuentes-de-poder",
            "conectividad",
            "combos-actualizacion-pc",
            "refrigeracion",
            "ups-y-estabilizadores",
            "motherboards",
            "teclados,-mouses-y-pads",
            "tv-",
            "procesadores",
            "auriculares-y-microfonos-",
            "outlet",
            "memorias-ram",
            "parlantes-y-audio",
            "almacenamiento",
            "camaras-web-e-ip"
        ],
        "selectors": {
            "card": ".contenidos, .card-ecommerce",
            "titulo": ".card-title, .title, .h4, .product-title",
            "precio": ".card-footer, .price, .h4",
            "link": "a[href]",
            "id": ".card-description, .pull-center"
        }
        
    },
    "compragamer": {
        "url_api": "https://static.compragamer.com/productos",
        "tipo": "json",
        "categorias": [],
        "keys": {
            "titulo": "nombre",
            "precio_oferta": "precioEspecial",
            "precio_lista": "precioLista",
            "categoria": "categoria",
            "id": "id_producto"
        }
    }
}

def obtener_id_generico(card, config_id):
    """En casos extremos (Venex), donde su id no está en un span solitario sino que es un dato "sucio", aplica el regex."""
    if not config_id:
        return None
    
    elem = card.select_one(config_id["selector"])
    if not elem:
        return None
        
    # Obtiene el valor id (sea texto o un atributo HTML como onclick/href)
    attr = config_id.get("attr")
    valor_raw = elem.get_text() if attr == "text" else elem.get(attr, "")
    if not valor_raw:
        return None
    
    # Aplica la regla de Regex para aislar los dígitos del ID
    patron = config_id.get("regex")
    if patron:
        match = re.search(patron, valor_raw)
        if match:
            # Si la regex define un grupo de captura (...), devolvemos ese grupo, si no el match entero.
            return match.group(1) if match.groups() else match.group(0)
        return None
    
    return valor_raw.strip()