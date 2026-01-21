# MyPet01

## Overview
A personal pet website now being developed with Python.

## User Preferences
- **Package Management**: Use `poetry` for installing and managing modules.
- **Linting & Formatting**: Use `ruff` for code quality.
- **Type Checking**: Use `mypy` (installed in the `dev` group).
- **Testing**: Use `pytest` (installed in the `test` group).

## Project Structure
- `manage.py` - Django project management script
- `mypet_project/` - Django project configuration
- `main.py` - Legacy entry point
- `replit.nix` - Nix environment configuration

## Running the Application
### Django
```bash
python manage.py runserver 0.0.0.0:5000
```

## Tech Stack
- Python 3.12
- Django 5.x
- Poetry (for dependency management)
- Ruff, Mypy, Pytest (dev tools)

## Recent Changes
- 2026-01-20: Project prepared for Python development.
- 2026-01-20: Installed Django 5.x and initialized project structure.
- 2026-01-20: Configured "Run Django App" workflow on port 5000.
- 2026-01-20: Installed Django and initialized project.
