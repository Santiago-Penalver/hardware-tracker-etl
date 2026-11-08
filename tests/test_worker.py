import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from scrapers.database import db
from config.worker import pipeline_scraping
from config.logger import config_logger

logger = config_logger("test")

@patch("config.worker.guardar_productos")
@patch("config.worker.descargar_tienda_multithread")
def test_pipeline_scraping_flujo_completo(mock_descargar, mock_guardar):
    """Verifica que el pipeline de scraping ejecute la secuencia completa 
    mockeando la red y el guardado en base de datos para proteger los datos reales."""
    
    # Config de los mocks para que actúen de forma simulada.
    mock_descargar.return_value = None
    mock_guardar.return_value = 10  # Simula que guardó productos correctamente.
    
    # Ejecuta el pipeline dentro del contexto de la app de Flask.
    with app.app_context():
        try:
            pipeline_scraping()
            exito = True
        except Exception as e:
            exito = False
            logger.error(f"El pipeline lanzó una excepción: {e}")
            
    assert exito, "El pipeline de scraping debería ejecutarse de punta a punta exitosamente."
    assert mock_guardar.call_count > 0, "El pipeline debió intentar guardar los productos procesados."