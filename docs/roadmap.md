# MyPet01 — Roadmap инфраструктуры

> Актуальный документ с принятыми решениями по инфраструктуре и порядку реализации.
> **Сверяться с этим файлом перед началом любой инфраструктурной задачи.**
> Последнее обновление: апрель 2026

---

## 1. Принятые архитектурные решения

| Решение | Выбор | Причина |
|---------|-------|---------|
| Хостинг | VDSka (3 VPS) | Текущий провайдер, нет API → Ansible достаточно |
| Мониторинг | Prometheus + Grafana + Uptime Kuma | Netdata исключён, Prometheus — стандарт |
| Staging | Windows локально (Docker Desktop) | Отдельный VPS для staging не нужен |
| Бэкапы | rsync → VPS2 + boto3 → S3 (Selectel) | Правило 3-2-1 |
| S3 для медиа | Отдельный план (`docs/planning/S3_MIGRATION_PLAN.md`) | Пока медиа хранится локально |
| Безопасность | fail2ban + ufw + SSH-ключи | На всех 3 VPS |
| Terraform | Опционально, только в самом конце | VDSka не имеет API |
| Переезд на Selectel | Опционально, только когда всё работает | Terraform provider, оплата из РФ |

---

## 2. Что уже реализовано

| Компонент | Статус | Где |
|-----------|--------|-----|
| Django-приложение | ✅ | `mypet_project/`, `blog/`, `users/`, `core/` |
| `docker-compose.prod.yml` | ✅ | HAProxy + Nginx + Gunicorn + PG + Redis + Certbot + SoftEther VPN |
| `docker-compose.yml` | ✅ | Локальная разработка (Django + PG + Redis) |
| CI/CD | ✅ | GitHub Actions: preprod → prod |
| HAProxy (GeoIP, security) | ✅ | `haproxy/` — RIPE NCC GeoIP, rate limiting, blacklist |
| Nginx конфиги | ✅ | `nginx/` |
| `scripts/setup_vps.sh` | ✅ | Bash-скрипт настройки VPS (preprod / prod) |
| `scripts/update-geoip.sh` | ✅ | Обновление GeoIP-базы RIPE NCC |
| `scripts/cron-geoip-update.sh` | ✅ | Cron-задача обновления GeoIP |
| `scripts/init-letsencrypt.sh` | ✅ | Инициализация Let's Encrypt |
| `docs/planning/S3_MIGRATION_PLAN.md` | ✅ | План миграции медиафайлов на S3 |
| 2 VPS (preprod + prod) | ✅ | 217.147.15.220 (preprod), 91.204.75.25 (prod) |

**Что НЕ реализовано:** VPS2 (бэкапы), VPS3 (управление), Ansible-роли, backup.py, Prometheus+Grafana, fail2ban.

---

## 3. Инфраструктура (3 VPS + Windows + S3)

```
💻 Windows (локально)
   Docker Desktop — Staging / разработка
   тестирование перед деплоем на продакшн
         │
         │  деплой после проверки
         ▼
┌──────────────────────────────┐  rsync  ┌──────────────────────────────┐
│   VPS1 — Продакшн (VDSka)    │────────▶│   VPS2 — Бэкапы + Резерв     │
│   91.204.75.25               │         │   (VDSka, новый)             │
│                              │         │                              │
│  Docker Compose:             │         │  Хранение: pg_dump + media   │
│  HAProxy → Nginx → Gunicorn  │         │  Uptime Kuma (пинг VPS1)     │
│  PostgreSQL + Redis          │         │                              │
│  Certbot + SoftEther VPN     │         │  ⚡ Failover: при сбое VPS3  │
│                              │         │  берёт управление на себя    │
│  node/postgres/nginx         │         │  и восстанавливает VPS3      │
│  exporters (Prometheus)      │         └──────────────┬───────────────┘
└──────────────────────────────┘                        │
         ▲                                              │ Ansible (SSH)
         │ Ansible (SSH)                                │
         └──────────────────┬─────────────────────────-┘
                            │
               ┌────────────▼──────────────────┐
               │   VPS3 — Управление (новый)    │
               │   (VDSka)                      │
               │                                │
               │  Ansible control node          │
               │  Prometheus + Grafana          │
               │  Python backup.py              │
               │  (rsync → VPS2 + boto3 → S3)  │
               └───────────────┬────────────────┘
                               │ boto3 (S3 API)
                               ▼
               ┌───────────────────────────────┐
               │  ☁ S3 Selectel Object Storage  │
               │  pg_dump + media архив         │
               │  ротация: 30 дней             │
               │  (off-site, катастр. восст.)  │
               └───────────────────────────────┘
```

