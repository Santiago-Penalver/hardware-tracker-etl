import math
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


def productos_tracker_db():
    try:
        conexion = sqlite3.connect("hardware_tracker.db")
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT id, nombre, precio, marca, fecha, categoria, tienda FROM precios_lista ORDER BY precio ASC"
        )
        productos = cursor.fetchall()

        conexion.close()
        return productos
    except sqlite3.OperationalError:
        return []


@app.route("/")
def index():
    marca_indicada = "Todo"
    categoria_indicada = "Todo"
    tienda_indicada = "Todo"
    pagina = 1
    por_pagina = 12
    offset = 0

    conexion = sqlite3.connect("hardware_tracker.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    query_base = "FROM precios_lista WHERE 1=1"

    # Total general
    cursor.execute(f"SELECT COUNT(*) {query_base}")
    total_productos = cursor.fetchone()[0]
    total_paginas = (
        math.ceil(total_productos / por_pagina) if total_productos > 0 else 1
    )

    # --- Totales específicos por marca/categoría ---
    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(nombre) LIKE '%ryzen%' OR LOWER(marca) LIKE '%amd%'"
    )
    total_amd = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(nombre) LIKE '%intel%' OR LOWER(nombre) LIKE '%core%'"
    )
    total_intel = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(marca) LIKE '%asus%' OR LOWER(nombre) LIKE '%asus%'"
    )
    total_asus = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(marca) LIKE '%gigabyte%' OR LOWER(nombre) LIKE '%aorus%' OR LOWER(nombre) LIKE '%gigabyte%'"
    )
    total_gigabyte = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(marca) LIKE '%msi%' OR LOWER(nombre) LIKE '%msi%'"
    )
    total_msi = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(marca) LIKE '%kingston%' OR LOWER(marca) LIKE '%hyperx%'"
    )
    total_kingston = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM precios_lista WHERE LOWER(marca) LIKE '%razer%' OR LOWER(marca) LIKE '%logitech%' OR LOWER(marca) LIKE '%redragon%'"
    )
    total_perifericos_marcas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM precios_lista 
        WHERE LOWER(marca) NOT IN ('amd', 'intel', 'asus', 'gigabyte', 'msi', 'kingston', 'hyperx')
        AND LOWER(nombre) NOT LIKE '%ryzen%'
        AND LOWER(nombre) NOT LIKE '%intel%'
    """)
    total_otros = cursor.fetchone()[0]

    # Productos paginados con la columna tienda incluida
    query_final = f"SELECT id, nombre, precio, marca, fecha, categoria, tienda {query_base} ORDER BY precio ASC LIMIT ? OFFSET ?"
    cursor.execute(query_final, (por_pagina, offset))
    productos = cursor.fetchall()
    conexion.close()

    return render_template(
        "index.html",
        productos=productos,
        pagina_actual=pagina,
        total_paginas=total_paginas,
        total_productos=total_productos,
        total_amd=total_amd,
        total_intel=total_intel,
        total_asus=total_asus,
        total_gigabyte=total_gigabyte,
        total_msi=total_msi,
        total_kingston=total_kingston,
        total_perifericos_marcas=total_perifericos_marcas,
        total_otros=total_otros,
        marca_actual=marca_indicada,
        categoria_actual=categoria_indicada,
        tienda_actual=tienda_indicada
    )


@app.route("/filtrar")
def filtrar_productos():
    marca_indicada = request.args.get("marca", "Todo")
    categoria_indicada = request.args.get("categoria", "Todo")
    tienda_indicada = request.args.get("tienda", "Todo")

    # Paginación
    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = 12
    offset = (pagina - 1) * por_pagina

    conexion = sqlite3.connect("hardware_tracker.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    query_base = "FROM precios_lista WHERE 1=1"
    params = []

    # Filtro de Tienda
    if tienda_indicada != "Todo":
        query_base += " AND LOWER(tienda) = ?"
        params.append(tienda_indicada.lower().strip())

    # Filtro de Marca
    if marca_indicada != "Todo":
        marca_clean = marca_indicada.lower().strip()
        if "adata" in marca_clean or "xpg" in marca_clean:
            query_base += " AND (LOWER(marca) LIKE '%adata%' OR LOWER(marca) LIKE '%xpg%')"
        elif "gigabyte" in marca_clean or "aorus" in marca_clean:
            query_base += " AND (LOWER(marca) LIKE '%gigabyte%' OR LOWER(marca) LIKE '%aorus%')"
        elif "hyperx" in marca_clean:
            query_base += " AND LOWER(marca) LIKE '%hyperx%'"
        elif "kingston" in marca_clean:
            query_base += " AND LOWER(marca) LIKE '%kingston%'"
        else:
            query_base += " AND LOWER(marca) = ?"
            params.append(marca_clean)

    # Filtro de Categoría
    if categoria_indicada != "Todo":
        cat_limpia = categoria_indicada.lower().strip()
        query_base += " AND LOWER(categoria) = ?"
        params.append(cat_limpia)

    cursor.execute(f"SELECT COUNT(*) {query_base}", params)
    total_productos = cursor.fetchone()[0]
    total_paginas = (
        math.ceil(total_productos / por_pagina) if total_productos > 0 else 1
    )

    query_final = f"SELECT id, nombre, precio, marca, fecha, categoria, tienda {query_base} ORDER BY precio ASC LIMIT ? OFFSET ?"
    params_final = params + [por_pagina, offset]

    cursor.execute(query_final, params_final)
    productos = cursor.fetchall()
    conexion.close()

    return render_template(
        "productos_cards.html",
        productos=productos,
        pagina_actual=pagina,
        total_paginas=total_paginas,
        marca_actual=marca_indicada,
        categoria_actual=categoria_indicada,
        tienda_actual=tienda_indicada
    )

# ID del producto:
@app.route("/detalle/<int:producto_id>")
def producto_seleccionado(producto_id):
    conexion = sqlite3.connect("hardware_tracker.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT id, nombre, precio, marca, fecha, categoria, tienda FROM precios_lista WHERE id = ?",
        (producto_id,),
    )
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        return render_template("producto_detalle.html", prod=producto)
    return "<p class='text-gray-400 p-4'>Producto no encontrado</p>"

# Vaciar. No funcionaba el htmx para cerrar ventana individual así que para eso está sencilla función.
@app.route("/vaciar")
def vaciar_detalle():
    return ""


if __name__ == "__main__":
    app.run(debug=True, port=5000)