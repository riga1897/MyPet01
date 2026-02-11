# GitHub Secrets Configuration Guide

Настройка GitHub Secrets для автоматического деплоя MyPet01.

## Обзор

GitHub Secrets используются для безопасного хранения конфиденциальных данных и передачи их в CI/CD pipeline.

**Преимущества:**
- Безопасность — секреты зашифрованы в GitHub
- Автоматизация — деплой без ручной настройки .env на VPS
- Удобство — один `git push main` → полный деплой

## Как добавить секреты

1. Откройте репозиторий на GitHub
2. Перейдите: **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Введите **Name** и **Value**
5. Нажмите **Add secret**

## Общие Secrets

| Secret | Описание | Как получить |
|--------|----------|--------------|
| `GHCR_TOKEN` | Personal Access Token для GitHub Container Registry | GitHub → Settings → Developer settings → Personal access tokens → Classic → Generate (scope: `read:packages`) |

## Production Secrets

### SSH доступ

| Secret | Описание | Пример |
|--------|----------|--------|
| `SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `SSH_USER` | Имя пользователя SSH | `depuser` |
| `SERVER_IP` | IP адрес production VPS | `123.45.67.89` |
| `DEPLOY_DIR` | Путь для деплоя | `/opt/blog` |

### Генерация SSH ключа

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

cat ~/.ssh/github_deploy
```

## Pre-Production Secrets

| Secret | Описание | Пример |
|--------|----------|--------|
| `PREPROD_SSH_KEY` | SSH ключ для препрода | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `PREPROD_SSH_USER` | Пользователь SSH | `depuser` |
| `PREPROD_SERVER_IP` | IP препрод сервера | `192.168.1.100` |
| `PREPROD_DEPLOY_DIR` | Путь деплоя | `/opt/blog-preprod` |

## Автогенерируемые значения

Эти значения генерируются автоматически скриптом на VPS:
- `SECRET_KEY` — Django secret (50 chars)
- `POSTGRES_PASSWORD` — Пароль БД (24 chars)

## Repository Variables

Переменные настраиваются в: **Settings** → **Secrets and variables** → **Actions** → вкладка **Variables**

| Variable | Описание | Значения | По умолчанию | Область действия |
|----------|----------|----------|--------------|------------------|
| `LOAD_DEMO_DATA` | Загрузка демо-данных при деплое | `true` / `false` | `false` | Только препрод |
| `CERTBOT_STAGING` | Использовать staging Let's Encrypt (тестовые сертификаты) | `0` / `1` | `0` | Только препрод |
| `CREATE_PR_ON_PREDEPLOY` | Создавать draft PR в main при деплое на препрод | `true` / `false` | `true` | Только препрод |

> **Важно:** `CERTBOT_STAGING` и `LOAD_DEMO_DATA` влияют **только на препрод**. В production:
> - SSL сертификат **всегда реальный** (`STAGING=0` захардкожен в `ci.yml`)
> - Демо-данные **не загружаются**

## Чек-лист

### Общие
- [ ] `GHCR_TOKEN` — Personal Access Token с правами `read:packages`

### Production
- [ ] `SSH_KEY`
- [ ] `SSH_USER`
- [ ] `SERVER_IP`
- [ ] `DEPLOY_DIR`

### Pre-Production
- [ ] `PREPROD_SSH_KEY`
- [ ] `PREPROD_SSH_USER`
- [ ] `PREPROD_SERVER_IP`
- [ ] `PREPROD_DEPLOY_DIR`

### Variables (опциональные)
- [ ] `LOAD_DEMO_DATA` — `true` для препрода
- [ ] `CERTBOT_STAGING` — `1` для тестовых сертификатов на препроде
- [ ] `CREATE_PR_ON_PREDEPLOY` — `false` если не нужны автоматические PR

## Идемпотентность

Скрипты `generate-production-env.sh` и `generate-preprod-env.sh`:
- Если `.env` существует → **НЕ перезаписывают**
- Секреты сохраняются между деплоями
- Для пересоздания: удалите `.env` вручную

```bash
ssh user@vps "rm /opt/blog/.env"
git push origin main
```

## Troubleshooting

### Permission denied (publickey)
1. Проверьте публичный ключ на VPS: `cat ~/.ssh/authorized_keys`
2. Проверьте приватный ключ в GitHub Secrets

### .env не изменился после деплоя
Скрипт пропускает генерацию если `.env` уже существует.
Удалите `.env` на VPS и запустите деплой снова.

### Демо-данные не загрузились
1. Проверьте что `LOAD_DEMO_DATA=true` в GitHub Variables
2. Проверьте `.env` на VPS: `grep LOAD_DEMO_DATA .env`
3. Можно загрузить вручную: `docker compose -f docker-compose.prod.yml exec -T web python manage.py setup_demo_content`
