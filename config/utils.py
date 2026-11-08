import re

# Lista centralizada de exclusión para todas las tiendas
PALABRAS_EXCLUIDAS = [
    # Servicios y no-hardware
    "ARMADO",
    "SERVICE",
    "INSTALACION",
    "INSTALACIÓN",
    "GARANTIA",
    "GARANTÍA",
    "LICENCIA",
    "ENVIO",
    "ENVÍO",
    "SILLA",
    # Accesorios y fundas
    "FUNDA",
    "APOYA",
    "REPOSAMUÑECA",
    # Eh?
    "ROBOT",
    "CAMISETA",
    "MOCHILA",
    # Cables, adaptadores y extensores
    "CABLE",
    "ADAPTADOR",
    "EXTENSOR",
    "SPLITTER",
    # Almacenamiento menor / Portátil
    "PEN DRIVE",
    "PENDRIVE",
    "MEMORIA MICRO SD",
    "MICROSD",
]


def es_producto_valido(nombre, precio):
    """Filtra servicios, armados e ítems inválidos."""
    try:
        precio_num = float(precio)
        if precio_num <= 0:
            return False
    except (ValueError, TypeError):
        return False

    nombre_upper = nombre.upper()
    for palabra in PALABRAS_EXCLUIDAS:
        if palabra in nombre_upper:
            return False

    return True

# Mapeo global de marcas/fabricantes
FABRICANTES_MAP = {
    "asus": "Asus",
    "gigabyte": "Gigabyte",
    "aorus": "Gigabyte",
    "msi": "MSI",
    "asrock": "AsRock",
    "lenovo": "Lenovo",
    "hp": "HP",
    "dell": "Dell",
    "acer": "Acer",
    "samsung": "Samsung",
    "lg": "LG",
    "hyundai": "Hyundai",
    "viewsonic": "ViewSonic",
    "redragon": "Redragon",
    "logitech": "Logitech",
    "razer": "Razer",
    "corsair": "Corsair",
    "hyperx": "HyperX",
    "kingston": "Kingston",
    "patriot": "Patriot",
    "crucial": "Crucial",
    "adata": "Adata / XPG",
    "xpg": "Adata / XPG",
    "vsg": "VSG",
    "zotac": "Zotac",
    "pny": "PNY",
    "evga": "EVGA",
    "sapphire": "Sapphire",
    "xfx": "XFX",
    "powercolor": "PowerColor",
    "gainward": "Gainward",
    "palit": "Palit",
    "cooler master": "Cooler Master",
    "thermaltake": "Thermaltake"
}

def detectar_marca(nombre_producto: str) -> str:
    nombre_lower = nombre_producto.lower().strip()

    # PRIMERA PRIORIDAD:
    # Evalua Fabricantes_map en primer lugar, buscando la marca por sobre todo.
    for clave, nombre_oficial in FABRICANTES_MAP.items():
        if re.search(r'\b' + re.escape(clave) + r'\b', nombre_lower):
            return nombre_oficial

    # SEGUNDA INSTANCIA:
    # Procesadores. Evalua si es uno, pero excluyendo keywords.
    cpu_real = ("procesador" in nombre_lower or "cpu" in nombre_lower) and not any(
        x in nombre_lower for x in ["cooler", "disipador", "watercooling", "fan", "refrigeracion"]
    )

    if cpu_real:
        if any(re.search(r'\b' + re.escape(k) + r'\b', nombre_lower) for k in ["intel", "core", "pentium", "celeron", "xeon"]):
            return "Intel"
        if any(re.search(r'\b' + re.escape(k) + r'\b', nombre_lower) for k in ["amd", "ryzen", "athlon", "threadripper"]):
            return "AMD"

    # TERCERA INSTANCIA:
    # Fallback en caso de procesadores / gpu con nombres reconocibles.
    if any(re.search(r'\b' + re.escape(k) + r'\b', nombre_lower) for k in ["intel", "core ultra", "core i3", "core i5", "core i7", "core i9"]):
        return "Intel"

    if any(re.search(r'\b' + re.escape(k) + r'\b', nombre_lower) for k in ["amd", "ryzen"]):
        return "AMD"

    if any(re.search(r'\b' + re.escape(k) + r'\b', nombre_lower) for k in ["nvidia", "geforce", "rtx", "gtx"]):
        return "Nvidia"

    return "Genérica"

def categorizar_producto(nombre_producto: str, categoria_original: str = "") -> str:

    texto = nombre_producto.lower().strip()

    # Categorías:
    PREFIJOS = [
        # (Palabras de inicio, Categoría de destino)
        (["gabinete", "gabinetes", "chasis"], "gabinetes"),
        (["teclado", "mouse", "auricular", "auriculares", "microfono", "micrófono", "joystick", "volante", "pad"], "perifericos"),
        (["notebook", "laptop", "netbook"], "notebooks"),
        (["cooler", "disipador", "watercooling", "water cooler", "fan"], "refrigeracion"),
        (["motherboard", "mother", "placa madre"], "motherboards"),
        (["procesador", "cpu"], "procesadores"),
        (["fuente", "fuentes"], "fuentes"),
        (["monitor", "monitores"], "monitores"),
        (["placa de video", "placa de vídeo", "gpu"], "placas_de_video"),
        (["memoria", "ram"], "memorias_ram"),
        (["disco", "ssd", "hd", "hdd"], "almacenamiento"),
        (["kit", "combo", "pc", "pc gamer"], "kits_pc"),
        (["cable", "adaptador", "splitter"], "otros")
    ]

    # Analiza la primera keyword completa del título del producto o si empieza con tal:
    for palabras, cat_destino in PREFIJOS:
        for p in palabras:
            if texto.startswith(f"{p} ") or texto == p:
                return cat_destino

    # Fallback: Si no empieza con la keyword del prefijo, la busca en cualquier parte del texto:
    if categoria_original:
        cat_orig_clean = categoria_original.lower().strip()
        for palabras, cat_destino in PREFIJOS:
            for p in palabras:
                if p in cat_orig_clean:
                    return cat_destino

    return "otros"
