# План миграции на S3-совместимое хранилище

## Обзор

Этот документ описывает план миграции медиафайлов с локального хранилища на S3-совместимое облачное хранилище (AWS S3, Cloudflare R2, DigitalOcean Spaces, MinIO).

## Оценка сложности

| Аспект | Сложность | Время |
|--------|-----------|-------|
| Настройка кода | Низкая | 30 мин |
| Перенос файлов | Зависит от объёма | 1-60 мин |
| Тестирование | Средняя | 1 час |
| Откат (если нужен) | Низкая | 15 мин |

**Общая оценка: 2-4 часа** для типичного блога с < 10 ГБ медиа.

---

## Этап 1: Подготовка

### 1.1 Выбор провайдера

| Провайдер | Плюсы | Минусы | Стоимость |
|-----------|-------|--------|-----------|
| **AWS S3** | Надёжность, экосистема | Сложный биллинг, egress дорогой | $0.023/GB хранение + egress |
| **Cloudflare R2** | Нет платы за egress, S3-совместим | Новый сервис | $0.015/GB хранение |
| **DigitalOcean Spaces** | Простой, включён CDN | Меньше регионов | $5/250GB |
| **MinIO (self-hosted)** | Бесплатно, полный контроль | Нужен сервер | Только инфра |

**Рекомендация:** Cloudflare R2 для production (нет платы за трафик), MinIO для dev/staging.

### 1.2 Создание bucket

```bash
# AWS S3
aws s3 mb s3://mypet-media --region eu-central-1

# Cloudflare R2 (через dashboard или wrangler)
wrangler r2 bucket create mypet-media

# DigitalOcean Spaces
doctl compute cdn create --origin mypet-media.fra1.digitaloceanspaces.com
```

### 1.3 Настройка CORS (обязательно для загрузки из браузера)

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://yourdomain.com"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

---

## Этап 2: Установка зависимостей

```bash
poetry add django-storages boto3
```

---

## Этап 3: Конфигурация Django

### 3.1 Обновить `mypet_project/config.py`

```python
# S3 Storage settings
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""
AWS_STORAGE_BUCKET_NAME: str = ""
AWS_S3_REGION_NAME: str = "eu-central-1"
AWS_S3_ENDPOINT_URL: str = ""  # Для R2/Spaces/MinIO
AWS_S3_CUSTOM_DOMAIN: str = ""  # CDN домен (опционально)
AWS_DEFAULT_ACL: str = "private"  # или "public-read"
AWS_S3_FILE_OVERWRITE: bool = False
AWS_QUERYSTRING_AUTH: bool = True  # Signed URLs для private файлов
USE_S3_STORAGE: bool = False  # Переключатель
```

### 3.2 Обновить `mypet_project/settings.py`

```python
from mypet_project.config import config

if config.USE_S3_STORAGE:
    # S3 storage backend
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": config.AWS_ACCESS_KEY_ID,
                "secret_key": config.AWS_SECRET_ACCESS_KEY,
                "bucket_name": config.AWS_STORAGE_BUCKET_NAME,
                "region_name": config.AWS_S3_REGION_NAME,
                "endpoint_url": config.AWS_S3_ENDPOINT_URL or None,
                "custom_domain": config.AWS_S3_CUSTOM_DOMAIN or None,
                "default_acl": config.AWS_DEFAULT_ACL,
                "file_overwrite": config.AWS_S3_FILE_OVERWRITE,
                "querystring_auth": config.AWS_QUERYSTRING_AUTH,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    # Media URL для S3
    if config.AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{config.AWS_S3_CUSTOM_DOMAIN}/"
    else:
        MEDIA_URL = f"https://{config.AWS_STORAGE_BUCKET_NAME}.s3.{config.AWS_S3_REGION_NAME}.amazonaws.com/"
else:
    # Local storage (текущая конфигурация)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
```

### 3.3 Переменные окружения (.env)

```bash
# S3 Storage
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=mypet-media
AWS_S3_REGION_NAME=eu-central-1

# Для Cloudflare R2
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com

# Для DigitalOcean Spaces
AWS_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com

# CDN (опционально)
AWS_S3_CUSTOM_DOMAIN=cdn.yourdomain.com
```

---

## Этап 4: Миграция существующих файлов

### 4.1 Синхронизация локальных файлов в S3

```bash
# AWS CLI
aws s3 sync ./media/ s3://mypet-media/ --exclude "*.pyc"

# Для R2 (через rclone)
rclone sync ./media/ r2:mypet-media/

# Для Spaces
s3cmd sync ./media/ s3://mypet-media/
```

