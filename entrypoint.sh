#!/bin/sh

# Verify postgres is up
# (You might want to add a wait-for-it script here in a robust setup, 
# but for now we rely on docker-compose depends_on healthcheck)

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
