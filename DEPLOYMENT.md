# Развёртывание MyPet01 — Гармония Души

## Обзор

Проект развёртывается в несколько этапов:

1. **Локальная разработка (Windows + Docker)** — DEBUG=1, тесты, линтеры
2. **GitHub CI/CD** — автоматическое тестирование при push
3. **Pre-Production** — тестовое окружение с DEBUG=0
4. **Production (Ubuntu 24.04)** — финальное развёртывание

---

## Этап 1: Локальная разработка (Windows + Docker)

### Требования

- Docker Desktop для Windows
- Git

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/MyPet01.git
cd MyPet01

# 2. Запустить в режиме разработки
docker compose -f docker-compose.dev.yml up --build

# 3. Открыть в браузере
# http://localhost:8000
```

### Применение миграций

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### Создание суперпользователя

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Запуск тестов

```bash
docker compose -f docker-compose.dev.yml exec web poetry run pytest
```

### Запуск линтеров

```bash
docker compose -f docker-compose.dev.yml exec web poetry run ruff check .
docker compose -f docker-compose.dev.yml exec web poetry run mypy .
```

### Остановка

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Этап 2: GitHub Actions CI/CD

### Структура пайплайна

```
.github/workflows/ci-cd.yml

Jobs:
├── test          # Pytest + Coverage
├── lint          # Ruff + Mypy
├── build         # Docker image → GHCR
├── deploy-preprod # На preprod сервер (release/* ветки)
└── deploy-prod   # На production (main ветка)
```

### Настройка GitHub Secrets

В Settings → Secrets and variables → Actions добавьте:

| Secret | Описание |
|--------|----------|
| `SECRET_KEY` | Django SECRET_KEY |
| `PREPROD_SSH_KEY` | SSH ключ для preprod сервера |
| `PREPROD_SERVER_IP` | IP preprod сервера |
| `PREPROD_SSH_USER` | SSH пользователь |
| `PREPROD_DEPLOY_DIR` | Директория на сервере |
| `PROD_SSH_KEY` | SSH ключ для prod сервера |
| `PROD_SERVER_IP` | IP prod сервера |
| `PROD_SSH_USER` | SSH пользователь |
| `PROD_DEPLOY_DIR` | Директория на prod сервере |

### Git Flow

```
feature/* → develop → release/* → main
           ↓           ↓          ↓
         tests       preprod   production
```

---

## Этап 3: Pre-Production

### Первоначальная настройка сервера

```bash
# SSH на сервер
ssh user@preprod-server

# Установить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Создать директорию проекта
mkdir -p /opt/mypet01
cd /opt/mypet01
```

### Развёртывание

```bash
# Скопировать файлы
scp docker-compose.prod.yml user@server:/opt/mypet01/
scp -r nginx user@server:/opt/mypet01/
scp .env.docker.example user@server:/opt/mypet01/.env

# На сервере — отредактировать .env
nano /opt/mypet01/.env

# Запустить
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Этап 4: Production (Ubuntu 24.04)

### Требования

- Ubuntu 24.04 LTS
- Docker + Docker Compose
- Домен + SSL-сертификат (Let's Encrypt)

### Установка

```bash
# 1. Обновить систему
sudo apt update && sudo apt upgrade -y

# 2. Установить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Клонировать проект
cd /opt
git clone https://github.com/your-username/MyPet01.git mypet01
cd mypet01

# 4. Настроить окружение
cp .env.docker.example .env
nano .env  # Заполнить реальные значения

# 5. Запустить
docker compose -f docker-compose.prod.yml up -d --build
```

### SSL с Caddy (рекомендуется)

Вместо nginx можно использовать Caddy для автоматического SSL:

```bash
# Установить Caddy
sudo apt install -y caddy

# /etc/caddy/Caddyfile
yourdomain.com {
    reverse_proxy localhost:80
}

sudo systemctl enable caddy
sudo systemctl start caddy
```

### SSL с Certbot + Nginx

```bash
# Установить certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Полезные команды

### Просмотр логов

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Перезапуск после изменений

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### Резервное копирование БД

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U mypet_user mypet_db > backup_$(date +%Y%m%d).sql
```

### Восстановление БД

```bash
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U mypet_user mypet_db
```

---

## Структура файлов

```
MyPet01/
├── docker-compose.dev.yml      # Разработка (DEBUG=1)
├── docker-compose.prod.yml     # Production
├── docker-compose.yaml         # Legacy (не использовать)
├── Dockerfile                  # Образ приложения
├── docker-entrypoint.sh        # Скрипт запуска
├── nginx/
│   └── nginx.conf              # Конфигурация nginx
├── .env.example                # Пример для Replit
├── .env.docker.example         # Пример для Docker
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # GitHub Actions
└── DEPLOYMENT.md               # Этот файл
```

---

## Чек-лист перед production

- [ ] SECRET_KEY — уникальный, надёжный
- [ ] DEBUG=0
- [ ] ALLOWED_HOSTS — только ваш домен
- [ ] CSRF_TRUSTED_ORIGINS — с https://
- [ ] PostgreSQL пароль — надёжный
- [ ] SSL-сертификат установлен
- [ ] Резервное копирование настроено
- [ ] Мониторинг (опционально: Sentry, Prometheus)
