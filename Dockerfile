# Utiliser une image Python légère et optimisée
FROM python:3.11-slim-bookworm

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement pour optimiser Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Skipping apt-get install to avoid network timeouts (using pre-built wheels and python healthcheck)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# Copier uniquement requirements.txt pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Copier le script d'entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Créer le répertoire des logs
RUN mkdir -p logs

# Exposer le port 8000
EXPOSE 8000

# Définir l'entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Commande de démarrage par défaut (Gunicorn + Uvicorn workers)
CMD ["gunicorn", "core.asgi:application", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
