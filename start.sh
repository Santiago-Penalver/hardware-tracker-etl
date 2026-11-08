#!/bin/sh

echo "Ejecutando migraciones de Alembic..."
alembic upgrade head

echo "Arrancando el servicio con: $@"
exec "$@"