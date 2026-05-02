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
# VPS2 (pre-production)
./scripts/setup-github.sh vps2 $VPS2_SERVER_IP

# VPS1 (production)
./scripts/setup-github.sh vps1 $VPS1_SERVER_IP
```

Скрипт автоматически:
- Подключается к VPS как root (по паролю)
- Создаёт пользователей `depuser` (деплой) и `useradmin` (администратор)
- Генерирует SSH ключи для GitHub Actions и администратора
- Меняет пароль root на новый случайный
- Отключает root SSH
- Устанавливает GitHub Secrets
- Для VPS2 — устанавливает Variables (`CERTBOT_STAGING`, `LOAD_DEMO_DATA`, `CREATE_PR_ON_VPS2DEPLOY`)
- Выводит пароль root и ключ администратора для сохранения

> **Важно:** После завершения скрипта сохраните пароль root и ключ администратора — они больше нигде не доступны!

> **Примечание**: Docker, UFW, fail2ban и директория деплоя установятся автоматически при первом деплое через CI/CD.

---

## Только настройка VPS (без GitHub)

```bash
# На VPS от root:
./setup_vps.sh vps2   # или vps1
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

| Параметр | VPS1 (Production) | VPS2 (Hot Standby) | VPS3 (Management) |
|----------|-------------------|--------------------|-------------------|
| CPU | 4 vCPU | 4 vCPU | 2 vCPU |
| RAM | 4 GB | 4 GB | 2 GB |
| Диск | 40 GB SSD | 80 GB SSD | 40 GB SSD |
| ОС | Ubuntu 22.04 | Ubuntu 22.04 | Ubuntu 22.04 |

---

## GitHub Secrets

Перейти: GitHub → Repository → Settings → Secrets and variables → Actions → **New repository secret**

IP-адреса хранятся **только** в GitHub Secrets. В коде и конфигах используются только имена переменных.

### Общие

| Secret | Описание | Как получить |
|--------|----------|--------------|
| `GHCR_TOKEN` | Personal Access Token для GHCR | GitHub → Settings → Developer settings → Personal access tokens → Classic → scope: `read:packages` |

### VPS1 (Production — ветка `main`)

| Secret | Описание | Пример |
|--------|----------|--------|
| `VPS1_SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `VPS1_SSH_USER` | Имя пользователя SSH | `depuser` |
| `VPS1_SERVER_IP` | IP адрес VPS1 | вставить после создания |
| `VPS1_DEPLOY_DIR` | Путь для деплоя | `/opt/mypet01` |

### VPS2 (Pre-Production — ветка `release/*`)

| Secret | Описание | Пример |
|--------|----------|--------|
| `VPS2_SSH_KEY` | SSH ключ для VPS2 | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `VPS2_SSH_USER` | Пользователь SSH | `depuser` |
| `VPS2_SERVER_IP` | IP VPS2 сервера | вставить после создания |
| `VPS2_DEPLOY_DIR` | Путь деплоя | `/opt/mypet01` |

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
| `LOAD_DEMO_DATA` | Загрузка демо-данных | `true` / `false` | `false` | Только VPS2 |
| `CERTBOT_STAGING` | Тестовый SSL (staging Let's Encrypt) | `0` / `1` | `0` | Только VPS2 |
| `CREATE_PR_ON_VPS2DEPLOY` | Создание draft PR в main | `true` / `false` | `true` | Только VPS2 |

> **Важно:** `CERTBOT_STAGING` и `LOAD_DEMO_DATA` влияют **только на VPS2**. На VPS1 SSL всегда реальный, демо-данные не загружаются.

---

## Идемпотентность .env

Скрипты `generate-vps1-env.sh` и `generate-vps2-env.sh`:
- Если `.env` существует → **НЕ перезаписывают**
- Секреты сохраняются между деплоями
- Для пересоздания: удалите `.env` вручную

```bash
ssh user@vps "rm /opt/mypet01/.env"
git push origin main
```

---

## Чек-лист

### Общие
- [ ] `GHCR_TOKEN` — Personal Access Token с правами `read:packages`

### VPS1 (Production)
- [ ] `VPS1_SSH_KEY`
- [ ] `VPS1_SSH_USER`
- [ ] `VPS1_SERVER_IP`
- [ ] `VPS1_DEPLOY_DIR`

### VPS2 (Pre-Production / Hot Standby)
- [ ] `VPS2_SSH_KEY`
- [ ] `VPS2_SSH_USER`
- [ ] `VPS2_SERVER_IP`
- [ ] `VPS2_DEPLOY_DIR`

### Variables (опциональные)
- [ ] `LOAD_DEMO_DATA` — `true` для VPS2
- [ ] `CERTBOT_STAGING` — `1` для тестовых сертификатов
- [ ] `CREATE_PR_ON_VPS2DEPLOY` — `false` если не нужны PR

---

## Проверка

### Проверить подключение

```bash
ssh -i ~/.ssh/depuser_key depuser@$VPS1_SERVER_IP
ssh -i ~/.ssh/depuser_key depuser@$VPS2_SERVER_IP
```

### Проверить инфраструктуру (после первого деплоя)

```bash
docker ps
docker compose version
sudo ufw status
sudo systemctl status fail2ban
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
2. Проверьте приватный ключ в GitHub Secrets (`VPS1_SSH_KEY` или `VPS2_SSH_KEY`)

### .env не изменился после деплоя
Скрипт пропускает генерацию если `.env` уже существует. Удалите `.env` на VPS и деплойте снова.

### Демо-данные не загрузились
1. Проверьте `LOAD_DEMO_DATA=true` в GitHub Variables
2. Проверьте `.env` на VPS: `grep LOAD_DEMO_DATA .env`
3. Загрузите вручную: `docker compose -f docker-compose.prod.yml exec -T web python manage.py setup_demo_content`
