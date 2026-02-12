# Деплой MyPet01 на VPS

Три варианта деплоя:
- **CI/CD (рекомендуется)** — автоматический деплой через GitHub Actions
- **Docker (ручной)** — быстрый и простой
- **Ручная установка** — для тонкой настройки

> **Подготовка VPS и секретов:** [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)
> **Стратегия и CI/CD архитектура:** [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md)

---

# Вариант 0: CI/CD (рекомендуется)

Автоматический деплой при `git push` через GitHub Actions.

## Настройка (один раз)

1. Подготовьте VPS и GitHub Secrets — [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)
2. Убедитесь, что все секреты заполнены — [чек-лист](VPS_AND_SECRETS.md#чек-лист)
3. Изучите Gitflow и pipeline — [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md)

## Деплой на pre-production

```bash
git checkout -b release/v1.0 develop
git push origin release/v1.0
```

CI/CD автоматически прогонит тесты, соберёт образ, задеплоит на препрод и создаст draft PR.
Подробности pipeline: [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md#pre-production-pipeline-release)

## Деплой на production

```bash
git checkout main
git merge release/v1.0
git push origin main
```

CI/CD задеплоит на production VPS с реальным SSL сертификатом.
Подробности: [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md#production-pipeline-main)

---

# Вариант 1: Docker (ручной)

## Требования

- Ubuntu 22.04+ / Debian 11+
- Docker 24+
- Docker Compose v2+

## 1. Установка Docker

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

## 2. Клонирование проекта

```bash
mkdir -p /opt/blog && cd /opt/blog
git clone https://github.com/riga1897/MyPet01.git .
```

## 3. Настройка переменных окружения

```bash
cp deploy/.env.production.example .env
nano .env

# Обязательно установить:
# - SECRET_KEY (сгенерировать: openssl rand -hex 32)
# - POSTGRES_PASSWORD
# - ALLOWED_HOSTS
```

## 4. SSL сертификаты

```bash
mkdir -p nginx/ssl nginx/certbot

# Вариант A: Let's Encrypt (бесплатно)
sudo apt install certbot
sudo certbot certonly --standalone \
    -d www.mine-craft.su \
    -d site.mine-craft.su \
    -d vpn.mine-craft.su

sudo cp /etc/letsencrypt/live/mine-craft.su/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/mine-craft.su/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem

# Вариант B: Самоподписанный (для тестирования)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/CN=mine-craft.su"
```

### Настройка сертификата в SoftEther VPN

После первого запуска контейнеров:

```bash
docker compose -f docker-compose.prod.yml exec softether vpncmd localhost /server
ServerCertSet /LOADCERT:/etc/ssl/vpn/fullchain.pem /LOADKEY:/etc/ssl/vpn/privkey.pem
ServerCertGet
```

### Автообновление сертификатов

```bash
chmod +x deploy/renew-certs.sh

sudo crontab -e
# Добавить строку:
0 3,15 * * * /opt/blog/deploy/renew-certs.sh >> /var/log/certbot-renew.log 2>&1
```

Скрипт автоматически:
1. Проверяет и обновляет сертификаты через certbot
2. Копирует новые сертификаты в `nginx/ssl/`
3. Перезапускает Nginx и SoftEther для применения

## 5. Запуск

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml ps
```

## 6. Обновление

```bash
cd /opt/blog
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 7. Полезные команды Docker

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx

# Перезапуск
docker compose -f docker-compose.prod.yml restart

# Остановка
docker compose -f docker-compose.prod.yml down

# Очистка (с удалением данных!)
docker compose -f docker-compose.prod.yml down -v
```

---

# VPN и сетевая архитектура

## Архитектура SNI-роутинга

HAProxy работает в режиме `network_mode: host` для SNI-маршрутизации:
- `www.mine-craft.su`, `site.mine-craft.su` → Nginx → Django
- `vpn.mine-craft.su` → SoftEther VPN

```
Internet → HAProxy (host network)
              ├── :80 → HTTPS redirect / Let's Encrypt
              ├── :443 → SNI routing (web/vpn)
              ├── :25565 → Minecraft (failover)
              └── :25575 → RCON (failover)

Контейнеры на localhost:
  - Nginx: 127.0.0.1:8443 (HTTPS), 127.0.0.1:8080 (HTTP)
  - SoftEther: 127.0.0.1:4443 (SSL VPN)
  - Django: 127.0.0.1:8000 (Gunicorn)

Напрямую на хост (минуя HAProxy):
  - SoftEther: 992/tcp, 5555/tcp (management)
  - SoftEther: 500, 4500, 1701/udp (IPsec/L2TP)
  - SoftEther: 1194/udp (OpenVPN)
```

## Первоначальная настройка VPN

```bash
docker compose -f docker-compose.prod.yml exec softether vpncmd localhost /server

# Внутри vpncmd:
ServerPasswordSet
HubCreate VPN
Hub VPN
UserCreate myuser /GROUP:none /REALNAME:none /NOTE:none
UserPasswordSet myuser
SecureNatEnable
exit
```

## Порты VPN

| Протокол | Порт | Описание |
|----------|------|----------|
| SSTP/SSL | 443/tcp | Через HAProxy (vpn.mine-craft.su) |
| Management | 992/tcp | Администрирование (SoftEther Server Manager) |
| Management | 5555/tcp | Администрирование (альтернативный) |
| L2TP/IPsec | 500, 4500, 1701/udp | Напрямую |
| OpenVPN | 1194/udp | Напрямую |

## Minecraft Failover

HAProxy проверяет доступность хоста `newnout01` (через VPN) и автоматически переключается на резервный сервер `mainserv01.netcraze.pro`.

| Порт | Назначение | Основной | Резервный |
|------|------------|----------|-----------|
| 25565/tcp | Minecraft игра | newnout01:25565 | mainserv01.netcraze.pro:25565 |
| 25575/tcp | RCON | newnout01:25575 | mainserv01.netcraze.pro:25575 |

Параметры проверки: интервал 5 сек, порог недоступности 3, порог восстановления 2.

## VPN клиенты

- **Windows**: Встроенный SSTP клиент или SoftEther Client
- **macOS/iOS**: L2TP/IPsec
- **Android**: SoftEther VPN Client или OpenVPN
- **Linux**: SoftEther Client или OpenVPN

## Мониторинг HAProxy

```bash
curl http://localhost:8404/stats
```

---

# Вариант 2: Ручная установка

## Требования

- Ubuntu 22.04+ / Debian 11+
- Python 3.12, PostgreSQL 15+, Redis 7+, Nginx, Certbot

## 1. Подготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx certbot \
    python3-certbot-nginx git curl
sudo mkdir -p /var/www/blog /var/log/blog /tmp/blog-uploads
sudo chown -R www-data:www-data /var/www/blog /var/log/blog /tmp/blog-uploads
```

## 2. База данных PostgreSQL

```bash
sudo -u postgres psql

CREATE USER blog_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE blog_db OWNER blog_user;
GRANT ALL PRIVILEGES ON DATABASE blog_db TO blog_user;
\c blog_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

## 3. Клонирование и настройка проекта

```bash
cd /var/www/blog
sudo -u www-data git clone https://github.com/riga1897/MyPet01.git .
sudo -u www-data python3.12 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --only main
cp deploy/.env.production.example .env
nano .env
```

## 4. Инициализация Django

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5. Настройка Systemd

```bash
sudo cp deploy/blog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blog
sudo systemctl start blog
sudo systemctl status blog
```

## 6. Настройка Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 7. SSL сертификат (Let's Encrypt)

```bash
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot \
    -d www.mine-craft.su -d site.mine-craft.su
sudo systemctl enable certbot.timer
```

## 8. Настройка Redis

```bash
sudo nano /etc/redis/redis.conf
sudo systemctl restart redis
redis-cli ping
```

## 9. Проверка деплоя

```bash
sudo systemctl status blog nginx redis postgresql
sudo tail -f /var/log/blog/gunicorn-*.log
sudo tail -f /var/log/nginx/blog-*.log
curl -I https://www.mine-craft.su
```

## 10. Обновление приложения

```bash
cd /var/www/blog
sudo -u www-data git pull origin main
source .venv/bin/activate
poetry install --only main
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart blog
```

---

# SSL при CI/CD деплое

SSL сертификаты настраиваются автоматически при деплое:
- **Препрод:** Зависит от `CERTBOT_STAGING` (`1` = тестовый, `0` = реальный)
- **Production:** Всегда реальный сертификат (захардкожен `STAGING=0`)

При первом деплое:
1. Nginx стартует с самоподписанным (dummy) сертификатом
2. CI/CD запускает `init-letsencrypt.sh` для получения сертификата
3. Certbot автоматически обновляет сертификат каждые 12 часов (если нужно)

### Ручная настройка SSL (если нужно)

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

**Автообновление:** Certbot проверяет каждые 12 часов, обновление раз в ~60 дней. Nginx перезагружается раз в неделю для подхвата сертификатов.

---

# Чек-лист деплоя

## Перед деплоем

- [ ] Все тесты проходят: `poetry run pytest`
- [ ] Линтеры чистые: `poetry run ruff check .` и `poetry run mypy .`
- [ ] Docker образ собирается локально: `docker compose build`
- [ ] GitHub Secrets заполнены — [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md#чек-лист)
- [ ] VPS доступен по SSH: `ssh depuser@<IP>`

## После деплоя

- [ ] Сайт открывается: `https://<DOMAIN>`
- [ ] HTTP редиректит на HTTPS
- [ ] Админка доступна: `https://<DOMAIN>/admin/`
- [ ] Логин работает
- [ ] Контент отображается (демо-данные загружены)
- [ ] Медиафайлы доступны для авторизованных пользователей
- [ ] Статика загружается (CSS, JS, изображения)
- [ ] SSL сертификат валидный (замочек в браузере)

## Полезные команды на VPS

```bash
ssh depuser@<IP>
cd /opt/blog-preprod

docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml restart web
docker compose -f docker-compose.prod.yml exec web python manage.py shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('OK')"
docker compose -f docker-compose.prod.yml exec -T web python manage.py setup_demo_content
```

---

# Откат при проблемах

```bash
ssh depuser@<IP>
cd /opt/blog-preprod

# Посмотреть логи
docker compose -f docker-compose.prod.yml logs --tail=100 web

# Откатить к предыдущему образу
docker compose -f docker-compose.prod.yml down
nano .env  # Поменять IMAGE_TAG на предыдущий тег
docker compose -f docker-compose.prod.yml up -d

# Пересоздать .env с нуля
rm .env
SERVER_IP=<IP> ./generate-preprod-env.sh
docker compose -f docker-compose.prod.yml restart
```

---

# Настройка VPN (SoftEther) после деплоя

VPN-сервер SoftEther стартует вместе с контейнерами, но требует ручной настройки:

```bash
docker cp vpn_server.config $(docker ps -q -f name=softether):/usr/vpnserver/vpn_server.config
docker restart $(docker ps -q -f name=softether)
```

> **Важно:** Конфиг VPN содержит пароли и ключи. Не храните его в Git-репозитории.

---

# Troubleshooting

### Ошибка 502 Bad Gateway

```bash
sudo systemctl status blog
sudo tail -50 /var/log/blog/gunicorn-error.log
```

### Статика не загружается

```bash
python manage.py collectstatic --clear --noinput
sudo chown -R www-data:www-data /var/www/blog/staticfiles
```

### Проблемы с базой данных

```bash
psql -U blog_user -d blog_db -h localhost
python manage.py showmigrations
```
