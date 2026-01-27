# Деплой Blog на VPS

Два варианта деплоя:
- **Docker (рекомендуется)** — быстрый и простой
- **Ручная установка** — для тонкой настройки

---

# Вариант 1: Docker (рекомендуется)

## Требования

- Ubuntu 22.04+ / Debian 11+
- Docker 24+
- Docker Compose v2+

## 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Перелогиниться для применения группы
exit
# Войти снова
```

## 2. Клонирование проекта

```bash
mkdir -p /opt/blog && cd /opt/blog
git clone https://github.com/riga1897/MyPet01.git .
```

## 3. Настройка переменных окружения

```bash
cp deploy/.env.production.example .env
nano .env  # Заполнить реальными значениями

# Обязательно установить:
# - SECRET_KEY (сгенерировать: openssl rand -hex 32)
# - POSTGRES_PASSWORD
# - ALLOWED_HOSTS
```

## 4. SSL сертификаты

```bash
# Создать директории для сертификатов
mkdir -p nginx/ssl nginx/certbot

# Вариант A: Let's Encrypt (бесплатно) — включая VPN домен!
sudo apt install certbot
sudo certbot certonly --standalone \
    -d www.mine-craft.su \
    -d site.mine-craft.su \
    -d vpn.mine-craft.su

# Копировать сертификаты (используются и Nginx, и SoftEther VPN)
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
# Подключиться к VPN серверу
docker compose -f docker-compose.prod.yml exec softether vpncmd localhost /server

# Установить сертификат Let's Encrypt
ServerCertSet /LOADCERT:/etc/ssl/vpn/fullchain.pem /LOADKEY:/etc/ssl/vpn/privkey.pem

# Проверить установленный сертификат
ServerCertGet
```

### Автообновление сертификатов

```bash
# Сделать скрипт исполняемым
chmod +x deploy/renew-certs.sh

# Добавить в crontab (проверка дважды в день)
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
# Сборка и запуск
docker compose -f docker-compose.prod.yml up -d --build

# Применение миграций
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Создание суперпользователя
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Проверка статуса
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

## 8. Настройка SoftEther VPN

Архитектура использует HAProxy для SNI-роутинга трафика на 443 порту:
- `www.mine-craft.su`, `site.mine-craft.su` → Nginx → Django
- `vpn.mine-craft.su` → SoftEther VPN

### Сетевая архитектура

HAProxy работает в режиме `network_mode: host` — это позволяет ему видеть VPN сеть SoftEther и обращаться к VPN клиентам напрямую.

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

### Первоначальная настройка VPN

```bash
# Подключение к vpncmd для настройки
docker compose -f docker-compose.prod.yml exec softether vpncmd localhost /server

# Внутри vpncmd:
# 1. Установить пароль администратора
ServerPasswordSet

# 2. Создать Virtual Hub
HubCreate VPN
Hub VPN

# 3. Создать пользователя
UserCreate myuser /GROUP:none /REALNAME:none /NOTE:none
UserPasswordSet myuser

# 4. Включить SecureNAT (для доступа к интернету через VPN)
SecureNatEnable

# 5. Выход
exit
```

### Порты VPN

| Протокол | Порт | Описание |
|----------|------|----------|
| SSTP/SSL | 443/tcp | Через HAProxy (vpn.mine-craft.su) |
| Management | 992/tcp | Администрирование (SoftEther Server Manager) |
| Management | 5555/tcp | Администрирование (альтернативный) |
| L2TP/IPsec | 500, 4500, 1701/udp | Напрямую |
| OpenVPN | 1194/udp | Напрямую |

### Minecraft Failover

HAProxy проверяет доступность хоста `newnout01` (через VPN) и автоматически переключается на резервный сервер `mainserv01.netcraze.pro` если основной недоступен.

| Порт | Назначение | Основной | Резервный |
|------|------------|----------|-----------|
| 25565/tcp | Minecraft игра | newnout01:25565 | mainserv01.netcraze.pro:25565 |
| 25575/tcp | RCON | newnout01:25575 | mainserv01.netcraze.pro:25575 |

Параметры проверки:
- Интервал: 5 секунд
- Порог недоступности: 3 неудачные проверки
- Порог восстановления: 2 успешные проверки

### Клиенты

