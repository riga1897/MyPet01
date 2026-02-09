# Чек-лист деплоя MyPet01

Пошаговая инструкция для подготовки VPS и GitHub к первому деплою.

## Этап 1: Подготовка VPS

### Автоматическая настройка (рекомендуется)

```bash
# Подключиться к VPS как root
ssh root@<IP_ВАШЕГО_VPS>

# Скопировать и запустить скрипт
scp scripts/setup_vps.sh root@<IP>:/tmp/
ssh root@<IP> "bash /tmp/setup_vps.sh"
```

Скрипт автоматически:
- Создаст пользователя `depuser` с ограниченными правами sudo
- Сгенерирует SSH ключ для GitHub Actions

> **Примечание**: Docker, UFW, fail2ban и директория деплоя будут установлены/созданы автоматически при первом деплое через GitHub Actions (CI/CD).

### Ручная настройка

Подробная инструкция по ручному созданию пользователя: **[DEPUSER_SETUP.md](./DEPUSER_SETUP.md)**

Краткий чек-лист:

- [ ] Создать пользователя: `adduser --disabled-password --gecos "" depuser`
- [ ] Настроить ограниченный sudo (см. [DEPUSER_SETUP.md](./DEPUSER_SETUP.md#шаг-2-настройка-ограниченных-прав-sudo))
- [ ] Сгенерировать SSH ключ: `ssh-keygen -t ed25519 -C "github-actions-deploy" -f /home/depuser/.ssh/github_deploy -N ""`
- [ ] Добавить публичный ключ в `~/.ssh/authorized_keys`
- [ ] Docker, UFW, fail2ban, директория деплоя — установятся автоматически при первом деплое (CI/CD)

### Требования к VPS

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| ОС | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 |
| RAM | 1 GB | 2 GB |
| Диск | 10 GB | 20 GB |
| CPU | 1 vCPU | 2 vCPU |

---

## Этап 2: GitHub Personal Access Token

- [ ] Перейти: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- [ ] Нажать **Generate new token (classic)**
- [ ] Название: `MyPet01 GHCR`
- [ ] Срок: выбрать подходящий (90 дней или без срока)
- [ ] Отметить scope: `read:packages`
- [ ] Нажать **Generate token**
- [ ] **Скопировать токен** (он покажется только один раз!)

---

## Этап 3: GitHub Secrets

Перейти: GitHub → Repository → Settings → Secrets and variables → Actions → **New repository secret**

### Общие

| # | Secret | Значение | Статус |
|---|--------|----------|--------|
| 1 | `GHCR_TOKEN` | Personal Access Token из Этапа 2 | ☐ |

### Pre-Production (preprod)

| # | Secret | Значение | Статус |
|---|--------|----------|--------|
| 2 | `PREPROD_SSH_KEY` | Приватный SSH ключ (из скрипта настройки VPS) | ☐ |
| 3 | `PREPROD_SSH_USER` | `depuser` | ☐ |
| 4 | `PREPROD_SERVER_IP` | IP адрес VPS | ☐ |
| 5 | `PREPROD_DEPLOY_DIR` | `/opt/blog-preprod` | ☐ |

### Production (когда будете готовы)

| # | Secret | Значение | Статус |
|---|--------|----------|--------|
| 6 | `SSH_KEY` | Приватный SSH ключ для prod VPS | ☐ |
| 7 | `SSH_USER` | `depuser` | ☐ |
| 8 | `SERVER_IP` | IP адрес production VPS | ☐ |
| 9 | `DEPLOY_DIR` | `/opt/blog` | ☐ |

---

## Этап 4: Проверка перед деплоем

- [ ] Все тесты проходят: `poetry run pytest`
- [ ] Линтеры чистые: `poetry run ruff check .` и `poetry run mypy .`
- [ ] Docker образ собирается локально: `docker-compose build`
- [ ] GitHub Secrets заполнены (минимум: GHCR_TOKEN + PREPROD_*)
- [ ] VPS доступен по SSH: `ssh depuser@<IP>`

---

## Этап 5: Запуск предеплоя

```bash
# Убедиться, что develop содержит последние изменения
git checkout develop
git pull origin develop

# Создать release ветку
git checkout -b release/v1.0 develop
git push origin release/v1.0
```

CI/CD автоматически:
1. Прогонит тесты (pytest + coverage 100%)
2. Проверит линтеры (ruff + mypy)
3. Соберёт Docker образ → GitHub Container Registry
4. Подключится к VPS по SSH
5. Сгенерирует `.env` (если не существует)
6. Запустит контейнеры (web, db, redis, nginx, haproxy)
7. Применит миграции, создаст суперпользователя, загрузит данные
8. Проверит health check
9. Создаст draft PR в main

---

## Этап 6: Настройка SSL (Let's Encrypt)

После успешного деплоя настройте HTTPS сертификаты:

```bash
ssh depuser@<IP>
cd /opt/blog-preprod

# Первый запуск — тестовый сертификат (проверить что всё работает)
STAGING=1 bash init-letsencrypt.sh

# Если тест прошёл — получить настоящий сертификат
# Сначала удалить тестовый
docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
    rm -rf /etc/letsencrypt/live /etc/letsencrypt/archive /etc/letsencrypt/renewal

# Получить настоящий сертификат
STAGING=0 bash init-letsencrypt.sh
```

Скрипт `init-letsencrypt.sh` автоматически:
1. Скачивает рекомендуемые TLS параметры
2. Создаёт временный самоподписанный сертификат
3. Запускает nginx с временным сертификатом
4. Запрашивает настоящий сертификат у Let's Encrypt
5. Перезагружает nginx с новым сертификатом
6. Запускает контейнер certbot для автообновления
7. Добавляет cron задачу для перезагрузки nginx

**Требования:**
- Домен (`www.mine-craft.su`, `site.mine-craft.su`) должен указывать на IP сервера (DNS A-записи)
- Порт 80 должен быть открыт (для ACME-challenge через HAProxy)

**Автообновление:**
- Certbot проверяет необходимость обновления каждые 12 часов
- Фактическое обновление — раз в ~60 дней (за 30 дней до истечения)
- Nginx перезагружается раз в неделю (cron) для подхвата новых сертификатов

---

## Этап 7: Проверка после деплоя

- [ ] Сайт открывается: `https://<DOMAIN>`
- [ ] HTTP редиректит на HTTPS
- [ ] Админка доступна: `https://<DOMAIN>/admin/`
- [ ] Логин работает
- [ ] Контент отображается
- [ ] Статика загружается (CSS, JS, изображения)
- [ ] SSL сертификат валидный (замочек в браузере)

### Полезные команды на VPS

```bash
# Подключиться к VPS
ssh depuser@<IP>
cd /opt/blog-preprod

# Логи контейнеров
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx

# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Рестарт
docker compose -f docker-compose.prod.yml restart web

# Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Сбросить кэш
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('OK')"
```

---

## Этап 8: Релиз в production

Когда предеплой проверен и всё работает:

```bash
# Мержим release в main
git checkout main
git merge release/v1.0
git push origin main
```

CI/CD автоматически задеплоит на production VPS.

---

## Откат при проблемах

```bash
ssh depuser@<IP>
cd /opt/blog-preprod

# Посмотреть логи
docker compose -f docker-compose.prod.yml logs --tail=100 web

# Откатить к предыдущему образу
docker compose -f docker-compose.prod.yml down
# Поменять IMAGE_TAG в .env на предыдущий тег
nano .env
docker compose -f docker-compose.prod.yml up -d

# Пересоздать .env с нуля
rm .env
SERVER_IP=<IP> ./generate-preprod-env.sh
docker compose -f docker-compose.prod.yml restart
```

---

## Схема Gitflow

```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
```

Подробнее: [CI_CD.md](./CI_CD.md) | [GITHUB_SECRETS.md](./GITHUB_SECRETS.md)
