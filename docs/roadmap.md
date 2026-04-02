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
| Безопасность | fail2ban + ufw + SSH-ключи | На всех 3 VPS |
| Terraform | Опционально, только в самом конце | VDSka не имеет API |
| Переезд на Selectel | Опционально, только когда всё работает | Terraform provider, оплата из РФ |

---

## 2. Инфраструктура (3 VPS + Windows + S3)

```
💻 Windows (локально)
   Docker Desktop — Staging / разработка
   тестирование перед деплоем на продакшн
         │
         │  деплой после проверки
         ▼
┌─────────────────────────┐   rsync    ┌──────────────────────────────┐
│   VPS1 — Продакшн       │───────────▶│   VPS2 — Бэкапы + Резерв     │
│   (VDSka)               │            │   (VDSka)                    │
│                         │            │                              │
│  Docker Compose:        │            │  Хранение: pg_dump + media   │
│  Django + PostgreSQL    │            │  Uptime Kuma (пинг VPS1)     │
│  + Redis + Nginx        │            │                              │
│                         │            │  ⚡ Failover: при сбое VPS3  │
│  node_exporter          │            │  берёт управление на себя    │
│  postgres_exporter      │            │  и восстанавливает VPS3      │
│  nginx_exporter         │            └──────────────┬───────────────┘
└─────────────────────────┘                           │
         ▲                                            │ Ansible (SSH)
         │ Ansible (SSH)                              │
         └──────────────────┬─────────────────────────┘
                            │
               ┌────────────▼──────────────────┐
               │   VPS3 — Управление            │
               │   (VDSka)                      │
               │                                │
               │  Ansible control node          │
               │  Prometheus + Grafana          │
               │  Python backup.py              │
               │  (backup.py → rsync + S3)      │
               │                                │
               │  ⚠ При сбое VPS3:              │
               │  VPS2 подхватывает функции     │
               │  и восстанавливает VPS3        │
               └───────────────┬────────────────┘
                               │
                               │ boto3 (S3 API)
                               ▼
               ┌───────────────────────────────┐
               │  ☁ S3 Selectel Object Storage  │
               │  pg_dump + media архив        │
               │  ротация: 30 дней             │
               │  (off-site, катастр. восст.)  │
               └───────────────────────────────┘
```

---

## 3. Технологический стек

### Приложение (VPS1)
| Компонент | Технология |
|-----------|-----------|
| Backend | Django 6.0 + Gunicorn |
| База данных | PostgreSQL |
| Кэш | Redis |
| Reverse proxy + Static | Nginx |
| Контейнеризация | Docker Compose |

### Мониторинг (VPS3)
| Компонент | Назначение |
|-----------|-----------|
| Prometheus | Сбор метрик со всех VPS |
| Grafana | Дашборды + алерты (Telegram / email) |
| node_exporter | CPU, RAM, диск — на каждом VPS |
| postgres_exporter | Метрики PostgreSQL — на VPS1 |
| nginx_exporter | Метрики Nginx — на VPS1 |
| Uptime Kuma | Пинг VPS1 каждые 30 сек, запуск failover — на VPS2 |

### Безопасность (все VPS)
| Инструмент | Роль |
|-----------|------|
| fail2ban | Блокировка IP при брутфорсе SSH и Nginx |
| ufw / iptables | Фаервол: открыты только порты 22, 80, 443 |
| SSH-ключи | Вход только по ключу, пароли отключены |

### DevOps Pipeline
| Инструмент | Роль |
|-----------|------|
| Ansible | Настройка всех VPS изнутри (с VPS3 по SSH) |
| Docker Compose | Оркестрация контейнеров на VPS1 |
| Python backup.py | Автоматизация бэкапов: rsync + S3 + Telegram |
| Terraform | Опционально — только при переходе на Selectel |

---

## 4. Стратегия бэкапов (правило 3-2-1)

