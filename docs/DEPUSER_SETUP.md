# Создание пользователя depuser для деплоя

Пошаговая инструкция по созданию выделенного пользователя `depuser` на VPS для автоматического развёртывания через GitHub Actions.

## Зачем отдельный пользователь?

- **Безопасность**: GitHub Actions не подключается к серверу под root
- **Ограничение прав**: depuser имеет только те права, которые нужны для деплоя
- **Аудит**: все действия деплоя логируются от имени отдельного пользователя
- **Изоляция**: компрометация SSH-ключа не даёт полный root-доступ

---

## Вариант 1: Автоматическая настройка (рекомендуется)

Скрипт `scripts/setup_vps.sh` создаёт пользователя автоматически:

```bash
# Подключиться к VPS как root
ssh root@<IP_ВАШЕГО_VPS>

# Скачать и запустить скрипт
scp scripts/setup_vps.sh root@<IP>:/tmp/
ssh root@<IP> "bash /tmp/setup_vps.sh"
```

Скрипт создаст пользователя `depuser` со всеми необходимыми правами.

---

## Вариант 2: Ручная настройка

### Шаг 1: Создание пользователя

Подключитесь к VPS как root:

```bash
ssh root@<IP_ВАШЕГО_VPS>
```

Создайте пользователя без пароля (авторизация только по SSH-ключу):

```bash
adduser --disabled-password --gecos "Deploy User" depuser
```

### Шаг 2: Добавление в группу docker

Чтобы `depuser` мог управлять контейнерами без sudo:

```bash
usermod -aG docker depuser
```

> **Важно**: Docker должен быть установлен до этого шага. Если Docker ещё не установлен — сначала установите его (см. [DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)).

### Шаг 3: Настройка ограниченных прав sudo

Создайте файл sudoers с ограниченными правами:

```bash
cat > /etc/sudoers.d/depuser << 'EOF'
# Команды для первоначальной установки Docker (CI/CD)
# Пути /bin/ и /usr/bin/ для совместимости с Ubuntu/Debian
Cmnd_Alias DEPLOY_APT = /usr/bin/apt-get update, /usr/bin/apt-get install *
Cmnd_Alias DEPLOY_DOCKER_SETUP = /usr/sbin/usermod -aG docker *, /usr/bin/install -m 0755 -d /etc/apt/keyrings, /usr/bin/gpg --dearmor -o /etc/apt/keyrings/docker.gpg, /bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/tee /etc/apt/sources.list.d/docker.list
Cmnd_Alias DEPLOY_DIRS = /bin/mkdir -p *, /usr/bin/mkdir -p *, /bin/chown -R *, /usr/bin/chown -R *
Cmnd_Alias DEPLOY_SYSTEMCTL = /usr/bin/systemctl enable docker, /usr/bin/systemctl start docker, /usr/bin/systemctl restart docker
depuser ALL=(ALL) NOPASSWD: DEPLOY_APT, DEPLOY_DOCKER_SETUP, DEPLOY_DIRS, DEPLOY_SYSTEMCTL
EOF
chmod 440 /etc/sudoers.d/depuser
```

Проверьте синтаксис:

```bash
visudo -cf /etc/sudoers.d/depuser
```

Должно вывести: `/etc/sudoers.d/depuser: parsed OK`

#### Что разрешено depuser:

| Категория | Команды | Назначение |
|-----------|---------|------------|
| APT | `apt-get update`, `apt-get install` | Установка пакетов (Docker при первом деплое) |
| Docker Setup | `usermod`, `install`, `gpg`, `chmod`, `tee` | Настройка Docker репозитория |
| Директории | `mkdir -p`, `chown -R` | Создание директории деплоя |
| Systemctl | `systemctl enable/start/restart docker` | Управление Docker сервисом |

#### Что запрещено:

- Редактирование файлов (`nano`, `vim`, `vi`)
- Удаление файлов и директорий (`rm`, `rmdir`)
- Управление пользователями (`adduser`, `deluser`, `passwd`)
- Изменение сетевых настроек (`iptables`, `ufw`)
- Доступ к другим сервисам (`systemctl` кроме docker)
- Полный root-доступ

