# Essivi Backend - Docker Infrastructure

## Quick Start

```bash
# Navigate to Docker infrastructure folder
cd infrastructure/docker

# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
```

## Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Traefik** | essivi-traefik | 80/443/8080 | Reverse proxy & load balancer |
| **PostgreSQL** | essivi-postgres | 5432 | Primary database |
| **Redis** | essivi-redis | 6379 | Cache & WebSocket channels |
| **MongoDB** | essivi-mongo | 27017 | Analytics database |
| **Backend** | essivi-backend | 8000 | Django ASGI application |

## Access Points

- **API**: http://api.localhost or http://localhost
- **Traefik Dashboard**: http://traefik.localhost:8080
- **API Documentation**: http://api.localhost/api/schema/

## Configuration

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

## Commands

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f [service_name]

# Execute Django commands
docker compose exec backend python manage.py [command]

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Database migrations
docker compose exec backend python manage.py migrate
```

## Production Considerations

1. **Change SECRET_KEY** in `.env`
2. Set **DEBUG=False**
3. Configure **HTTPS** via Traefik with Let's Encrypt
4. Use **secrets management** for sensitive data
5. Set proper **ALLOWED_HOSTS**