---

## 4. Влияние HAProxy / Certbot / SoftEther VPN на новые роли

### HAProxy (GeoIP + security)
- **GeoIP уже обновляется** через `scripts/update-geoip.sh` и `cron-geoip-update.sh` — Ansible-роль должна скопировать эти скрипты и настроить cron
- **Certbot уже в whitelist HAProxy** (README: "VPN и ACME без ограничений") — проблем с обновлением сертификатов нет
- **fail2ban + HAProxy:** реальный IP клиента приходит в `X-Forwarded-For`, а не напрямую. fail2ban нужно настроить читать этот заголовок из Nginx-логов, иначе забанит сам HAProxy
- **Prometheus:** HAProxy-exporter нужен для мониторинга метрик балансировщика; доступ к нему только через VPN или localhost

### Certbot (Let's Encrypt)
- Уже работает через `scripts/init-letsencrypt.sh`
- Certbot-контейнер обновляет сертификаты автоматически каждые 12 часов
- **Добавить в Grafana:** алерт на срок жизни TLS-сертификата (за 14+ дней до истечения)
- SoftEther VPN шарит сертификаты из `./nginx/ssl` — при обновлении сертификата VPN получает их автоматически

### SoftEther VPN
- Открывает дополнительный вектор атаки — включить в мониторинг (Uptime Kuma)
- fail2ban: настроить на логи SoftEther если есть авторизация через логи
- Бэкап конфига SoftEther (`softether_data` volume) — включить в `backup.py`

### Итог по Ansible-ролям
| Роль | Что учесть |
|------|------------|
| `security/` | fail2ban читает IP из Nginx-логов (`X-Forwarded-For`), не напрямую |
| `monitoring/` | Добавить HAProxy-exporter; алерт на срок TLS-сертификата |
| `backup_client/` | Бэкапить Docker volumes включая `softether_data` и `certbot_conf` |
| `management/` | Скопировать `update-geoip.sh` и настроить cron на VPS3 |

---

## 5. Стратегия бэкапов (правило 3-2-1)

| Копия | Где | Скорость восстановления | Назначение |
|-------|-----|------------------------|------------|
| Оригинал | VPS1 (продакшн) | мгновенно | рабочие данные |
| Локальная | VPS2 (rsync) | секунды | быстрый failover |
| Offsite | S3 Selectel Object Storage | минуты | катастрофное восстановление |

**Что бэкапим:** pg_dump, media volume, certbot_conf volume, softether_data volume, HAProxy configs.
**Ротация:** 7 дней на VPS2, 30 дней в S3.

**S3 для бэкапов:** Selectel Object Storage (`boto3`, эндпоинт `https://s3.selcdn.ru`)
**S3 для медиа:** отдельный план — `docs/planning/S3_MIGRATION_PLAN.md`

---

## 6. Failover VPS3 → VPS2

При сбое VPS3 (Ansible control node):
1. **VPS2** обнаруживает сбой через Uptime Kuma
2. VPS2 берёт на себя запуск Ansible-плейбука восстановления
3. Плейбук восстанавливает VPS3 из снапшота или пересоздаёт
4. После восстановления VPS3 управление возвращается обратно

---

## 7. Структура репозитория инфраструктуры

