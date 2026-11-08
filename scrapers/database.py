import sys
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.logger import config_logger
from config.parser import procesar_json
from config.MultiT_config import TIENDAS

logger = config_logger("database")

load_dotenv()

db = SQLAlchemy()

class PrecioLista(db.Model):
    __tablename__ = 'precios_lista'

    id = db.Column(db.Integer, primary_key=True)
    sku_tienda =db.Column(db.String(100))
    nombre = db.Column(db.String(255), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    marca =db.Column(db.String(100))
    categoria = db.Column(db.String(100))
    tienda = db.Column(db.String(100))
    link = db.Column(db.String(500))
    fecha_actualizacion = db.Column(db.String(100))

    __table_args__  =(
        db.UniqueConstraint('tienda', 'sku_tienda', name='uix_tienda_sku'),
    )

class HistorialPrecio(db.Model):
    __tablename__ = 'historial_precio'
    
    id = db.Column(db.Integer, primary_key=True)
    tienda = db.Column(db.String(50), nullable=False)
    sku_tienda = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

def guardar_productos(productos, nombre_tienda):
    """Inserta o actualiza la lista de productos procesados."""
    if not productos:
        logger.warning("No hay productos en la base de datos.")
        return 0

    logger.info(f"-> Productos recibidos del parser: {len(productos)}")

    from app import app

    with app.app_context():
        try:

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            vistos = set()
            values_list = []
            historial_list = []

            for p in productos:
                sku = str(p.get('sku_tienda', '')).strip()
                nombre = str(p.get('nombre', '')).strip()

                # Validamos que tengan SKU y nombre válidos antes de agregarlos
                if not sku or not nombre:
                    logger.warning(f"Producto descartado por SKU o nombre vacíos: SKU={sku}, Nombre={nombre}")
                    continue

                # Control anti-duplicados:
                key_unica = (nombre_tienda, sku)
                if key_unica in vistos:
                    continue
                vistos.add(key_unica)

                new_precio = float(p.get('precio') or 0.0)
                link_producto = p.get('link')
                marca = p.get('marca') or 'Genérica'
                categoria = p.get('categoria') or 'Genérica'

                # Tabla principal (Upsert)
                values_list.append({
                    'tienda': nombre_tienda,
                    'sku_tienda': sku,
                    'nombre': nombre,
                    'precio': new_precio,
                    'marca': marca,
                    'categoria': categoria,
                    'link': link_producto,
                    'fecha_actualizacion': timestamp
                })

                # Tabla de historial (Append)
                historial_list.append(
                    HistorialPrecio(
                        tienda=nombre_tienda,
                        sku_tienda=sku,
                        precio=new_precio,
                        fecha_registro=datetime.now()
                    )
                )

            if not values_list:
                return 0

            # Upsert nativo de PostgreSQL
            stmt = pg_insert(PrecioLista).values(values_list)

            # Si se topa con el indice único, actualiza los campos vigentes.
            stmt = stmt.on_conflict_do_update(
                index_elements=['tienda', 'sku_tienda'],
                set_={
                    'nombre': stmt.excluded.nombre,
                    'precio': stmt.excluded.precio,
                    'marca': stmt.excluded.marca,
                    'categoria': stmt.excluded.categoria,
                    'link': stmt.excluded.link,
                    'fecha_actualizacion': stmt.excluded.fecha_actualizacion
                }
            )

            db.session.execute(stmt)

            db.session.bulk_save_objects(historial_list)

            db.session.commit()

            total_procesados = len(values_list)
            logger.info(f"Guardado/Actualización exitoso para '{nombre_tienda}': {total_procesados} productos actualizados y registrados en el historial.")
            return total_procesados
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al guardar en la base de datos para {nombre_tienda}: {e}")
            return 0

if __name__ == "__main__":

    from app import app

    with app.app_context():
        # Crea las tablas en PostgreSQL si no existen.
        db.create_all()
        db.session.commit()
    
    for tienda in TIENDAS.keys():
        productos = procesar_json(tienda)
        guardar_productos(productos, tienda)