- **Windows**: Встроенный SSTP клиент или SoftEther Client
- **macOS/iOS**: L2TP/IPsec
- **Android**: SoftEther VPN Client или OpenVPN
- **Linux**: SoftEther Client или OpenVPN

### Мониторинг HAProxy

```bash
# Статистика HAProxy доступна на :8404/stats
curl http://localhost:8404/stats
```

---

# Вариант 2: Ручная установка

## Требования

- Ubuntu 22.04+ / Debian 11+
- Python 3.12
- PostgreSQL 15+
- Redis 7+
- Nginx
- Certbot (для SSL)

---

## 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx certbot \
    python3-certbot-nginx git curl

# Создание пользователя и директорий
sudo mkdir -p /var/www/blog /var/log/blog /tmp/blog-uploads
sudo chown -R www-data:www-data /var/www/blog /var/log/blog /tmp/blog-uploads
```

---

## 2. База данных PostgreSQL

```bash
# Вход под пользователем postgres
sudo -u postgres psql

# Создание базы и пользователя
CREATE USER blog_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE blog_db OWNER blog_user;
GRANT ALL PRIVILEGES ON DATABASE blog_db TO blog_user;

# Включение расширений
\c blog_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

---

## 3. Клонирование и настройка проекта

```bash
cd /var/www/blog

# Клонирование репозитория
sudo -u www-data git clone https://github.com/riga1897/MyPet01.git .

# Создание виртуального окружения
sudo -u www-data python3.12 -m venv .venv
source .venv/bin/activate

# Установка Poetry и зависимостей
pip install poetry
poetry install --only main

# Копирование и настройка .env
cp deploy/.env.production.example .env
nano .env  # Заполнить реальными значениями
```

---

## 4. Инициализация Django

```bash
source .venv/bin/activate

# Применение миграций
python manage.py migrate

# Сбор статики
python manage.py collectstatic --noinput

# Создание суперпользователя
python manage.py createsuperuser
```

---

## 5. Настройка Systemd

```bash
# Копирование сервиса
sudo cp deploy/blog.service /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение и запуск
sudo systemctl enable blog
sudo systemctl start blog

# Проверка статуса
sudo systemctl status blog
```

---

## 6. Настройка Nginx

```bash
# Копирование конфигурации
sudo cp deploy/nginx.conf /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/

# Удаление дефолтного сайта
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск nginx
sudo systemctl reload nginx
```

---

## 7. SSL сертификат (Let's Encrypt)

```bash
# Создание директории для certbot
sudo mkdir -p /var/www/certbot

# Получение сертификата
sudo certbot certonly --webroot -w /var/www/certbot \
    -d www.mine-craft.su -d site.mine-craft.su

# Автопродление (добавляется автоматически)
sudo systemctl enable certbot.timer
```

---

## 8. Настройка Redis

```bash
# Редактирование конфигурации (опционально)
sudo nano /etc/redis/redis.conf

# Перезапуск
sudo systemctl restart redis

# Проверка
redis-cli ping  # Должен ответить PONG
```

---

## 9. Проверка деплоя

```bash
# Проверка сервисов
sudo systemctl status blog nginx redis postgresql

# Логи приложения
sudo tail -f /var/log/blog/gunicorn-*.log

# Логи nginx
sudo tail -f /var/log/nginx/blog-*.log

# Тест сайта
curl -I https://www.mine-craft.su
```

---

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

## Полезные команды

```bash
# Перезапуск приложения
sudo systemctl restart blog

# Просмотр логов в реальном времени
sudo journalctl -u blog -f

# Проверка портов
sudo ss -tlnp | grep -E '80|443|8000'

# Очистка кэша Redis
redis-cli FLUSHDB
```

---

## Troubleshooting

### Ошибка 502 Bad Gateway
```bash
# Проверить, запущен ли gunicorn
sudo systemctl status blog
# Проверить логи
sudo tail -50 /var/log/blog/gunicorn-error.log
```

### Статика не загружается
```bash
# Пересобрать статику
python manage.py collectstatic --clear --noinput
# Проверить права
sudo chown -R www-data:www-data /var/www/blog/staticfiles
```

### Проблемы с базой данных
```bash
# Проверить подключение
psql -U blog_user -d blog_db -h localhost
# Проверить миграции
python manage.py showmigrations
```
