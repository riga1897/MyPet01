# Настройка VPS и GitHub Secrets

Единый гайд по подготовке VPS и настройке секретов для автоматического деплоя MyPet01.

---

## Быстрый старт (автоматическая настройка)

Скрипт `setup-github.sh` выполняет полный цикл: настройка VPS + установка GitHub Secrets.

### Требования

- **Git Bash** (Windows) или bash (Linux/Mac)
- **GitHub CLI** (`gh`) — установлен и авторизован
- Root-доступ к VPS (по паролю — первоначальный)

### Установка GitHub CLI

```bash
# Windows (PowerShell)
winget install GitHub.cli

# Mac
brew install gh

# Linux
# https://github.com/cli/cli/blob/trunk/docs/install_linux.md
```

### Авторизация

```bash
gh auth login
# Выбрать: GitHub.com → HTTPS → Login with a web browser
gh auth status
```

### Запуск (в Git Bash из директории проекта)

```bash
# Препрод
./scripts/setup-github.sh preprod 217.147.15.220

# Прод
./scripts/setup-github.sh prod 91.204.75.25
```

Скрипт автоматически:
- Подключается к VPS как root (по паролю)
- Создаёт пользователей `depuser` (деплой) и `useradmin` (администратор)
- Генерирует SSH ключи для GitHub Actions и администратора
- Меняет пароль root на новый случайный
- Отключает root SSH
- Устанавливает GitHub Secrets
- Для препрода — устанавливает Variables (`CERTBOT_STAGING`, `LOAD_DEMO_DATA`, `CREATE_PR_ON_PREDEPLOY`)
- Выводит пароль root и ключ администратора для сохранения

> **Важно:** После завершения скрипта сохраните пароль root и ключ администратора — они больше нигде не доступны!

> **Примечание**: Docker, UFW, fail2ban и директория деплоя установятся автоматически при первом деплое через CI/CD.

---

## Только настройка VPS (без GitHub)

```bash
# На VPS от root:
./setup_vps.sh preprod   # или prod
```

Затем вручную настройте GitHub Secrets (см. раздел ниже).

---

## Ручная настройка depuser

### Шаг 1: Создание пользователя

```bash
ssh root@<IP_ВАШЕГО_VPS>
adduser --disabled-password --gecos "Deploy User" depuser
```

### Шаг 2: Настройка ограниченных прав sudo

> Docker, UFW, fail2ban и директория деплоя установятся автоматически при первом деплое через GitHub Actions.

```bash
cat > /etc/sudoers.d/depuser << 'EOF'
Cmnd_Alias DEPLOY_APT = /usr/bin/apt-get update, /usr/bin/apt-get install *
Cmnd_Alias DEPLOY_DOCKER_SETUP = /usr/sbin/usermod -aG docker *, /usr/bin/install -m 0755 -d /etc/apt/keyrings, /usr/bin/gpg --dearmor -o /etc/apt/keyrings/docker.gpg, /bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/tee /etc/apt/sources.list.d/docker.list
Cmnd_Alias DEPLOY_DIRS = /bin/mkdir -p *, /usr/bin/mkdir -p *, /bin/chown -R *, /usr/bin/chown -R *
Cmnd_Alias DEPLOY_SYSTEMCTL = /usr/bin/systemctl enable docker, /usr/bin/systemctl start docker, /usr/bin/systemctl restart docker, /usr/bin/systemctl enable fail2ban, /usr/bin/systemctl start fail2ban, /usr/bin/systemctl restart fail2ban
Cmnd_Alias DEPLOY_UFW = /usr/sbin/ufw default *, /usr/sbin/ufw allow *, /usr/sbin/ufw enable, /usr/sbin/ufw status *
Cmnd_Alias DEPLOY_SYSCTL = /usr/bin/tee -a /etc/sysctl.conf, /usr/sbin/sysctl -p
depuser ALL=(ALL) NOPASSWD: DEPLOY_APT, DEPLOY_DOCKER_SETUP, DEPLOY_DIRS, DEPLOY_SYSTEMCTL, DEPLOY_UFW, DEPLOY_SYSCTL
EOF
chmod 440 /etc/sudoers.d/depuser
visudo -cf /etc/sudoers.d/depuser
```

