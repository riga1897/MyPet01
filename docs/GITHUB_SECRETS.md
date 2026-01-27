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

## Production Secrets

### SSH доступ

| Secret | Описание | Пример |
|--------|----------|--------|
| `SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `SSH_USER` | Имя пользователя SSH | `root` или `ubuntu` |
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
| `PREPROD_SSH_USER` | Пользователь SSH | `ubuntu` |
| `PREPROD_SERVER_IP` | IP препрод сервера | `192.168.1.100` |
| `PREPROD_DEPLOY_DIR` | Путь деплоя | `/opt/blog-preprod` |

## Автогенерируемые значения

Эти значения генерируются автоматически скриптом на VPS:
- `SECRET_KEY` — Django secret (50 chars)
- `POSTGRES_PASSWORD` — Пароль БД (24 chars)

## Чек-лист

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

## Идемпотентность

Скрипт `generate-production-env.sh`:
- Если `.env` существует → **НЕ перезаписывает**
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
