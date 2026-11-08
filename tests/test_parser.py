import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.parser import limpiar_precio, procesar_json

# TEST PARA LIMPIAR PRECIO:
@pytest.mark.parametrize(
    "precio_entrada, esperado",
    [
        ("$ 150.999,00", 150999),
        ("1.500", 1500),
        ("$45.999", 45999),
        ("12345", 12345),
        ("", 0),
        (None, 0),
        ("Precio no disponible", 0),
    ],
)
def test_limpiar_precio(precio_entrada, esperado):
    """Verifica que la función limpiar_precio convierta correctamente 
    diferentes formatos de texto en números enteros limpios."""
    resultado = limpiar_precio(precio_entrada)
    assert resultado == esperado

# TEST PARA EL PARSEO DE TIENDAS (HTML/API):
@pytest.mark.parametrize("tienda", ["compragamer", "mexx", "venex"])
def test_procesar_json_estructura(tienda):
    """Verifica que procesar_json lea el archivo crudo local, 
    ejecute el parser correspondiente y devuelva una lista de productos válida."""
    
    # Ejecuta el parser con el caché local disponible.
    productos = procesar_json(tienda)
    
    # Validaciones fundamentales que aseguran la salud de los datos.
    assert isinstance(productos, list), f"El parser de {tienda} debe retornar una lista."
    
    if len(productos) > 0:
        # Si hay productos procesados, valida que tengan las claves obligatorias para la DB.
        primer_producto = productos[0]
        claves_esperadas = {"tienda", "nombre", "precio", "marca", "categoria", "link", "sku_tienda"}
        
        assert claves_esperadas.issubset(primer_producto.keys()), \
            f"Al producto le faltan claves requeridas. Claves encontradas: {primer_producto.keys()}"
        
        # Validaciones lógicas de calidad de datos
        assert isinstance(primer_producto["precio"], int), "El precio debe ser un número entero limpio."
        assert primer_producto["precio"] >= 0, "El precio no puede ser negativo."
        assert len(primer_producto["nombre"]) > 0, "El nombre del producto no puede estar vacío."