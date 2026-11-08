import pytest
from alembic.config import Config
from alembic import command

@pytest.fixture
def alembic_config_temp(tmp_path):
    """Fixture que configura Alembic para que trabaje sobre una 
    base de datos SQLite temporal y aislada exclusivamente para el test."""

    db_file = tmp_path / "test_migraciones.db"
    db_url = f"sqlite:///{db_file}"

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", db_url)
    
    return config

def test_migraciones_upgrade(alembic_config_temp):
    """Verifica que las migraciones de Alembic puedan aplicarse 
    de cero (head) sin romper la estructura de las tablas."""

    command.upgrade(alembic_config_temp, "head")

def test_migraciones_upgrade_y_downgrade(alembic_config_temp):
    """Verifica la ida y vuelta: sube hasta el tope, 
    baja hasta la base y vuelve a subir limpiamente."""

    # Sube a la última versión.
    command.upgrade(alembic_config_temp, "head")
    
    # Deshacer todas las migraciones (vuelve a cero).
    command.downgrade(alembic_config_temp, "base")
    
    # Vuelve a aplicar las migraciones para asegurar que el ciclo es robusto.
    command.upgrade(alembic_config_temp, "head")