### 4.2 Проверка синхронизации

```bash
# Подсчёт файлов локально
find ./media -type f | wc -l

# Подсчёт файлов в S3
aws s3 ls s3://mypet-media/ --recursive | wc -l
```

### 4.3 Management команда для проверки целостности

```python
# blog/management/commands/verify_s3_migration.py
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from blog.models import Content

class Command(BaseCommand):
    help = 'Verify all media files exist in S3'

    def handle(self, *args, **options):
        missing = []
        for content in Content.objects.exclude(video_file=''):
            if not default_storage.exists(content.video_file.name):
                missing.append(content.video_file.name)
        
        for content in Content.objects.exclude(thumbnail=''):
            if not default_storage.exists(content.thumbnail.name):
                missing.append(content.thumbnail.name)
        
        if missing:
            self.stderr.write(f"Missing files: {len(missing)}")
            for f in missing[:10]:
                self.stderr.write(f"  - {f}")
        else:
            self.stdout.write(self.style.SUCCESS("All files present in S3"))
```

---

## Этап 5: Обновление кода (если нужно)

### 5.1 Проверить использование MEDIA_ROOT

Поиск прямых обращений к файловой системе:

```bash
grep -r "MEDIA_ROOT" --include="*.py" .
grep -r "os.path.join.*media" --include="*.py" .
```

**Что заменить:**
- `os.path.exists(path)` → `default_storage.exists(name)`
- `open(path, 'rb')` → `default_storage.open(name, 'rb')`
- `os.remove(path)` → `default_storage.delete(name)`

### 5.2 Обновить ProtectedMediaView

```python
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

class ProtectedMediaView(LoginRequiredMixin, View):
    def get(self, request, path):
        if '..' in path or path.startswith('/'):
            raise Http404("Invalid path")
        
        if not default_storage.exists(path):
            raise Http404("File not found")
        
        file = default_storage.open(path, 'rb')
        return FileResponse(file, filename=os.path.basename(path))
```

---

## Этап 6: Тестирование

### 6.1 Локальное тестирование с MinIO

```bash
# Запуск MinIO в Docker
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# .env для тестирования
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=mypet-media
AWS_S3_ENDPOINT_URL=http://localhost:9000
```

### 6.2 Чеклист тестирования

- [ ] Загрузка нового файла через админку
- [ ] Просмотр существующего контента
- [ ] Удаление файла
- [ ] Генерация thumbnail
- [ ] Проверка signed URLs (если private)
- [ ] Проверка CORS (загрузка из браузера)

---

## Этап 7: Деплой

### 7.1 Порядок деплоя

1. Добавить secrets в GitHub/CI:
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   AWS_STORAGE_BUCKET_NAME
   AWS_S3_ENDPOINT_URL (если не AWS)
   ```

2. Синхронизировать файлы с VPS на S3

3. Задеплоить код с `USE_S3_STORAGE=true`

4. Проверить работу сайта

5. (Опционально) Удалить локальные файлы после подтверждения

### 7.2 Docker Compose обновление

```yaml
services:
  web:
    environment:
      - USE_S3_STORAGE=true
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
      - AWS_S3_ENDPOINT_URL=${AWS_S3_ENDPOINT_URL}
```

---

## Откат (если что-то пошло не так)

1. Установить `USE_S3_STORAGE=false` в .env
2. Перезапустить сервис
3. Файлы останутся в S3, но Django будет использовать локальное хранилище

---

## Бюджет и мониторинг

### Оценка стоимости (на примере 50 ГБ медиа, 100 ГБ трафик/месяц)

| Провайдер | Хранение | Трафик | Итого/месяц |
|-----------|----------|--------|-------------|
| AWS S3 | $1.15 | $9.00 | ~$10 |
| Cloudflare R2 | $0.75 | $0 | ~$1 |
| DO Spaces | $5 (250GB) | включён | $5 |

### Мониторинг

```python
# Добавить в Prometheus metrics
from prometheus_client import Counter

s3_uploads = Counter('s3_uploads_total', 'Total S3 uploads')
s3_downloads = Counter('s3_downloads_total', 'Total S3 downloads')
```

---

## Следующие шаги

1. [ ] Выбрать провайдера
2. [ ] Создать bucket и настроить CORS
3. [ ] Добавить зависимости и конфигурацию
4. [ ] Протестировать локально с MinIO
5. [ ] Синхронизировать файлы
6. [ ] Задеплоить на staging
7. [ ] Задеплоить на production
