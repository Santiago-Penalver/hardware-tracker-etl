#!/bin/bash

echo "🚀 Levantando HardwareTracker con Docker..."
docker compose up --build -d

echo "⏳ Esperando a que los servicios se estabilicen..."
sleep 3 # Damos unos segundos para asegurar que la base de datos y migraciones estén listas

echo "🧪 Ejecutando suite de pruebas con Pytest..."
docker compose run --rm web pytest -v

if [ $? -eq 0 ]; then
    echo ""
    echo "✨ ¡Todo en orden! Los tests pasaron exitosamente."
    echo "👉 Podes acceder a la app en: http://localhost:5000"
else
    echo ""
    echo "❌ ¡Atención! Hubo fallas en los tests. Revisá los logs de arriba."
    exit 1
fi