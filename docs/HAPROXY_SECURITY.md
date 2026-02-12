# Безопасность HAProxy

Документация по настройке и управлению безопасностью HAProxy на продакшн-сервере.

## Содержание

- [Архитектура защиты](#архитектура-защиты)
- [Ручной чёрный список IP](#ручной-чёрный-список-ip)
- [GeoIP фильтрация](#geoip-фильтрация)
- [Rate Limiting](#rate-limiting)
- [Блокировка сканеров](#блокировка-сканеров)
- [Автоматический бан (BADREQ)](#автоматический-бан-badreq)
- [VPN (SoftEther)](#vpn-softether)
- [ACME / Let's Encrypt](#acme--lets-encrypt)
- [ICMP блокировка](#icmp-блокировка)
- [Порядок проверок](#порядок-проверок)
- [Команды управления](#команды-управления)

---

## Архитектура защиты

HAProxy — единая точка входа для всего трафика. Четыре фронтенда:

| Фронтенд | Порт | Протокол | Назначение |
|---|---|---|---|
| `ft_ssl` | 443 | TCP (SNI) | HTTPS — сайт и VPN |
| `ft_http` | 80 | HTTP | Редирект на HTTPS + ACME |
| `ft_minecraft` | 25565 | TCP | Minecraft сервер |
| `ft_minecraft_rcon` | 25575 | TCP | Minecraft RCON |

---

## Ручной чёрный список IP

**Файл:** `haproxy/blacklist/blocked_ips.lst`

Ручной список IP-адресов сканеров и агрессивных краулеров. Проверяется **первым** во всех фронтендах, до rate limiting и гео-фильтрации.

### Как добавить IP в чёрный список

1. Открыть файл `haproxy/blacklist/blocked_ips.lst`
2. Добавить IP-адрес (один на строку), можно с комментарием:
   ```
   # Сканер — обнаружен 2026-02-12
   1.2.3.4
   ```
3. Перезагрузить HAProxy **без даунтайма**:
   ```bash
   docker compose -f docker-compose.prod.yml kill -s HUP haproxy
   ```

### Формат файла

```
# Комментарии начинаются с #
# Один IP или CIDR на строку
45.135.193.11
87.120.191.67/32
10.0.0.0/8
```

### Важно

- ACME-запросы (Let's Encrypt) **не блокируются** даже если IP в чёрном списке (только в `ft_http`)
- В `ft_ssl`, `ft_minecraft`, `ft_minecraft_rcon` — блокировка безусловная
- Файл монтируется в контейнер как read-only: `./haproxy/blacklist:/usr/local/etc/haproxy/blacklist:ro`

---

## GeoIP фильтрация

Доступ к сайту и Minecraft — **только с российских IP**.

**Файл:** `haproxy/geoip/ru_networks.lst`

### Источник данных

RIPE NCC delegated stats (не требуется API-ключ MaxMind).

### Генерация списка

```bash
bash scripts/update-geoip.sh
```

### Автообновление (cron)

```bash
0 3 * * 0 /path/to/scripts/cron-geoip-update.sh
```

Обновляет список каждое воскресенье в 3:00.

### Что фильтруется

| Фронтенд | Гео-фильтр |
|---|---|
| `ft_ssl` (сайт) | Только российские IP |
| `ft_ssl` (VPN) | **Без ограничений** — VPN доступен из любой страны |
| `ft_http` | Только российские IP (ACME без ограничений) |
| `ft_minecraft` | Только российские IP |
| `ft_minecraft_rcon` | Только российские IP |

### VPN SNI (без гео-ограничений)

Два домена для VPN (оба пропускаются без проверки страны):
- `vpn.mine-craft.su` — препрод
- `mainsrv01.mine-craft.su` — прод

### Первый деплой

Перед первым запуском HAProxy необходимо сгенерировать GeoIP данные:

```bash
bash scripts/update-geoip.sh
```

---

## Rate Limiting

Реализовано через stick-tables HAProxy.

### Лимиты

| Фронтенд | Лимит | Действие |
|---|---|---|
| `ft_ssl` | 30 соединений/10 сек | reject |
| `ft_ssl` | 20 одновременных соединений | reject |
| `ft_http` | 50 запросов/10 сек | deny 429 |
| `ft_minecraft` | 10 соединений/10 сек | reject |
| `ft_minecraft_rcon` | 5 соединений/10 сек | reject |

### Stick-tables

```
st_tcp_rates:  expire 5m,  хранит conn_rate(10s), conn_cur, gpc0
st_http_rates: expire 30m, хранит http_req_rate(10s), http_err_rate(10s), gpc0, conn_rate(10s)
```

---

## Блокировка сканеров

В `ft_http` блокируются типичные пути сканеров (403 + автобан):

- `/SDK/webLanguage`, `/hudson`, `/wp-admin`, `/wp-login`, `/wp-content`
- `/xmlrpc.php`, `/phpmyadmin`, `/pma`, `/.env`, `/.git`
- `/vendor`, `/telescope`, `/jenkins`, `/actuator`, `/admin`
- `/cgi-bin`, `/solr`, `/manager`, `/jmx-console`, `/invoker`
- `/remote/fgt_lang`, `/boaform`, `/HNAP1`, `/config`, `/api/v1/pods`

При попадании на эти пути IP получает метку `gpc0` и блокируется на 30 минут.

---

## Автоматический бан (BADREQ)

IP-адреса с высокой частотой ошибок (>5 ошибок/10 сек, включая 400 от некорректных запросов) автоматически получают метку `gpc0` и блокируются на 30 минут.

Механизм:
1. HAProxy считает `http_err_rate` в stick-table `st_http_rates`
2. Если >5 ошибок за 10 сек — инкремент `gpc0`
3. Все последующие запросы от этого IP — 403
4. Через 30 минут (expire stick-table) бан снимается

---

## VPN (SoftEther)

### Docker volumes

```
softether_data:/mnt           — конфигурация (vpn_server.config)
softether_logs:/usr/local/bin/server_log — логи
```

### Бэкап конфигурации

```bash
docker cp <container_id>:/mnt/vpn_server.config ./backup/
```

---

## ACME / Let's Encrypt

ACME-запросы (`/.well-known/acme-challenge/`) **всегда пропускаются** без каких-либо ограничений:

- Без гео-фильтрации (Let's Encrypt валидирует с разных стран)
- Без rate limiting
- Без проверки чёрного списка
- Без проверки автобана

Роутинг: `ft_http` → `bk_certbot` (127.0.0.1:8080)

---

## ICMP блокировка

Сервер **не отвечает на ping**:

```
net.ipv4.icmp_echo_ignore_all = 1
```

Настраивается в `scripts/setup_vps.sh` и применяется в `/etc/sysctl.conf`.

**Важно:** мониторинг через ICMP (ping) не будет работать. Используйте TCP health checks.

---

## Порядок проверок

### ft_ssl (443)

1. Чёрный список IP → reject
2. Rate limiting (conn_rate, conn_cur) → reject
3. SNI detection
4. VPN SNI → bk_vpn (без гео-фильтра)
5. Гео-фильтр (только российские IP для сайта) → reject
6. Роутинг на бэкенд

### ft_http (80)

1. Определение ACME
2. Чёрный список IP (кроме ACME) → deny 403
3. Rate limiting tracking (кроме ACME)
4. Гео-фильтр (кроме ACME) → deny 403
5. Автобан gpc0 (кроме ACME) → deny 403
6. BADREQ автобан (кроме ACME) → deny 403
7. Rate limiting запросов (кроме ACME) → deny 429
8. Блокировка scanner paths (кроме ACME) → deny 403 + автобан
9. Роутинг: ACME → bk_certbot, остальное → bk_http_redirect (301 на HTTPS)

### ft_minecraft (25565) / ft_minecraft_rcon (25575)

1. Чёрный список IP → reject
2. Rate limiting → reject
3. Гео-фильтр → reject
4. Роутинг на бэкенд

---

## Команды управления

### Перезагрузка HAProxy (без даунтайма)

```bash
docker compose -f docker-compose.prod.yml kill -s HUP haproxy
```

### Полный перезапуск HAProxy

```bash
docker compose -f docker-compose.prod.yml restart haproxy
```

### Просмотр логов HAProxy

```bash
docker compose -f docker-compose.prod.yml logs -f haproxy
```

### Обновление GeoIP данных

```bash
bash scripts/update-geoip.sh
docker compose -f docker-compose.prod.yml kill -s HUP haproxy
```

### Анализ логов — поиск сканеров

```bash
docker compose -f docker-compose.prod.yml logs haproxy | grep -oP '^\S+' | sort | uniq -c | sort -rn | head -20
```

### Статистика HAProxy (только локально)

```
http://127.0.0.1:8404/stats
```