Отдельный репозиторий `mypet01-infra`:

```
mypet01-infra/
├── ansible/
│   ├── inventory.ini               # IP всех трёх серверов
│   ├── site.yml                    # Главный плейбук
│   ├── group_vars/
│   │   ├── prod.yml                # Переменные VPS1
│   │   ├── backup.yml              # Переменные VPS2
│   │   └── management.yml          # Переменные VPS3
│   └── roles/
│       ├── docker/                 # Установка Docker + Compose
│       ├── mypet01/                # Деплой приложения на VPS1
│       ├── backup_client/          # rsync → VPS2 + boto3 → S3 (с VPS1)
│       ├── backup_server/          # Приём rsync-бэкапов (VPS2)
│       ├── management/             # Ansible control node + cron GeoIP (VPS3)
│       ├── monitoring/             # Prometheus + Grafana (VPS3), exporters + HAProxy-exporter (VPS1), Uptime Kuma (VPS2)
│       └── security/               # fail2ban (X-Forwarded-For) + ufw (все VPS)
├── docker-compose.prod.yml         # ✅ Уже реализовано
├── .env.example                    # Шаблон переменных окружения
└── scripts/
    └── backup.py                   # pg_dump + volumes + rsync → VPS2 + boto3 → S3 + Telegram алерт
```

### Ansible inventory.ini

```ini
[prod]
vps1.example.com ansible_user=root   # 91.204.75.25

[backup]
vps2.example.com ansible_user=root   # новый VPS

[management]
vps3.example.com ansible_user=root   # новый VPS

[all:vars]
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

---

## 8. Порядок реализации

| # | Статус | Задача | Что входит | Оценка |
|---|--------|--------|------------|--------|
| 1 | ✅ Готово | **docker-compose.prod.yml** | HAProxy + Nginx + Gunicorn + PG + Redis + Certbot + SoftEther VPN | — |
| 2 | ✅ Готово | **CI/CD** | GitHub Actions: preprod (217.147.15.220) → prod (91.204.75.25) | — |
| 3 | ⏳ | **Провизионинг VPS2 + VPS3** | Создать новые VPS на VDSka, настроить SSH-доступ | 1 день |
| 4 | ⏳ | **Ansible-роли** | docker, mypet01, backup_client, backup_server, management, monitoring, **security** | 1–2 нед. |
| 5 | ⏳ | **Python backup.py** | pg_dump + volumes + rsync → VPS2 + boto3 → S3 + Telegram алерт + ротация | 2–3 дня |
| 6 | ⏳ | **Мониторинг** | Prometheus + Grafana + HAProxy-exporter (VPS3), Uptime Kuma (VPS2), TLS-алерт | 2–3 дня |
| 7 | ⏳ | **Failover-логика** | Скрипт на VPS2 для подхвата функций VPS3 при сбое | 2–3 дня |
| 8 | ⏭ Опционально | **S3 для медиафайлов** | Миграция media на S3 (подробно в `docs/planning/S3_MIGRATION_PLAN.md`) | — |
| 9 | ⏭ Опционально | **Terraform + Selectel** | Только если нужен полноценный IaC | — |

---

## 9. Learning Roadmap

| Приоритет | Направление | Что конкретно |
|-----------|-------------|---------------|
| 🔴 Высокий | Python-автоматизация | `boto3`, `paramiko`, `requests`, `psutil` |
| 🔴 Высокий | **Ansible** | Роли, плейбуки, Ansible Vault; плейбук деплоя mypet01 |
| 🟡 Средний | Контейнеризация | Docker Compose для продакшна, базовый Kubernetes |
| 🟡 Средний | **Мониторинг** | Prometheus + Grafana, PromQL, настройка алертов |
| 🟢 Желательно | Работа с API железа | VMware vSphere API, Redfish (IPMI), API СХД Dell/NetApp |
| ⚪ Опционально | **Terraform** | IaC для управления ВМ — только при переходе на Selectel |
