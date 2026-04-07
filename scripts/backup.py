#!/usr/bin/env python3
"""
MyPet01 — скрипт резервного копирования
Запускается с VPS3 по cron ежедневно в 02:00

Стратегия 3-2-1:
  1. Оригинал — VPS1 (продакшн)
  2. Локальная копия — rsync → VPS2
  3. Offsite — boto3 → S3 (провайдер TBD)
"""

import os
import subprocess
import logging
import datetime
import boto3
from botocore.client import Config
from pathlib import Path
from dotenv import load_dotenv

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/mypet01-backup.log"),
    ],
)
log = logging.getLogger(__name__)

# --- Загрузка конфига ---
load_dotenv("/opt/scripts/backup.env")

VPS2_HOST = os.environ["VPS2_HOST"]
VPS2_BACKUP_DIR = os.environ.get("VPS2_BACKUP_DIR", "/opt/backups")
APP_DIR = os.environ.get("APP_DIR", "/opt/mypet01")

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
S3_BUCKET = os.environ.get("S3_BUCKET", "")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_RETENTION_DAYS = int(os.environ.get("S3_RETENTION_DAYS", "30"))

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

TMP_DIR = Path("/tmp/mypet01-backup")
TODAY = datetime.date.today().strftime("%Y%m%d")


def send_telegram(message: str) -> None:
    """Отправить уведомление в Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request, json
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Не удалось отправить Telegram-уведомление: {e}")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Выполнить команду с логированием."""
    log.info(f"Выполняю: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and check:
        raise RuntimeError(f"Команда завершилась с ошибкой: {result.stderr}")
    return result


def dump_postgres() -> Path:
    """Сделать дамп PostgreSQL из Docker-контейнера."""
    dump_file = TMP_DIR / f"db_{TODAY}.sql.gz"
    log.info("Создаю дамп PostgreSQL...")
    run([
        "bash", "-c",
        f"docker exec mypet01-db-1 pg_dump -U blog_user blog_db | gzip > {dump_file}"
    ])
    log.info(f"Дамп создан: {dump_file} ({dump_file.stat().st_size // 1024} KB)")
    return dump_file


def archive_volumes() -> list[Path]:
    """Архивировать важные Docker volumes."""
    archives = []
    volumes = {
        "media": f"{APP_DIR}/media",
        "certbot": "/var/lib/docker/volumes/mypet01_certbot_conf/_data",
        "softether": "/var/lib/docker/volumes/mypet01_softether_data/_data",
    }
    for name, path in volumes.items():
        if not Path(path).exists():
            log.warning(f"Директория {path} не найдена, пропускаю")
            continue
        archive = TMP_DIR / f"{name}_{TODAY}.tar.gz"
        log.info(f"Архивирую {name}...")
        run(["tar", "-czf", str(archive), "-C", str(Path(path).parent), Path(path).name])
        archives.append(archive)
        log.info(f"Архив создан: {archive} ({archive.stat().st_size // 1024} KB)")
    return archives


def rsync_to_vps2(files: list[Path]) -> None:
    """Синхронизировать бэкапы на VPS2."""
    log.info(f"Копирую на VPS2 ({VPS2_HOST})...")
    run([
        "rsync", "-avz", "--progress",
        *[str(f) for f in files],
        f"root@{VPS2_HOST}:{VPS2_BACKUP_DIR}/"
    ])
    log.info("rsync завершён успешно")


def upload_to_s3(files: list[Path]) -> None:
    """Загрузить бэкапы в S3."""
    if not S3_ENDPOINT or not S3_BUCKET or not S3_ACCESS_KEY:
        log.warning("S3 не настроен (провайдер TBD), пропускаю загрузку в S3")
        return

    log.info(f"Загружаю в S3 ({S3_ENDPOINT}, bucket: {S3_BUCKET})...")
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    for file in files:
        key = f"backups/{TODAY}/{file.name}"
        s3.upload_file(str(file), S3_BUCKET, key)
        log.info(f"Загружен: s3://{S3_BUCKET}/{key}")

    # Удалить старые бэкапы из S3
    cutoff = datetime.date.today() - datetime.timedelta(days=S3_RETENTION_DAYS)
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix="backups/"):
        for obj in page.get("Contents", []):
            obj_date_str = obj["Key"].split("/")[1]
            try:
                obj_date = datetime.datetime.strptime(obj_date_str, "%Y%m%d").date()
                if obj_date < cutoff:
                    s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
                    log.info(f"Удалён старый бэкап из S3: {obj['Key']}")
            except ValueError:
                pass


def cleanup() -> None:
    """Удалить временные файлы."""
    for f in TMP_DIR.glob("*"):
        f.unlink()
    log.info("Временные файлы удалены")


def main() -> None:
    log.info("=" * 50)
    log.info(f"Запуск бэкапа MyPet01 — {TODAY}")
    log.info("=" * 50)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    all_files: list[Path] = []

    try:
        db_dump = dump_postgres()
        all_files.append(db_dump)

        volume_archives = archive_volumes()
        all_files.extend(volume_archives)

        rsync_to_vps2(all_files)
        upload_to_s3(all_files)

        cleanup()
        msg = f"✅ Бэкап MyPet01 успешно завершён ({TODAY})\nФайлов: {len(all_files)}"
        log.info(msg)
        send_telegram(msg)

    except Exception as e:
        msg = f"❌ Ошибка бэкапа MyPet01 ({TODAY})\n{e}"
        log.error(msg)
        send_telegram(msg)
        raise


if __name__ == "__main__":
    main()
