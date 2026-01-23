#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files (optional, but good for production)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Start the server
echo "Starting server..."
exec "$@"