#### Что разрешено depuser

| Категория | Команды | Назначение |
|-----------|---------|------------|
| APT | `apt-get update`, `apt-get install` | Установка пакетов |
| Docker Setup | `usermod`, `install`, `gpg`, `chmod`, `tee` | Настройка Docker репозитория |
| Директории | `mkdir -p`, `chown -R` | Создание директории деплоя |
| Systemctl | `systemctl enable/start/restart docker/fail2ban` | Управление сервисами |
| UFW | `ufw default/allow/enable/status` | Настройка файрвола |
| Sysctl | `tee -a /etc/sysctl.conf`, `sysctl -p` | Unprivileged port binding (HAProxy) |

#### Что запрещено

- Редактирование файлов (`nano`, `vim`, `vi`)
- Удаление файлов и директорий (`rm`, `rmdir`)
- Управление пользователями (`adduser`, `deluser`, `passwd`)
- Изменение сетевых настроек (`iptables`)
- Полный root-доступ

### Шаг 3: Генерация SSH-ключа

```bash
mkdir -p /home/depuser/.ssh
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /home/depuser/.ssh/github_deploy -N ""
cat /home/depuser/.ssh/github_deploy.pub >> /home/depuser/.ssh/authorized_keys
sort -u /home/depuser/.ssh/authorized_keys -o /home/depuser/.ssh/authorized_keys
```

### Шаг 4: Настройка прав на файлы

```bash
chown -R depuser:depuser /home/depuser/.ssh
chmod 700 /home/depuser/.ssh
chmod 600 /home/depuser/.ssh/authorized_keys
chmod 600 /home/depuser/.ssh/github_deploy
chmod 600 /home/depuser/.ssh/github_deploy.pub
```

### Шаг 5: Скопировать приватный ключ

```bash
cat /home/depuser/.ssh/github_deploy
```

Скопируйте **весь** вывод, включая строки `-----BEGIN` и `-----END`.

---

## Требования к VPS

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| ОС | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 |
| RAM | 1 GB | 2 GB |
| Диск | 10 GB | 20 GB |
| CPU | 1 vCPU | 2 vCPU |

---

## GitHub Secrets

Перейти: GitHub → Repository → Settings → Secrets and variables → Actions → **New repository secret**

### Общие

| Secret | Описание | Как получить |
|--------|----------|--------------|
| `GHCR_TOKEN` | Personal Access Token для GHCR | GitHub → Settings → Developer settings → Personal access tokens → Classic → scope: `read:packages` |

### Production

