import sys
import os
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask

try:
    from config.logger import config_logger
except ModuleNotFoundError:
    from logger import config_logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.downloader import descargar_tienda_multithread, TIENDAS
from scrapers.database import guardar_productos, procesar_json, db

logger = config_logger("worker")

app_worker = Flask(__name__)

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

app_worker.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
db.init_app(app_worker)

def pipeline_scraping():

    logger.info("Iniciando descarga y actualización de datos...")
    inicio = time.time()

    try:
        for tienda in TIENDAS.keys():
            print(f"[1/2] Descargando...{tienda.upper()}")
            descargar_tienda_multithread(tienda, max_workers=8)

            print(f"[2/2] Guardando en base de datos...{tienda.upper()}")
            datos = procesar_json(tienda)
            guardar_productos(datos, tienda)

        final = time.time()
        logger.info("Datos guardados con éxito.")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    logger.info("Verificando y creando tablas en la base de datos...")
    with app_worker.app_context():
        db.create_all()

    logger.info("Worker: Ejecución inicial al arrancar...")
    pipeline_scraping()

    scheduler = BlockingScheduler()
    scheduler.add_job(pipeline_scraping, "interval", hours=4)
    try:
        logger.info("Planificador iniciado. Próxima ejecución en 4 horas.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.error("Worker: Detenido.")