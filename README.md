# SyncflowAI Backend

This is the Django backend for SyncflowAI Phase 1 MVP. It includes core infrastructure for user authentication, workspace/brand management, social platform integrations, and an AI content generation pipeline.

## Features (Phase 1)
- Authentication (JWT)
- Workspace & Brand Management
- Social Accounts (OAuth interfaces)
- AI Content Studio (Powered by LiteLLM)
- Background Jobs (Celery, Redis) for Publishing
- PostgreSQL Database

## Prerequisites
- Docker & Docker Compose
- Python 3.13+ (if running locally without Docker)

## Getting Started

### 1. Environment Setup
Create a `.env` file based on the example:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
To boot up the entire stack (Django, PostgreSQL, Redis, Celery, Celery Beat, and Flower):
```bash
docker-compose up --build
```

### 3. Database Migrations
Once the containers are running, run database migrations in a new terminal:
```bash
docker-compose exec web python manage.py migrate
```

### 4. Create a Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application
- **API (Swagger Docs)**: http://localhost:8000/api/schema/swagger-ui/
- **Django Admin**: http://localhost:8000/admin/
- **Flower (Celery Monitor)**: http://localhost:5555/

## Useful Management Commands
- **Make migrations**: `docker-compose exec web python manage.py makemigrations`
- **Run tests**: `docker-compose exec web python manage.py test`
- **Restart Celery**: `docker-compose restart celery`
- **Format code** (if configured): `docker-compose exec web black .`