| Secret | Описание | Пример |
|--------|----------|--------|
| `SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `SSH_USER` | Имя пользователя SSH | `depuser` |
| `SERVER_IP` | IP адрес production VPS | `91.204.75.25` |
| `DEPLOY_DIR` | Путь для деплоя | `/opt/blog` |

### Pre-Production

| Secret | Описание | Пример |
|--------|----------|--------|
| `PREPROD_SSH_KEY` | SSH ключ для препрода | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `PREPROD_SSH_USER` | Пользователь SSH | `depuser` |
| `PREPROD_SERVER_IP` | IP препрод сервера | `217.147.15.220` |
| `PREPROD_DEPLOY_DIR` | Путь деплоя | `/opt/blog-preprod` |

### Автогенерируемые значения

Генерируются автоматически скриптом на VPS:
- `SECRET_KEY` — Django secret (50 chars)
- `POSTGRES_PASSWORD` — Пароль БД (24 chars)

---

## GitHub Personal Access Token

1. Перейти: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Нажать **Generate new token (classic)**
3. Название: `MyPet01 GHCR`
4. Срок: выбрать подходящий (90 дней или без срока)
5. Отметить scope: `read:packages`
6. Нажать **Generate token**
7. **Скопировать токен** (покажется только один раз!)

---

## Repository Variables

Вкладка **Variables** (не Secrets):

| Variable | Описание | Значения | По умолчанию | Область |
|----------|----------|----------|--------------|---------|
| `LOAD_DEMO_DATA` | Загрузка демо-данных | `true` / `false` | `false` | Только препрод |
| `CERTBOT_STAGING` | Тестовый SSL (staging Let's Encrypt) | `0` / `1` | `0` | Только препрод |
| `CREATE_PR_ON_PREDEPLOY` | Создание draft PR в main | `true` / `false` | `true` | Только препрод |

> **Важно:** `CERTBOT_STAGING` и `LOAD_DEMO_DATA` влияют **только на препрод**. В production SSL всегда реальный, демо-данные не загружаются.

---

## Идемпотентность .env

Скрипты `generate-production-env.sh` и `generate-preprod-env.sh`:
- Если `.env` существует → **НЕ перезаписывают**
- Секреты сохраняются между деплоями
- Для пересоздания: удалите `.env` вручную

```bash
ssh user@vps "rm /opt/blog/.env"
git push origin main
```

---

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
- [ ] `CERTBOT_STAGING` — `1` для тестовых сертификатов
- [ ] `CREATE_PR_ON_PREDEPLOY` — `false` если не нужны PR

---

## Проверка

### Проверить подключение

```bash
ssh -i ~/.ssh/depuser_key depuser@<IP_VPS>
```

### Проверить инфраструктуру (после первого деплоя)

```bash
docker ps
docker compose version
sudo ufw status
sudo systemctl status fail2ban
```

### Проверить ограничения sudo

```bash
sudo apt-get update       # ← должно работать
sudo rm -rf /             # ← запрещено
sudo reboot               # ← запрещено
sudo nano /etc/hosts      # ← запрещено
```

---

## Безопасность

### Рекомендации

1. **Отключить вход root по SSH** (после настройки depuser):
   ```bash
   sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
   systemctl restart sshd
   ```

2. **Отключить вход по паролю** (только ключи):
   ```bash
   sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   systemctl restart sshd
   ```

3. **Ротация ключей**: периодически генерируйте новый SSH-ключ и обновляйте GitHub Secret

### Принцип минимальных привилегий

`depuser` работает по принципу **least privilege**:
- Docker-команды через членство в группе `docker` (без sudo)
- sudo разрешён только для ограниченного набора команд при первоначальной настройке
- После установки инфраструктуры sudo фактически не используется

---

## Troubleshooting

### Permission denied (publickey)
1. Проверьте публичный ключ на VPS: `cat ~/.ssh/authorized_keys`
2. Проверьте приватный ключ в GitHub Secrets

### .env не изменился после деплоя
Скрипт пропускает генерацию если `.env` уже существует. Удалите `.env` на VPS и деплойте снова.

### Демо-данные не загрузились
1. Проверьте `LOAD_DEMO_DATA=true` в GitHub Variables
2. Проверьте `.env` на VPS: `grep LOAD_DEMO_DATA .env`
3. Загрузите вручную: `docker compose -f docker-compose.prod.yml exec -T web python manage.py setup_demo_content`

---

## FAQ

**Q: Что если Docker уже установлен?**
A: CI/CD проверяет наличие и пропускает установку. То же для UFW и fail2ban.

**Q: Можно использовать другое имя пользователя?**
A: Да, в скрипте: `DEPLOY_USER=myuser bash setup_vps.sh`. Укажите это имя в `SSH_USER`.

**Q: Что делать при компрометации ключа?**
A: Удалите публичный ключ из `authorized_keys`, сгенерируйте новый и обновите GitHub Secret.
