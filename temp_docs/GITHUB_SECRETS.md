# GitHub Secrets Configuration Guide

Этот документ описывает настройку GitHub Secrets для автоматического деплоя на production VPS.

---

## Обзор

GitHub Secrets используются для безопасного хранения конфиденциальных данных (API ключи, SSH ключи, IP адреса) и передачи их в CI/CD pipeline без коммита в Git.

**Преимущества:**
- ✅ Безопасность — секреты зашифрованы в GitHub
- ✅ Автоматизация — деплой без ручной настройки .env на VPS
- ✅ Версионирование — изменение секретов без пересборки образов
- ✅ Удобство — один `git push main` → полный деплой

---

## Как добавить секреты в GitHub

1. Откройте ваш репозиторий на GitHub
2. Перейдите: **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Введите **Name** (имя секрета) и **Value** (значение)
5. Нажмите **Add secret**

![GitHub Secrets Location](https://docs.github.com/assets/cb-28421/images/help/repository/actions-secrets-settings.png)

---

## Обязательные секреты

Эти секреты **НЕОБХОДИМЫ** для работы CI/CD pipeline:

### 1. SSH_KEY
**Описание:** Приватный SSH ключ для доступа к VPS  
**Как получить:**
```bash
# На вашей локальной машине (любая ОС)
ssh-keygen -t ed25519 -C "github-actions-deploy"

# Сохраните ключ в файл (например: ~/.ssh/github_deploy_key)
# НЕ УСТАНАВЛИВАЙТЕ PASSPHRASE (оставьте пустым)!

# Скопируйте публичный ключ на VPS
ssh-copy-id -i ~/.ssh/github_deploy_key.pub user@your-vps-ip

# Прочитайте приватный ключ для копирования в GitHub
cat ~/.ssh/github_deploy_key
```

**Значение для GitHub Secret:**  
Полное содержимое файла `~/.ssh/github_deploy_key` (начинается с `-----BEGIN OPENSSH PRIVATE KEY-----`)

---

### 2. SSH_USER
**Описание:** Имя пользователя для SSH подключения к VPS  
**Пример:** `root` или `ubuntu` или `deploy`

**Как узнать:**
```bash
# Ваш пользователь на VPS
whoami
```

---

### 3. SERVER_IP
**Описание:** IP адрес вашего production VPS  
**Пример:** `123.45.67.89`

**Как узнать:**
```bash
# На VPS выполните:
curl ifconfig.me
```

**⚠️ ВАЖНО:** Этот IP используется для:
- `ALLOWED_HOSTS` в Django
- `SITE_DOMAIN` для построения URL
- `CORS_ALLOWED_ORIGINS`

---

### 4. DEPLOY_DIR
**Описание:** Путь к директории для деплоя на VPS  
**Рекомендуемое значение:** `/opt/lms`

**Создание директории на VPS:**
```bash
# Подключитесь к VPS
ssh user@your-vps-ip

# Создайте директорию
sudo mkdir -p /opt/lms
sudo chown $USER:$USER /opt/lms
```

---

### 5. PROD_STRIPE_SECRET_KEY
**Описание:** Stripe Secret Key для production платежей  
**Формат:** `sk_live_...` (production) или `sk_test_...` (test режим)

**Как получить:**
1. Перейдите на https://dashboard.stripe.com/apikeys
2. Войдите в аккаунт Stripe
3. Переключитесь на **Live mode** (правый верхний угол)
4. Скопируйте **Secret key** (начинается с `sk_live_`)

**⚠️ SECURITY WARNING:**
- **НИКОГДА** не коммитьте этот ключ в Git!
- Используйте test ключи (`sk_test_...`) для staging окружения
- Production ключи (`sk_live_...`) только для VPS

---

### 6. PROD_STRIPE_PUBLISHABLE_KEY
**Описание:** Stripe Publishable Key (публичный ключ)  
**Формат:** `pk_live_...` (production) или `pk_test_...` (test режим)

**Как получить:**
1. Перейдите на https://dashboard.stripe.com/apikeys
2. Войдите в аккаунт Stripe
3. Переключитесь на **Live mode**
4. Скопируйте **Publishable key** (начинается с `pk_live_`)

**Примечание:** Этот ключ технически не секретный (используется в frontend), но удобнее хранить в secrets для единообразия.

---

## Опциональные секреты

Эти секреты нужны только если требуется дополнительная функциональность:

### PROD_EMAIL_HOST_USER
**Описание:** Email адрес для отправки уведомлений  
**Пример:** `noreply@yourdomain.com` или `your-gmail@gmail.com`

**Когда нужен:** Если хотите отправлять реальные email (не только в логи)

---

### PROD_EMAIL_HOST_PASSWORD
**Описание:** Пароль для SMTP сервера  
**Пример (Gmail):** App-specific password (НЕ ваш обычный пароль!)

**Как получить для Gmail:**
1. Включите 2FA на аккаунте Google
2. Перейдите: https://myaccount.google.com/apppasswords
3. Создайте App Password для "Mail"
4. Скопируйте сгенерированный пароль (16 символов)

**Когда нужен:** Если используете реальную SMTP отправку email

**Примечание:** По умолчанию проект использует `console backend` — email выводятся в логи Docker. Это достаточно для большинства случаев.

---

## Полный чек-лист секретов

Перед первым деплоем убедитесь что добавили:

- [x] `SSH_KEY` — приватный SSH ключ для доступа к VPS
- [x] `SSH_USER` — имя пользователя на VPS
- [x] `SERVER_IP` — IP адрес VPS
- [x] `DEPLOY_DIR` — путь для деплоя (рекомендуется `/opt/lms`)
- [x] `PROD_STRIPE_SECRET_KEY` — Stripe secret key
- [x] `PROD_STRIPE_PUBLISHABLE_KEY` — Stripe publishable key
- [ ] `PROD_EMAIL_HOST_USER` — опционально, для email
- [ ] `PROD_EMAIL_HOST_PASSWORD` — опционально, для email

---

## Как работает автогенерация .env

GitHub Actions автоматически генерирует `.env` файл на VPS используя скрипт `scripts/generate-production-env.sh`:

### Автоматически генерируются:
- ✅ `SECRET_KEY` — Django secret (50 chars, URL-safe, без `$`)
- ✅ `POSTGRES_PASSWORD` — пароль БД (base64, 24 bytes)
- ✅ ~20 других переменных (DEBUG, хосты, Redis, Celery, пути)

### Берутся из GitHub Secrets:
- ✅ `STRIPE_SECRET_KEY` ← `PROD_STRIPE_SECRET_KEY`
- ✅ `STRIPE_PUBLISHABLE_KEY` ← `PROD_STRIPE_PUBLISHABLE_KEY`
- ✅ `ALLOWED_HOSTS`, `SITE_DOMAIN`, `CORS_ALLOWED_ORIGINS` ← `SERVER_IP`

### Идемпотентность:
- Если `.env` уже существует → скрипт **НЕ перезаписывает** его
- Секреты сохраняются между деплоями
- Для пересоздания: удалите `.env` вручную на VPS и запустите деплой

---

## Проверка секретов

После добавления всех секретов проверьте их наличие:

```bash
# В GitHub репозитории перейдите:
# Settings → Secrets and variables → Actions → Repository secrets

# Должны видеть (значения скрыты):
# - SSH_KEY
# - SSH_USER
# - SERVER_IP
# - DEPLOY_DIR
# - PROD_STRIPE_SECRET_KEY
# - PROD_STRIPE_PUBLISHABLE_KEY
```

---

## Обновление секретов

Чтобы изменить секрет:

1. GitHub → Settings → Secrets and variables → Actions
2. Найдите нужный секрет в списке
3. Нажмите **Update**
4. Введите новое значение
5. Нажмите **Update secret**

**Примечание:** После обновления Stripe ключей нужно:
1. Удалить `.env` на VPS: `ssh user@vps-ip "rm /opt/lms/.env"`
2. Запустить деплой: `git push origin main`

---

## Безопасность

### ✅ DO:
- Используйте разные ключи для test/production
- Регулярно ротируйте SSH ключи
- Проверяйте логи деплоя на утечки секретов
- Используйте `sk_live_` ключи только для production VPS

### ❌ DON'T:
- **НИКОГДА** не коммитьте секреты в Git
- Не используйте production ключи локально
- Не шарите SSH_KEY с другими людьми
- Не выводите секреты в логи (GitHub Actions автоматически маскирует их)

---

## Troubleshooting

### Ошибка: "SSH_KEY environment variable is not set"
**Решение:** Добавьте `SSH_KEY` в GitHub Secrets

### Ошибка: "STRIPE_SECRET_KEY environment variable is not set"
**Решение:** Добавьте `PROD_STRIPE_SECRET_KEY` и `PROD_STRIPE_PUBLISHABLE_KEY` в GitHub Secrets

### Ошибка: "Permission denied (publickey)"
**Решение:** 
1. Проверьте что публичный ключ добавлен на VPS: `cat ~/.ssh/authorized_keys`
2. Проверьте что приватный ключ корректный в GitHub Secrets

### Деплой успешен, но .env не изменился
**Причина:** Скрипт пропускает генерацию если `.env` уже существует (идемпотентность)  
**Решение:** Удалите `.env` на VPS и запустите деплой снова:
```bash
ssh user@vps-ip "rm /opt/lms/.env"
git commit --allow-empty -m "Trigger .env regeneration"
git push origin main
```

---

## Дополнительная документация

- [CI/CD Pipeline](./CI_CD.md) — полное описание автоматизации
- [Deployment Strategy](./DEPLOYMENT_STRATEGY.md) — стратегия деплоя
- [Staging Testing](./STAGING_TESTING.md) — локальное staging тестирование с Docker

---

**Дата обновления:** 2025-11-23  
**Версия:** 1.0
