# ⚡ Hardware Tracker - Scraper & ETL Multi-Tienda

Sistema ETL automatizado y panel de monitoreo en tiempo real diseñado para extraer, limpiar, normalizar y almacenar datos de stock y precios de hardware desde múltiples tiendas de e-commerce. El proyecto está construido bajo una arquitectura modular, orientada a configuraciones (configuration-driven) y empaquetada en microservicios mediante Docker.

## 🛠️ Tecnologías y Stack Tecnológico

* **Backend & Orquestación:** Python 3.14, Flask, Chart.js, APScheduler (ejecución periódica desatendida cada 4 horas).
* **Web Scraping & Procesamiento:** BeautifulSoup4, Requests, `ThreadPoolExecutor` (concurrencia por hilos), Tenacity, lxml, Fake-UserAgent.
* **Base de Datos & ORM:** PostgreSQL, SQLAlchemy Core/ORM, Alembic (gestión y versión de migraciones del esquema).
* **Testing & Calidad:** `pytest` (pruebas unitarias y de integración para parsers, base de datos y flujo del worker).
* **Infraestructura & DevOps:** Docker, Docker Compose (servicios aislados para Web App, Base de Datos PostgreSQL y Worker desatendido), Bash Scripting (`start.sh`).
* **Frontend & Interactividad:** HTML5, Tailwind CSS, HTMX (filtrado asíncrono dinámico sin recargar la página), Font Awesome.

## 🚀 Arquitectura y Características Principales

* **Motor por Configuración (`MultiT_config.py`):** Arquitectura agnóstica que separa la lógica de extracción de las reglas de negocio. Permite integrar nuevos scrapers o cambiar de rubro con modificaciones mínimas.
* **Resiliencia en Paginación (`downloader.py`):** Detección defensiva de bucles y fallbacks en e-commerce mediante firmas de enlaces (`links_firma`), evitando redirecciones infinitas en la recolección de productos, además de contar con reintentos automáticos exponenciales (`tenacity`), incluyendo un fallback de reutilizamiento de caching local si la página no responde o nos bloquea momentáneamente.
* **Normalización & Reglas Defensivas (`utils.py` / `parser.py`):** Limpieza multi-formato de precios, exclusión estricta de productos no deseados (servicios, cables) y categorización de marcas por capas.
* **Persistencia Eficiente & Upsert Nativo (`database.py`):** Implementación de inserciones masivas de alto rendimiento utilizando el **Upsert Nativo de PostgreSQL** (`pg_insert` con `on_conflict_do_update`) para la tabla de precios vigentes, evitando duplicados y garantizando la integridad mediante índices únicos (`tienda`, `sku_tienda`). A su vez, gestiona registros históricos de precios mediante `bulk_save_objects` para trazabilidad temporal.
* **Worker Desacoplado:** Proceso en segundo plano gestionado por `BlockingScheduler` que ejecuta el pipeline de extracción y carga sin impactar en la fluidez de la app web.
* **Pruebas Automáticas (`pytest`):** Suite completa de pruebas unitarias verificando funciones de limpieza, resiliencia de parsers y transacciones de base de datos.

## 🖥️ Interfaz Web & Panel de Monitoreo (Flask + HTMX)

La aplicación web está construida como un monolito modular en **Flask**, diseñada con un enfoque moderno y ligero:

* **Frontend Dinámico con HTMX:** En lugar de utilizar frameworks pesados de JavaScript (como React o Angular), se implementó renderizado del lado del servidor (SSR) complementado con **HTMX**. Esto permite interacciones fluidas, filtrados asíncronos de productos y carga de paneles de detalle sin recargar la página.
* **Gráficos Históricos (Chart.js):** Cada producto cuenta con un panel de detalle interactivo que renderiza gráficos de evolución temporal de precios mediante **Chart.js**, consumiendo un endpoint JSON dedicado (`/producto/<id>/historial`).
* **Buscador y Filtros Avanzados:** Endpoints optimizados para filtrado cruzado por marca y categoría, con paginación en SQL y conteos dinámicos en tiempo real en la vista principal.

## 🧪 Pruebas Automáticas (Testing)

Para ejecutar la suite de pruebas unitarias e integración en tu entorno local:

```bash
pytest -v
```

## ⚙️ Cómo Ejecutar el Proyecto (con Docker)

La forma recomendada de ejecutar el sistema completo (Base de Datos + App Web + Worker) es mediante el script de arranque automatizado:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Santiago-Penalver/hardware-tracker-etl.git
   cd hardware-tracker-etl
   ```

2. **Configurar las variables de entorno (`.env`):**
   Creá un archivo `.env` en la raíz del proyecto basándote en las variables de conexión:
    ```env
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    DB_HOST=db # o 'localhost' si estás usando el Entorno de Desarrollo
    DB_PORT=5432
    DB_NAME=hardware_tracker
    DATABASE_URI=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

3. **Ejecutar el script de inicio (`run.sh`):**
   Concedé permisos de ejecución y lanzá el script para construir y levantar toda la infraestructura en segundo plano:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

4. **Acceder al dashboard web:**
   * **http://localhost:5000**

---

## 💻 Ejecución Manual (Entorno de Desarrollo)

Si preferís correrlo directamente en tu entorno local de Python sin Docker:

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar la app Flask:**
   ```bash
   python app.py
   ```

3. **Iniciar el Worker de scraping:**
   ```bash
   python config/worker.py
   ```

---

## 👨‍💻 Autor

* **Santiago Peñalver** - 2026