| Копия | Где | Скорость восстановления | Назначение |
|-------|-----|------------------------|------------|
| Оригинал | VPS1 (продакшн) | мгновенно | рабочие данные |
| Локальная | VPS2 (rsync) | секунды | быстрый failover |
| Offsite | S3 Selectel Object Storage | минуты | катастрофное восстановление |

**Ротация:** 7 дней на VPS2, 30 дней в S3.

**S3 провайдер:** Selectel Object Storage
- S3-совместимый API (`boto3` без изменений)
- Оплата в рублях / картой РФ / СБП
- Эндпоинт: `https://s3.selcdn.ru`
- Логично: если переезжаем на Selectel VPS, S3 уже там

**Альтернатива:** Yandex Object Storage — тоже S3-совместим, оплата из РФ.

---

## 5. Failover VPS3 → VPS2

При сбое VPS3 (Ansible control node):
1. **VPS2** обнаруживает сбой через Uptime Kuma
2. VPS2 берёт на себя запуск Ansible-плейбука восстановления
3. Плейбук восстанавливает VPS3 из снапшота или пересоздаёт
4. После восстановления VPS3 управление возвращается обратно

---

## 6. Структура репозитория инфраструктуры

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
│       ├── backup_client/          # Отправка бэкапов (VPS1 → VPS2 + S3)
│       ├── backup_server/          # Приём бэкапов (VPS2)
│       ├── management/             # Настройка VPS3 (Ansible, Python-скрипты)
│       ├── monitoring/             # Prometheus + Grafana (VPS3), exporters (все VPS), Uptime Kuma (VPS2)
│       └── security/               # fail2ban + ufw (все VPS)
├── docker-compose.prod.yml         # Продакшн-конфиг контейнеров
├── .env.example                    # Шаблон переменных окружения
└── scripts/
    └── backup.py                   # pg_dump + rsync → VPS2 + boto3 → S3 + Telegram алерт
```

### Ansible inventory.ini

```ini
[prod]
vps1.example.com ansible_user=root

[backup]
vps2.example.com ansible_user=root

[management]
vps3.example.com ansible_user=root

[all:vars]
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

---

## 7. Порядок реализации

| # | Задача | Что входит | Оценка |
|---|--------|------------|--------|
| 1 | **docker-compose.prod.yml** | Nginx + Gunicorn + PG + Redis + .env секреты | 2–3 дня |
| 2 | **Ansible-роли** | docker, mypet01, backup_client, backup_server, management, monitoring, **security** | 1–2 нед. |
| 3 | **Python backup.py** | pg_dump + rsync → VPS2 + boto3 → S3 + Telegram алерт + ротация | 2–3 дня |
| 4 | **Мониторинг** | Prometheus + Grafana на VPS3, exporters на всех VPS, Uptime Kuma на VPS2 | 2–3 дня |
| 5 | **Failover-логика** | Скрипт на VPS2 для подхвата функций VPS3 при сбое | 2–3 дня |
| 6 | **Terraform + Selectel** | Опционально — только если нужен полноценный IaC | — |

---

## 8. Что изучать (Learning Roadmap)

| Приоритет | Направление | Что конкретно |
|-----------|-------------|---------------|
| 🔴 Высокий | Python-автоматизация | `boto3`, `paramiko`, `requests`, `psutil` |
| 🔴 Высокий | **Ansible** | Роли, плейбуки, Ansible Vault; плейбук деплоя mypet01 |
| 🟡 Средний | Контейнеризация | Docker Compose для продакшна, базовый Kubernetes |
| 🟡 Средний | **Мониторинг** | Prometheus + Grafana, PromQL, настройка алертов |
| 🟢 Желательно | Работа с API железа | VMware vSphere API, Redfish (IPMI), API СХД Dell/NetApp |
| ⚪ Опционально | **Terraform** | IaC для управления ВМ — только при переходе на Selectel |
