import logging
import sys


def config_logger(nombre):
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    # Evita duplicados
    if not logger.handlers:
        # StreamHandler envía los logs a la consola
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # FileHandler crea una archivo de texto en el PC
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Fecha, Nivel, Módulo y Mensaje
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.addHandler(file_handler)
    return logger