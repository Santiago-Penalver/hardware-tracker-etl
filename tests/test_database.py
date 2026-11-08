import sys
import os
import pytest
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from scrapers.database import guardar_productos, db
from config.logger import config_logger

logger = config_logger("test")

@pytest.fixture(autouse=True)
def limpiar_mock_db():
    """Fixture que limpia los datos de prueba de la base de datos 
    después de que cada test finalice, utilizando el contexto de Flask."""

    yield

    try:
        with app.app_context():
            db.session.execute(
                text("DELETE FROM precios_lista WHERE sku_tienda = 'TEST-RTX-01'")
            )
            db.session.commit()
    except Exception as e:
        logger.warning(f"Advertencia: No se pudo limpiar la db tras el test: {e}")

def test_guardar_productos_estructura_valida():
    """Verifica que la función encargada de guardar en la base de datos 
    acepte una lista de productos con el formato correcto y ejecute sin errores."""
    
    # Crea un producto de prueba simulando la salida exacta del parser
    producto_mock = [{
        "tienda": "TestStore",
        "nombre": "Placa de Video Test RTX",
        "precio": 999999,
        "marca": "Nvidia",
        "categoria": "Placas de Video",
        "link": "https://teststore.com/producto-test",
        "sku_tienda": "TEST-RTX-01"
    }]

    # Ejecuta el guardado y verifica que la fucnión retorne el procesado exitosamente.
    resultado = guardar_productos(producto_mock, "TestStore")
    assert resultado == 1, "Debería haberse procesado o insertado 1 producto correctamente."

    with app.app_context():
        total = db.session.execute(
            text("SELECT count(*) FROM precios_lista WHERE sku_tienda = 'TEST-RTX-01'") 
        ).scalar()

        assert total == 1, "El producto de prueba debería existir en la tabla precios_lista."

def test_guardar_productos_upsert():
    """
    Verifica que si se intenta guardar el mismo producto dos veces 
    (mismo tienda y sku_tienda), se realice un upsert exitoso 
    actualizando los datos sin duplicar filas en la base de datos.
    """
    producto_mock = [{
        "tienda": "TestStore",
        "nombre": "Placa de Video Test RTX",
        "precio": 999999,
        "marca": "Nvidia",
        "categoria": "Placas de Video",
        "link": "https://teststore.com/producto-test",
        "sku_tienda": "TEST-RTX-DUP"
    }]

    # Primera inserción.
    guardar_productos(producto_mock, "TestStore")

    # Segunda inserción con el mismo SKU pero precio actualizado.
    producto_mock_actualizado = [{
        "tienda": "TestStore",
        "nombre": "Placa de Video Test RTX (Actualizada)",
        "precio": 888888,
        "marca": "Nvidia",
        "categoria": "Placas de Video",
        "link": "https://teststore.com/producto-test",
        "sku_tienda": "TEST-RTX-DUP"
    }]
    guardar_productos(producto_mock_actualizado, "TestStore")

    # Verificación en la base de datos.
    with app.app_context():
        # Cuenta cuántos registros existen con ese SKU exacto.
        resultado = db.session.execute(
            text("SELECT COUNT(*) FROM precios_lista WHERE sku_tienda = 'TEST-RTX-DUP'")
        ).scalar()
        
        # Debe haber exactamente 1 solo registro (sin duplicados).
        assert resultado == 1, "El upsert falló y duplicó el producto en la base de datos."
        
        # Verifica que se haya actualizado el precio.
        precio_actual = db.session.execute(
            text("SELECT precio FROM precios_lista WHERE sku_tienda = 'TEST-RTX-DUP'")
        ).scalar()
        assert precio_actual == 888888, "El precio no se actualizó correctamente durante el upsert."