import os
import math

from datetime import datetime
from flask import Flask, render_template, request, jsonify
from scrapers.database import db, PrecioLista, HistorialPrecio

app = Flask(__name__)

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port =  os.getenv("DB_PORT")
db_name =  os.getenv("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route("/")
def index():
    marca_indicada = "Todo"
    categoria_indicada = "Todo"
    tienda_indicada = "Todo"
    pagina = 1
    por_pagina = 12
    offset = 0

    ultimo_prod = PrecioLista.query.order_by(PrecioLista.fecha_actualizacion.desc()).first()
    timestamp_db = ultimo_prod.fecha_actualizacion if ultimo_prod else None

    if timestamp_db:
        iso_timestamp = timestamp_db.replace(" ", "T")
    else:
        iso_timestamp = datetime.now().isoformat()

    query_base = PrecioLista.query

    # Total general
    total_productos = query_base.count()
    total_paginas = math.ceil(total_productos / por_pagina) if total_productos > 0 else 1

    # --- Totales específicos por marca/categoría ---
    
    total_amd = PrecioLista.query.filter(
        db.or_(db.func.lower(PrecioLista.nombre).like('%ryzen%'), db.func.lower(PrecioLista.marca).like('%amd%'))
    ).count()

    total_intel = PrecioLista.query.filter(
        db.or_(db.func.lower(PrecioLista.nombre).like('%intel%'), db.func.lower(PrecioLista.nombre).like('%core%'))
    ).count()

    total_asus = PrecioLista.query.filter(
        db.or_(db.func.lower(PrecioLista.marca).like('%asus%'), db.func.lower(PrecioLista.nombre).like('%asus%'))
    ).count()

    total_gigabyte = PrecioLista.query.filter(
        db.or_(db.func.lower(PrecioLista.marca).like('%gigabyte%'), db.func.lower(PrecioLista.marca).like('%aorus%'))
    ).count()

    total_msi = PrecioLista.query.filter(
        db.func.lower(PrecioLista.marca).like('%msi%')
    ).count()

    total_kingston = PrecioLista.query.filter(
        db.or_(db.func.lower(PrecioLista.marca).like('%kingston%'), db.func.lower(PrecioLista.marca).like('%hyperx%'))
    ).count()

    total_perifericos_marcas = PrecioLista.query.filter(
        db.or_(
            db.func.lower(PrecioLista.marca).like('%razer%'),
            db.func.lower(PrecioLista.marca).like('%logitech%'),
            db.func.lower(PrecioLista.marca).like('%redragon%')
        )
    ).count()

    # Total otros (marcas que no sean ninguna de las principales)
    total_otros = PrecioLista.query.filter(
        ~db.func.lower(PrecioLista.marca).in_(['amd', 'intel', 'asus', 'gigabyte', 'msi', 'kingston', 'hyperx']),
        ~db.func.lower(PrecioLista.nombre).like('%ryzen%'),
        ~db.func.lower(PrecioLista.nombre).like('%intel%')
    ).count()

    # Productos paginados con la columna tienda incluida
    productos = query_base.order_by(PrecioLista.precio.asc()).offset(offset).limit(por_pagina).all()

    return render_template(
        "index.html",
        productos=productos,
        pagina_actual=pagina,
        sync_time=iso_timestamp,
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

    query = PrecioLista.query

    # Filtro de Tienda
    if tienda_indicada != "Todo":
        query = query.filter(db.func.lower(PrecioLista.tienda) == tienda_indicada.lower().strip())

    # Filtro de Marca
    if marca_indicada != "Todo":
        marca_clean = marca_indicada.lower().strip()
        if "adata" in marca_clean or "xpg" in marca_clean:
            query = query.filter(db.or_(db.func.lower(PrecioLista.marca).like('%adata%'), db.func.lower(PrecioLista.marca).like('%xpg%')))
        elif "gigabyte" in marca_clean or "aorus" in marca_clean:
            query = query.filter(db.or_(db.func.lower(PrecioLista.marca).like('%gigabyte%'), db.func.lower(PrecioLista.marca).like('%aorus%')))
        elif "hyperx" in marca_clean:
            query = query.filter(db.func.lower(PrecioLista.marca).like('%hyperx%'))
        elif "kingston" in marca_clean:
            query = query.filter(db.func.lower(PrecioLista.marca).like('%kingston%'))
        else:
            query = query.filter(db.func.lower(PrecioLista.marca) == marca_clean)

    # Filtro de Categoría
    if categoria_indicada != "Todo":
        cat_limpia = categoria_indicada.lower().strip()
        query = query.filter(db.func.lower(PrecioLista.categoria) == cat_limpia)

    total_productos = query.count()
    total_paginas = math.ceil(total_productos / por_pagina) if total_productos > 0 else 1

    productos = query.order_by(PrecioLista.precio.asc()).offset(offset).limit(por_pagina).all()

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
    producto = PrecioLista.query.get(producto_id)

    if producto:
        return render_template("producto_detalle.html", prod=producto)
    return "<p class='text-gray-400 p-4'>Producto no encontrado</p>"

# Historial de precios para el gráfico cronológico del producto
@app.route("/producto/<int:producto_id>/historial")
def historial_producto(producto_id):
    try:
        # Busca el producto actual para saber su tienda y sku_tienda
        producto = PrecioLista.query.get(producto_id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Consulta el historial usando la combinación correcta
        registros = HistorialPrecio.query.filter_by(
            tienda=producto.tienda,
            sku_tienda=producto.sku_tienda
        ).order_by(HistorialPrecio.fecha_registro.asc()).all()
        
        # Mapea con los nombres reales de las columnas
        fechas = [r.fecha_registro.strftime("%Y-%m-%d %H:%M") for r in registros]
        precios = [r.precio for r in registros]
        
        return jsonify({"fechas": fechas, "precios": precios})
    except Exception as e:
        print(f"ERROR EN HISTORIAL: {e}")
        return jsonify({"error": str(e)}), 500

# Buscador:
@app.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '').strip()
        results = []
        
        if query:
            productos = PrecioLista.query.filter(PrecioLista.nombre.ilike(f"%{query}%")).limit(10).all()
            for p in productos:
                results.append({
                    "tienda": p.tienda,
                    "nombre": p.nombre,
                    "precio": p.precio,
                    "link": p.link
                })
                
        return jsonify(results)
    except Exception as e:
        print(f"ERROR EN API SEARCH: {e}")
        return jsonify({"error": str(e)}), 500
    
# Vaciar. No funcionaba el htmx para cerrar ventana individual así que para eso está sencilla función.
@app.route("/vaciar")
def vaciar_detalle():
    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)