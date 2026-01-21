# MyPet01

## Overview
A personal pet website for the family. This is a Django 5.2 project using a modern backend stack.

## Tech Stack
- **Python**: 3.12
- **Framework**: Django 5.2.7
- **API**: Django REST Framework 3.16.1
- **Database**: PostgreSQL (psycopg2-binary)
- **Task Queue**: Celery (planned)
- **Cache/Broker**: Redis
- **Containerization**: Docker & Docker Compose (prepared)
- **Dependency Management**: Poetry 2.0+

## Project Architecture
The project is designed to be container-compatible. In Replit, it runs as a single "container" with integrated services.

## Current Setup Progress
- [x] Environment configured with Python 3.12
- [x] Dependencies defined in `pyproject.toml`
- [x] Docker configuration files prepared (`Dockerfile`, `docker-compose.yaml`)
- [x] Basic Django structure initialized

## How to Run (Replit)
Click the "Run" button to start the Django development server.

## Future Deployment (Ubuntu 24.04)
1. Install Docker and Docker Compose on Ubuntu.
2. Clone the repository.
3. Run `docker-compose up --build`.

## Recent Changes
- 2026-01-21: Upgraded environment to Python 3.12 and defined the full production stack.
