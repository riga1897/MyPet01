# Деплой Blog на VPS

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
