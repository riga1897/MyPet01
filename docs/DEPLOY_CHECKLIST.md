# Чек-лист деплоя MyPet01

Пошаговая инструкция для подготовки VPS и GitHub к первому деплою.

## Этап 1: Подготовка VPS + GitHub Secrets

### Полностью автоматическая настройка (рекомендуется)

Один скрипт делает всё: настраивает VPS и устанавливает GitHub Secrets.

**Требования:**
- Git Bash (Windows) или bash (Linux/Mac)
- GitHub CLI (`gh`) — [установка и авторизация](./GITHUB_SECRETS.md#автоматическая-настройка-рекомендуется)

```bash
# В Git Bash из директории проекта:

# Препрод
./scripts/setup-github.sh preprod 217.147.15.220

# Прод
./scripts/setup-github.sh prod 91.204.75.25
```

Скрипт автоматически:
- Подключится к VPS как root (запросит пароль)
- Создаст пользователей `depuser` (деплой) и `useradmin` (администратор)
- Сгенерирует SSH ключи для GitHub Actions и администратора
- Сменит пароль root на новый случайный
- Отключит root SSH
- Установит GitHub Secrets (`SSH_KEY`/`PREPROD_SSH_KEY`, `SERVER_IP`, и др.)
- Для препрода — установит Variables (`CERTBOT_STAGING`, `LOAD_DEMO_DATA`, `CREATE_PR_ON_PREDEPLOY`)
- Выведет пароль root и ключ администратора — **сохраните их!**

> **Примечание**: Docker, UFW, fail2ban и директория деплоя будут установлены/созданы автоматически при первом деплое через GitHub Actions (CI/CD).

### Только настройка VPS (без GitHub)

Если нужно только настроить VPS без автоматической установки GitHub Secrets:

```bash
# На VPS от root:
./setup_vps.sh preprod   # или prod
```

Затем вручную скопируйте SSH ключ деплоя в GitHub Secret (см. [GITHUB_SECRETS.md](./GITHUB_SECRETS.md#ручная-настройка)).

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

### Repository Variables (опциональные)

Вкладка **Variables** (не Secrets):

| # | Variable | Значение | Описание | Статус |
|---|----------|----------|----------|--------|
| 1 | `LOAD_DEMO_DATA` | `true` | Загрузка демо-данных на препроде | ☐ |
| 2 | `CERTBOT_STAGING` | `1` | Тестовый SSL на препроде (только препрод) | ☐ |
| 3 | `CREATE_PR_ON_PREDEPLOY` | `false` | Автосоздание draft PR | ☐ |

> **Важно:** `CERTBOT_STAGING` влияет только на препрод. В production всегда используется реальный сертификат.

---

## Этап 4: Проверка перед деплоем

- [ ] Все тесты проходят: `poetry run pytest`
- [ ] Линтеры чистые: `poetry run ruff check .` и `poetry run mypy .`
- [ ] Docker образ собирается локально: `docker compose build`
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
5. Настроит инфраструктуру VPS (Docker, UFW, fail2ban — при первом деплое)
6. Сгенерирует `.env` (если не существует)
7. Запустит контейнеры (web, db, redis, nginx, haproxy)
8. Проверит health check
9. **Настроит SSL** (автоматически, staging или production — зависит от `CERTBOT_STAGING`)
10. Применит миграции, создаст суперпользователя, загрузит данные
11. **Загрузит демо-контент** (если `LOAD_DEMO_DATA=true`)
12. Создаст draft PR в main

---

## Этап 6: SSL сертификаты

### Автоматическая настройка (CI/CD)

SSL сертификаты настраиваются автоматически при деплое:
- **Препрод:** Зависит от `CERTBOT_STAGING` (`1` = тестовый, `0` = реальный)
- **Production:** Всегда реальный сертификат (захардкожен `STAGING=0`)

При первом деплое:
1. Nginx стартует с самоподписанным (dummy) сертификатом
2. CI/CD обнаруживает отсутствие реального сертификата
3. Запускает `init-letsencrypt.sh` для получения сертификата от Let's Encrypt
4. Certbot автоматически обновляет сертификат каждые 12 часов (если нужно)

### Ручная настройка (если нужно)

```bash
ssh depuser@<IP>
cd /opt/blog-preprod

# Получить тестовый сертификат
STAGING=1 bash init-letsencrypt.sh

# Удалить тестовый и получить реальный
docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
    rm -rf /etc/letsencrypt/live /etc/letsencrypt/archive /etc/letsencrypt/renewal

STAGING=0 bash init-letsencrypt.sh
```

**Требования:**
- Домены должны указывать на IP серверов (DNS A-записи):
  - **Прод**: `www.mine-craft.su` → прод VPS, `mainsrv01.mine-craft.su` → прод VPS
  - **Препрод**: `site.mine-craft.su` → препрод VPS, `vpn.mine-craft.su` → препрод VPS
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
- [ ] Контент отображается (демо-данные загружены)
- [ ] Медиафайлы доступны для авторизованных пользователей
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

# Загрузить демо-данные вручную
docker compose -f docker-compose.prod.yml exec -T web python manage.py setup_demo_content
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

CI/CD автоматически задеплоит на production VPS с **реальным SSL сертификатом**.

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

## Настройка VPN (SoftEther)

VPN-сервер SoftEther стартует вместе с остальными контейнерами, но требует ручной настройки после первого деплоя:

1. Настроить через `vpncmd` или SoftEther Admin GUI
2. Или скопировать готовый конфиг с другого сервера:

```bash
docker cp vpn_server.config $(docker ps -q -f name=softether):/usr/vpnserver/vpn_server.config
docker restart $(docker ps -q -f name=softether)
```

> **Важно:** Конфиг VPN содержит пароли и ключи. Не храните его в Git-репозитории.

---

## Схема Gitflow

```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
```

Подробнее: [CI_CD.md](./CI_CD.md) | [GITHUB_SECRETS.md](./GITHUB_SECRETS.md)