### Шаг 4: Генерация SSH-ключа

Создайте SSH-ключ для авторизации GitHub Actions:

```bash
# Создать директорию .ssh
mkdir -p /home/depuser/.ssh

# Сгенерировать ключ (Ed25519 — современный и безопасный)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /home/depuser/.ssh/github_deploy -N ""

# Добавить публичный ключ в authorized_keys
cat /home/depuser/.ssh/github_deploy.pub >> /home/depuser/.ssh/authorized_keys

# Убрать дубликаты
sort -u /home/depuser/.ssh/authorized_keys -o /home/depuser/.ssh/authorized_keys
```

### Шаг 5: Настройка прав на файлы

```bash
chown -R depuser:depuser /home/depuser/.ssh
chmod 700 /home/depuser/.ssh
chmod 600 /home/depuser/.ssh/authorized_keys
chmod 600 /home/depuser/.ssh/github_deploy
chmod 600 /home/depuser/.ssh/github_deploy.pub
```

### Шаг 6: Создание директории деплоя

```bash
# Для pre-production
mkdir -p /opt/blog-preprod
chown -R depuser:depuser /opt/blog-preprod

# Для production
mkdir -p /opt/blog
chown -R depuser:depuser /opt/blog
```

### Шаг 7: Скопировать приватный ключ

Выведите приватный ключ на экран:

```bash
cat /home/depuser/.ssh/github_deploy
```

Скопируйте **весь** вывод, включая строки `-----BEGIN` и `-----END`.

---

## Настройка GitHub Secrets

Перейдите в репозиторий: **Settings → Secrets and variables → Actions → New repository secret**

### Pre-Production

| Secret | Значение |
|--------|----------|
| `PREPROD_SSH_KEY` | Приватный ключ (скопированный на Шаге 7) |
| `PREPROD_SSH_USER` | `depuser` |
| `PREPROD_SERVER_IP` | IP адрес VPS |
| `PREPROD_DEPLOY_DIR` | `/opt/blog-preprod` |

### Production

| Secret | Значение |
|--------|----------|
| `SSH_KEY` | Приватный ключ для prod VPS |
| `SSH_USER` | `depuser` |
| `SERVER_IP` | IP адрес production VPS |
| `DEPLOY_DIR` | `/opt/blog` |

---

## Проверка

### Проверить подключение с локальной машины

```bash
# Скопировать приватный ключ на локальную машину
# Сохранить в ~/.ssh/depuser_key (или другой путь)

ssh -i ~/.ssh/depuser_key depuser@<IP_VPS>
```

### Проверить права docker

```bash
# Под пользователем depuser
docker ps
docker compose version
```

### Проверить ограничения sudo

```bash
# Должно работать:
sudo apt-get update

# Должно быть запрещено:
sudo rm -rf /        # ← не сработает
sudo reboot          # ← не сработает
sudo nano /etc/hosts # ← не сработает
```

---

## Безопасность

### Рекомендации

1. **Отключить вход root по SSH** (после настройки depuser):
   ```bash
   # Под root:
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
- Docker-команды выполняются через членство в группе `docker` (без sudo)
- sudo разрешён только для ограниченного набора команд, необходимых при первоначальной настройке
- После установки Docker sudo фактически не используется при обычном деплое

---

## FAQ

**Q: Что если Docker уже установлен?**
A: CI/CD проверяет наличие Docker и пропускает установку. В этом случае sudo-команды не выполняются вообще.

**Q: Можно использовать другое имя пользователя?**
A: Да, в скрипте `setup_vps.sh` можно задать: `DEPLOY_USER=myuser bash setup_vps.sh`. Не забудьте указать это имя в GitHub Secret `SSH_USER`.

**Q: Что делать при компрометации ключа?**
A: Удалите публичный ключ из `authorized_keys`, сгенерируйте новый и обновите GitHub Secret.
