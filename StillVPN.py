"""STILL VPN v10 — единый файл: Telegram Bot + админка в боте и Mini App + API + WireGuard-agent.

РЕБРЕНДИНГ: видимое имя — Still VPN. Старые подарочные коды остаются действительными. Внутренние SHADE_MODE, X-Shade-*,
платёжный payload shade: и путь /app/data/shade.db сохранены для совместимости
с уже созданными данными, счетами и VPN-агентом.

Python 3.11+. Файл развёртывается ДВАЖДЫ, с разными режимами:
    SHADE_MODE=app    — BotHost: Aiogram 3 polling + FastAPI Mini App + SQLite в /app/data.
    SHADE_MODE=agent  — VPS с WireGuard, отдельный HTTPS-домен через Caddy.

УСТАНОВКА:
    pip install "aiogram>=3.13,<4" "fastapi>=0.115,<1" "uvicorn>=0.30,<1" \
      "sqlalchemy[asyncio]>=2.0,<3" "aiosqlite>=0.20,<1" "httpx>=0.27,<1" \
      "cryptography>=43,<47" "pydantic>=2.8,<3" "psutil>=5.9,<8"

НА BOTHost (переменные окружения, не код!):
    SHADE_MODE=app
    BOT_TOKEN=<BotFather токен; BotHost может передать автоматически>
    WEBAPP_URL=https://<домен-из-панели-BotHost>
    DATA_DIR=/app/data  # необязательно: по умолчанию на BotHost /app/data
    DATABASE_PATH=/app/data/shade.db  # необязательно: создаётся автоматически
    # DATABASE_URL=postgresql+asyncpg://...  # только при переходе на внешний PostgreSQL
    OWNER_IDS=<ваш числовой Telegram ID>
    CODE_PEPPER=<32+ случайных ASCII символов>
    GIFT_FERNET_KEY=<python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
    WG_AGENT_SECRET=<32+ символов, одинаковый на BotHost и первом VPS>
    WG_AGENT_SECRETS='{"2":"отдельный_секрет_для_VPS_2"}'  # только при двух и более узлах
    WG_AGENT_URL=https://wg.example.org
    WG_SERVER_ENDPOINT=<IP-VPS>:51820
    WG_SERVER_PUBLIC_KEY=<публичный WireGuard ключ сервера>
    WG_SERVER_CIDR=10.13.0.0/24
    PORT=<порт домена из BotHost, обычно 8000>
    ENABLE_PAYMENTS=0 (включить только после проверки работающего VPN)
    TERMS_URL=https://<реальная опубликованная страница условий>
    SUPPORT_CONTACT=@support_username

НА VPS:
    apt install wireguard wireguard-tools python3 python3-venv caddy postgresql-client
    Конфигурация /etc/wireguard/wg0.conf должна содержать уникальный PrivateKey,
    Address=10.13.0.1/24, ListenPort=51820, NAT + forwarding для интернета.
    systemctl enable --now wg-quick@wg0
    ufw allow 51820/udp
    Виртуальное окружение, то же shade.py, запуск под учёткой, имеющей доступ к wg:
    SHADE_MODE=agent WG_INTERFACE=wg0 WG_AGENT_SECRET=<...> PORT=8080 python shade.py
    Caddyfile: wg.example.org { reverse_proxy 127.0.0.1:8080 }
    НЕ открывайте порт 8080 в Интернет. Разрешите на VPS TCP/443 + UDP/51820.
    Агент не получает BOT_TOKEN, DATABASE_URL, приватные ключи пользователей.
    Начиная с v4 агент сохраняет временные разрешения WireGuard в
    /etc/stillvpn/peer_leases.json (root, chmod 600), проверяет их каждые 15 с.
    При недоступности BotHost разрешение истечёт через <= 5 минут.
    Для работы срока действия агент и BotHost должны быть обновлены до v4.
    Первое обновление агента удалит устаревшие Peer без lease: BotHost восстановит
    доступ действующим подписчикам после своей очередной синхронизации.

BotFather: /newbot; /setmenubutton -> URL WEBAPP_URL. В BotHost: главный файл
StillVPN.py, Python, порт из PORT, свой HTTPS-поддомен, один экземпляр приложения.
BotHost использует Python-зависимости из интерфейса или requirements.txt
(можно сгенерировать: python shade.py generate DIR).

Первый запуск: /start, /admin; создать тариф /adm_plan 30 100 2 0 Месяц.
Дополнительные команды /admin -> «Команды управления».
Сервис считает покупку подтверждённой ТОЛЬКО при successful_payment Telegram.

STILL VPN WEB v8 (на BotHost, без Telegram):
    Адрес: https://<домен-WEBAPP_URL>/web — один FastAPI процесс, одна SQLite.
    WEB_REGISTRATION_ENABLED=1  # самостоятельная регистрация логин/пароль (по умолчанию).
    BOT_USERNAME=<username без @>  # необязательно: бот попробует получить через Bot API.
    WEB_TRIAL_ENABLED=0  # по умолчанию, чтобы нельзя было массово создавать пробники.
    Для включения веб-пробника требуются SMTP_HOST, SMTP_PORT, SMTP_USER,
    SMTP_PASSWORD, SMTP_FROM, WEB_TRIAL_ENABLED=1 и подтверждённый email.
    Вход через HttpOnly+Secure cookie, CSRF-токен, scrypt-hash. Одноразовый код
    восстановления показывается при регистрации. /linkweb в Telegram создаёт
    код привязки к существующему Telegram-аккаунту (до первого использования VPN).
    На сайте пока НЕТ оплаты: Telegram Stars остаются только в Telegram.
    Без отдельного платёжного провайдера сайт не может принимать платные платежи.
    Требуется тестирование российских сетей без VPN и юридические документы.

v8 (сохранена функция v7): /api/admin/users/{id}/trial/shorten доступен только Owner, требует причину,
    не продлевает срок, записывает Audit Log и синхронизирует доступ с агентом.
    В админке пользователя действия «До 5 минут» и «Завершить сейчас».
    Экспорт .conf: файл можно получить в личном Telegram-чате по явному согласию
    или сохранить локально. При отправке в Telegram ключ кратковременно передаётся
    через HTTPS на BotHost и далее в Telegram, но в SQLite и журналах не хранится.
    Экспорт .conf: сначала локальное системное сохранение/передача файла,
    затем обычная загрузка/копирование. Telegram WebView может запрещать
    загрузку blob:-URL: полноценная гарантия скачивания невозможна без
    платформенной поддержки. При локальном экспорте ключ остаётся в браузере;
    при явной отправке в Telegram он передаётся транзитом по HTTPS и не пишется в БД.

v8 — дизайн: новый редакционный сайт и Mini App, экраны «Наш сервер», «Поделиться», канал
https://t.me/StillVPN_official (подписка не обязательна). /adm_start_photo — ответом
на загруженное в бот фото, /adm_start_photo_off — удалить. /adm_log_test — проверить группу. /invite — ссылка.
Логи регистраций, первых подключений, устройств, покупок, поддержки и действий админа
в LOG_CHAT_ID=-1004452182801: добавить бота в закрытую группу с разрешением писать.
Telegram ID, имя, фамилия и @username сохраняются, ключи/пароли в логи не попадают.
/api/servers/public — публичная информация о сервере. PUBLIC_SERVER_COUNTRY=Нидерланды,
PUBLIC_SERVER_PROVIDER=SKRIME. /build отдаёт релиз 10.0.0.
Рефералы: только учёт приглашений, без автоматических бонусов за регистрацию.

MINI APP АДМИНКА v8: кнопка «Админ» появляется только у OWNER_IDS или сотрудника
из таблицы admins. Backend повторно проверяет права каждой операции. Старую SQLite
базу не удалять. Обновлять до v10 только BotHost; VPN-агент v4 на VPS остаётся совместимым.

ВСПОМОГАТЕЛЬНЫЕ КОМАНДЫ:
    python shade.py selftest                  — автономные тесты криптографических проверок
    python shade.py dbtest                    — проверка подключения, миграций и транзакций БД
    python shade.py verify                    — проверка реального Telegram/БД/VPS (без записи)
    python shade.py generate ./deployment     — примеры .env, compose, requirements, Caddy
    python shade.py backup /app/data/backups   — онлайн-бэкап SQLite (для PostgreSQL pg_dump)
    python shade.py restore FILE.sqlite --confirm-restore  — только при остановленном боте

ВАЖНО: код — расширенная однофайловая реализация, не подтверждённый production.
Интеграционные испытания BotHost, Telegram Stars, VPS, живой SQLite и
failover и восстановления бэкапа необходимы до включения платежей.
Полноценный Alembic заменён встроенными идемпотентными SQL-миграциями.
SQLite поддерживает только ОДИН экземпляр приложения и не подходит для
горизонтального масштабирования; резервные копии /app/data обязательны.
Многоузловая эксплуатация: для узлов 2+ настройте в окружении BotHost
WG_AGENT_SECRETS JSON с ключами ID сервера и разными секретами; на каждом VPS
установите собственный WG_AGENT_SECRET. Для дальнейшего роста перейти на PostgreSQL, выделить отдельный
воркер очередей и централизованный rate limit. Нельзя запускать несколько
экземпляров polling одновременно. Протокол WireGuard сам по себе не гарантирует
обход блокировок. Доступен только IPv4; IPv6 не маршрутизируется.

Спецификации: https://core.telegram.org/bots/payments-stars
https://core.telegram.org/bots/webapps  https://bothost.ru/docs/domains-and-ports
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import sys
import shutil
import pathlib
import argparse
import secrets
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl, urlparse, unquote, quote

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

LOG = logging.getLogger("shade")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

MODE = os.getenv("SHADE_MODE", "app")
if MODE not in ("app", "agent"):
    raise RuntimeError("SHADE_MODE должен быть app или agent")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "/app/data")).expanduser()
DATABASE_PATH = pathlib.Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "shade.db"))).expanduser()
BOT_META_STATE_PATH = DATA_DIR / "bot_profile_state.json"
if MODE == "app" and not DATABASE_URL:
    # Bothost mounts /app/data as a persistent volume. Never keep the DB in /app root.
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    DATABASE_PATH = DATABASE_PATH.resolve()
    DATABASE_URL = "sqlite+aiosqlite:///" + str(DATABASE_PATH)
DATABASE_IS_SQLITE = DATABASE_URL.startswith("sqlite+aiosqlite:///")
if DATABASE_IS_SQLITE:
    # Explicit sqlite+aiosqlite URL may override DATABASE_PATH.
    DATABASE_PATH = pathlib.Path(DATABASE_URL.removeprefix("sqlite+aiosqlite:///"))
    if not DATABASE_PATH.is_absolute():
        raise RuntimeError("SQLite DATABASE_PATH должен быть абсолютным")
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)  # Restrict -wal/-shm and new database files to the bot user.
    DATABASE_PATH.touch(mode=0o600, exist_ok=True)
    DATABASE_PATH.chmod(0o600)

OWNER_IDS = {int(x.strip()) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()}
CODE_PEPPER = os.getenv("CODE_PEPPER", "")
GIFT_FERNET_KEY = os.getenv("GIFT_FERNET_KEY", "")
WG_AGENT_SECRET = os.getenv("WG_AGENT_SECRET", "")
# For several nodes set on BotHost: WG_AGENT_SECRETS='{"2":"node2-unique-32+ secret", ...}'
# Node 1 may use WG_AGENT_SECRET; agents each read only their own WG_AGENT_SECRET.
try:
    WG_AGENT_SECRETS = json.loads(os.getenv("WG_AGENT_SECRETS", "{}"))
    if not isinstance(WG_AGENT_SECRETS, dict):
        raise ValueError("WG_AGENT_SECRETS must be an object")
except (json.JSONDecodeError, ValueError) as exc:
    raise RuntimeError("WG_AGENT_SECRETS must be a JSON object") from exc
WG_AGENT_URL = os.getenv("WG_AGENT_URL", "").rstrip("/")
WG_SERVER_ENDPOINT = os.getenv("WG_SERVER_ENDPOINT", "")
WG_SERVER_PUBLIC_KEY = os.getenv("WG_SERVER_PUBLIC_KEY", "")
WG_SERVER_CIDR = os.getenv("WG_SERVER_CIDR", "10.13.0.0/24")
WG_SERVER_LOCATION = os.getenv("WG_SERVER_LOCATION", "Primary")
RELEASE = "11.0.0"
CHANNEL_URL = "https://t.me/StillVPN_official"
PUBLIC_SERVER_COUNTRY = os.getenv("PUBLIC_SERVER_COUNTRY", "Нидерланды")[:64]
PUBLIC_SERVER_PROVIDER = os.getenv("PUBLIC_SERVER_PROVIDER", "SKRIME")[:64]
try:
    LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "-1004452182801"))
except ValueError:
    raise RuntimeError("LOG_CHAT_ID должен быть числовым Telegram chat id")
WG_INTERFACE = os.getenv("WG_INTERFACE", "wg0")
ENABLE_PAYMENTS = os.getenv("ENABLE_PAYMENTS", "0") == "1"
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@support")
TERMS_URL = os.getenv("TERMS_URL", "")
WG_PEER_LEASE_SECONDS = min(900, max(120, int(os.getenv("WG_PEER_LEASE_SECONDS", "300"))))
WG_AGENT_LEASE_PATH = pathlib.Path(os.getenv("WG_AGENT_LEASE_PATH", "/etc/stillvpn/peer_leases.json"))
UTC = timezone.utc

def now() -> datetime:
    return datetime.now(UTC)

def bad(status: int, message: str) -> None:
    raise HTTPException(status, message)

def code_hash(code: str) -> str:
    return hmac.new(CODE_PEPPER.encode(), code.upper().encode(), hashlib.sha256).hexdigest()

def validate_wg_key(key: str) -> bool:
    try:
        b = base64.b64decode(key, validate=True)
        return len(b) == 32 and base64.b64encode(b).decode() == key
    except Exception:
        return False

def validate_init_data(raw: str, max_age: int = 86400) -> dict:
    if not raw or len(raw) > 12000:
        bad(401, "Нет авторизации Telegram. Откройте приложение через бота.")
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        bad(401, "Некорректные данные Telegram")
    data = dict(pairs)
    if len(pairs) != len(data) or not data.get("hash"):
        bad(401, "Некорректные данные Telegram")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs) if k != "hash")
    key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, data["hash"]):
        bad(401, "Неверная подпись Telegram")
    try:
        auth_ts = int(data["auth_date"])
        person = json.loads(data["user"])
        if type(person.get("id")) is not int or person["id"] <= 0:
            raise ValueError("user.id")
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        bad(401, "Некорректные данные авторизации")
    if not 0 <= time.time() - auth_ts <= max_age:
        bad(401, "Сессия Telegram устарела. Закройте и откройте Mini App.")
    return person

# Management commands are available without starting the bot or the VPN agent.
# Source remains a SINGLE .py file; auxiliary deployment files are optional generated artifacts.
REQUIREMENTS = """aiogram>=3.13,<4
fastapi>=0.115,<1
uvicorn>=0.30,<1
sqlalchemy[asyncio]>=2.0,<3
aiosqlite>=0.20,<1
# To use external PostgreSQL instead of BotHost App Data, install asyncpg separately.
httpx>=0.27,<1
cryptography>=43,<47
pydantic>=2.8,<3
psutil>=5.9,<8
"""

def command_generate(directory: str):
    """Create optional templates. Real credentials are NEVER generated or embedded."""
    path = pathlib.Path(directory).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    files = {
        "requirements.txt": REQUIREMENTS,
        ".env.example": """# BotHost: these are environment variables in Bothost UI (do NOT upload a filled .env)
SHADE_MODE=app
BOT_TOKEN=PASTE_BOTFATHER_TOKEN
WEBAPP_URL=https://YOUR-NAME.bothost.ru
# SQLite in permanent Bothost App Data: no DB URL/host/password needed.
DATA_DIR=/app/data
DATABASE_PATH=/app/data/shade.db
# DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/shade?ssl=require
OWNER_IDS=YOUR_TELEGRAM_NUMERIC_ID
CODE_PEPPER=GENERATE_32_PLUS_RANDOM_CHARACTERS
GIFT_FERNET_KEY=GENERATE_FERNET_KEY
WG_AGENT_SECRET=GENERATE_32_PLUS_RANDOM_CHARACTERS
# WG_AGENT_SECRETS={"2":"A_UNIQUE_RANDOM_SECRET_FOR_NODE2"}  # only if multi-node
WG_AGENT_URL=https://wg.example.org
WG_SERVER_ENDPOINT=VPS_PUBLIC_IP:51820
WG_SERVER_PUBLIC_KEY=WIREGUARD_SERVER_PUBLIC_KEY
WG_SERVER_CIDR=10.13.0.0/24
WG_SERVER_LOCATION=Main
PORT=8000
ENABLE_PAYMENTS=0
SUPPORT_CONTACT=@support
TERMS_URL=https://example.org/terms
BOT_USERNAME=YOUR_BOT_USERNAME_WITHOUT_AT
WEB_REGISTRATION_ENABLED=1
WEB_TRIAL_ENABLED=0
# To enable verified-email trials: SMTP_HOST, SMTP_PORT=587, SMTP_USER,
# SMTP_PASSWORD, SMTP_FROM and WEB_TRIAL_ENABLED=1.
# Never put SMTP credentials into code or public GitHub.
# VPS agent ONLY: SHADE_MODE=agent WG_INTERFACE=wg0 PORT=8080 AGENT_BIND=127.0.0.1
""",
        "Caddyfile.agent.example": """# Replace wg.example.org with your own agent domain and configure its A/AAAA DNS.
wg.example.org {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8080
}
""",
        "shade-agent.service.example": """# Copy to /etc/systemd/system/shade-agent.service after creating
# /opt/shade/venv, /opt/shade/shade.py, /etc/shade/agent.env
# Only WG_AGENT_SECRET, WG_INTERFACE, PORT, SHADE_MODE are required by agent.
[Unit]
Description=Still VPN WireGuard Agent
After=network-online.target wg-quick@wg0.service
Wants=network-online.target
[Service]
Type=simple
User=root
EnvironmentFile=/etc/shade/agent.env
WorkingDirectory=/opt/shade
ExecStart=/opt/shade/venv/bin/python /opt/shade/shade.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
CapabilityBoundingSet=CAP_NET_ADMIN
AmbientCapabilities=CAP_NET_ADMIN
[Install]
WantedBy=multi-user.target
""",
        "docker-compose.yml": """# OPTIONAL: self-host the same one-file app with SQLite on your own VPS.
# This example is NOT required by BotHost. Reverse-proxy port 8000 through HTTPS.
# On BotHost, data is already persisted at /app/data; no Docker Compose needed.
services:
  shade:
    image: python:3.12-slim
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./shade.py:/app/shade.py:ro
      - ./requirements.txt:/app/requirements.txt:ro
      - shade_data:/app/data
    command: sh -c 'pip install --no-cache-dir -r requirements.txt && python shade.py'
    environment:
      SHADE_MODE: app
      DATABASE_PATH: /app/data/shade.db
      BOT_TOKEN: ${BOT_TOKEN}
      WEBAPP_URL: ${WEBAPP_URL}
      OWNER_IDS: ${OWNER_IDS}
      CODE_PEPPER: ${CODE_PEPPER}
      GIFT_FERNET_KEY: ${GIFT_FERNET_KEY}
      WG_AGENT_SECRET: ${WG_AGENT_SECRET}
      WG_AGENT_URL: ${WG_AGENT_URL}
      WG_SERVER_ENDPOINT: ${WG_SERVER_ENDPOINT}
      WG_SERVER_PUBLIC_KEY: ${WG_SERVER_PUBLIC_KEY}
      WG_SERVER_CIDR: ${WG_SERVER_CIDR:-10.13.0.0/24}
      TERMS_URL: ${TERMS_URL}
      ENABLE_PAYMENTS: ${ENABLE_PAYMENTS:-0}
      PORT: 8000
    ports: ["127.0.0.1:8000:8000"]
volumes:
  shade_data:
""",
        "README.md": """# STILL VPN v3: подключение к Bothost App Data

### Что нужно

- Telegram-бот (токен BotFather) и числовой Telegram ID владельца.
- Аккаунт Bothost с Python, HTTPS-поддоменом и встроенным App Data.
- Отдельный VPS с WireGuard для VPN-трафика (BotHost VPN-туннель НЕ заменяет).
- Для работы VPN-агента — HTTPS-домен и общие секреты для запросов.

### Настройка BotHost

1. В BotHost загрузите shade.py и requirements.txt (второй файл можно
   сгенерировать командой `python shade.py generate ./deploy`).
2. Укажите главный файл shade.py, Python, один экземпляр бота, требуемые
   зависимости. Порт веб-сервиса PORT должен совпасть с опубликованным в BotHost.
3. Пропишите переменные окружения согласно .env.example (никому не отправляйте
   секреты): BOT_TOKEN, WEBAPP_URL, OWNER_IDS, CODE_PEPPER, GIFT_FERNET_KEY,
   WG_AGENT_SECRET, WG_AGENT_URL, WG_SERVER_ENDPOINT, WG_SERVER_PUBLIC_KEY,
   TERMS_URL. По умолчанию ENABLE_PAYMENTS=0.
4. Для SQLite используется `/app/data/shade.db` по умолчанию. Можно явно задать
   DATABASE_PATH=/app/data/shade.db; переменную DATABASE_URL не задавайте.
   Файл и таблицы создаются автоматически при первом старте. НЕ добавляйте
   `/app/data` в Git и не удаляйте его при обновлениях. Убедитесь, что
   контейнер имеет право записи в `/app/data`.
5. Перезапустите BotHost. Откройте HTTPS-ссылку Mini App, затем в BotFather
   выполните /setmenubutton и задайте WEBAPP_URL.
6. Напишите боту /start, затем /admin. Создайте тарифы, например
   `/adm_plan 30 100 2 0 Месяц`.

### VPN на отдельном VPS

Ubuntu 24.04, WireGuard (`wg0`, UDP/51820), настроенные IPv4 forwarding и
NAT. Открыть снаружи UDP/51820 и TCP/443; порт приложения агента 8080 держать
локальным. На VPS разверните тот же shade.py в SHADE_MODE=agent,
WG_INTERFACE=wg0, PORT=8080, AGENT_BIND=127.0.0.1 и WG_AGENT_SECRET.
Caddy проксирует https://wg.example.org на 127.0.0.1:8080. Секреты
агента/VPS не должны храниться внутри публичного Mini App. В BotHost
WG_AGENT_URL=https://wg.example.org, WG_SERVER_ENDPOINT=PUBLIC_IP:51820,
WG_SERVER_PUBLIC_KEY=(ключ сервера из `wg pubkey`), WG_SERVER_CIDR=10.13.0.0/24.
См. Caddyfile.agent.example и shade-agent.service.example.

### Проверки и бэкап

`python shade.py selftest` — криптографические тесты.
`python shade.py dbtest` — проверка таблиц SQLite, дат UTC, подписки и дублирования уведомлений.
`python shade.py verify` — проверка Telegram Bot API, SQLite и агента VPS.
`python shade.py backup /app/data/backups` — создаёт консистентную .sqlite
  резервную копию; для надёжности копируйте её ЗА ПРЕДЕЛЫ BotHost.
`python shade.py restore /path/to/backup.sqlite --confirm-restore` — восстановить
  из копии ТОЛЬКО ПРИ ОСТАНОВЛЕННОМ БОТЕ (иначе риск повреждения).

До включения ENABLE_PAYMENTS=1: проверьте на реальных устройствах VPN-туннель,
подписку, пробный период, лимиты и отзыв Peer, возвраты и Telegram Stars.
Оплата цифровых услуг должна соответствовать правилам Telegram и законам.

**SQLite рассчитана на один процесс.** Для нескольких экземпляров приложение
нужно перенести на PostgreSQL вместе с миграцией данных, здесь автоматического
переноса старой PostgreSQL-базы нет. Не запускайте одновременно два polling-бота.
Полный production-аудит безопасности и реальная интеграционная проверка должны
выполняться после подключения VPS, BotHost и Telegram.
""",
    }
    for filename, content in files.items():
        destination = path / filename
        if destination.exists():
            raise RuntimeError(f"Не перезаписываем существующий файл: {destination}")
        destination.write_text(content, encoding="utf-8")
        if filename.startswith(".env"):
            destination.chmod(0o600)
    print("Готово. Сгенерированы шаблоны в:", path.resolve())


def backup_environment() -> tuple[dict, str]:
    """Pass PG credentials only by process environment, not command arguments."""
    if not DATABASE_URL:
        raise ValueError("Нужна переменная окружения DATABASE_URL")
    u = urlparse(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1))
    if u.scheme != "postgresql" or not u.hostname or not u.path.strip("/"):
        raise ValueError("Неверный DATABASE_URL")
    env = os.environ.copy()
    env.update(PGHOST=u.hostname, PGPORT=str(u.port or 5432),
               PGUSER=unquote(u.username or ""), PGPASSWORD=unquote(u.password or ""),
               PGSSLMODE="require" if u.hostname not in ("localhost", "127.0.0.1", "db") else "prefer")
    return env, unquote(u.path.lstrip("/"))


def command_backup(directory: str) -> str:
    if DATABASE_IS_SQLITE:
        import sqlite3
        folder = pathlib.Path(directory).expanduser().resolve()
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        folder.chmod(0o700)
        if not DATABASE_PATH.is_file():
            raise RuntimeError(f"SQLite база ещё не создана: {DATABASE_PATH}. Запустите Still VPN сначала.")
        target = folder / ("shade-" + now().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4) + ".sqlite")
        # Built-in online backup captures a coherent snapshot, including any WAL changes.
        try:
            with sqlite3.connect(f"file:{DATABASE_PATH.as_posix()}?mode=ro", uri=True, timeout=30) as source:
                target.touch(mode=0o600, exist_ok=False)
                with sqlite3.connect(str(target), timeout=30) as dest:
                    source.backup(dest, pages=100, sleep=0.05)
                    integrity = dest.execute("PRAGMA quick_check").fetchone()
                    if integrity != ("ok",):
                        raise RuntimeError("SQLite backup failed integrity check")
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        print("SQLite backup создан и проверен:", target)
        return str(target)
    if shutil.which("pg_dump") is None:
        raise RuntimeError("pg_dump не найден: установите postgresql-client")
    env, database = backup_environment()
    folder = pathlib.Path(directory).expanduser()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder.chmod(0o700)
    filename = "shade-" + now().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4) + ".dump"
    target = folder / filename
    fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        subprocess.run(["pg_dump", "--format=custom", "--compress=6", "--no-owner",
                        "--no-privileges", "--file", str(target), database],
                       check=True, timeout=3600, env=env)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    print("Backup создан:", target)
    return str(target)


def command_restore(filename: str, confirm: bool):
    if not confirm:
        raise ValueError("Добавьте --confirm-restore после проверки целевой БД и резервной копии")
    if DATABASE_IS_SQLITE:
        import sqlite3
        source_path = pathlib.Path(filename).expanduser().resolve()
        if not source_path.is_file() or source_path.suffix != ".sqlite":
            raise ValueError("Укажите существующую резервную копию .sqlite")
        if source_path == DATABASE_PATH.resolve():
            raise ValueError("Нельзя восстанавливать базу из самой себя")
        # Administrator must stop the bot first. Running restore on an active DB is unsafe.
        with sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True, timeout=30) as source:
            if source.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise RuntimeError("Повреждённый файл резервной копии")
            DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with sqlite3.connect(str(DATABASE_PATH), timeout=30) as target:
                source.backup(target, pages=100, sleep=0.05)
                if target.execute("PRAGMA quick_check").fetchone() != ("ok",):
                    raise RuntimeError("Проверка восстановленной БД не прошла")
                target.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        print("SQLite восстановлена:", DATABASE_PATH)
        return
    if shutil.which("pg_restore") is None:
        raise RuntimeError("pg_restore не найден: установите postgresql-client")
    target = pathlib.Path(filename).resolve()
    if not target.is_file() or target.suffix != ".dump":
        raise ValueError("Не найден файл дампа .dump")
    env, database = backup_environment()
    subprocess.run(["pg_restore", "--clean", "--if-exists", "--no-owner",
                    "--no-privileges", "--dbname", database, str(target)],
                   check=True, timeout=3600, env=env)
    print("Восстановлено в БД:", database)


def command_selftest():
    """Dependency-free validation tests; live integrations still need external checks."""
    from urllib.parse import quote
    global BOT_TOKEN
    original = BOT_TOKEN
    BOT_TOKEN = "12345:TEST_SHADE_BOT_TOKEN"
    try:
        auth_date = int(time.time())
        person = {"id": 123456789, "first_name": "Test", "username": "testuser"}
        data = {"auth_date": str(auth_date), "user": json.dumps(person, separators=(',', ':')),
                "query_id": "AAEtest"}
        check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        auth_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        data["hash"] = hmac.new(auth_key, check.encode(), hashlib.sha256).hexdigest()
        raw = "&".join(f"{k}={quote(v, safe='')}" for k, v in data.items())
        assert validate_init_data(raw)["id"] == person["id"]
        signed_data = dict(data)
        signed_data["signature"] = "telegram-ed25519-signature-field"
        signed_check = "\n".join(f"{k}={v}" for k, v in sorted(signed_data.items()) if k != "hash")
        signed_data["hash"] = hmac.new(auth_key, signed_check.encode(), hashlib.sha256).hexdigest()
        signed_raw = "&".join(f"{k}={quote(v, safe='')}" for k, v in signed_data.items())
        assert validate_init_data(signed_raw)["id"] == person["id"]
        def should_fail(value):
            try: validate_init_data(value)
            except HTTPException as exc:
                assert exc.status_code == 401
                return
            raise AssertionError("Invalid initData was accepted")
        should_fail(raw.replace("testuser", "hacker"))
        should_fail(signed_raw.replace("telegram-ed25519", "forged"))
        should_fail(raw + "&auth_date=5")
        expired = dict(data);expired["auth_date"] = str(auth_date - 90000)
        check = "\n".join(f"{k}={v}" for k,v in sorted(expired.items()) if k != "hash")
        expired["hash"] = hmac.new(auth_key, check.encode(), hashlib.sha256).hexdigest()
        should_fail("&".join(f"{k}={quote(v, safe='')}" for k,v in expired.items()))
        assert validate_wg_key(base64.b64encode(bytes(range(32))).decode())
        assert not validate_wg_key("bad-key")
        assert code_hash("ABC") == code_hash("ABC") and code_hash("ABC") != code_hash("XYZ")
        print("PASS: подписанный initData, фальсификация, повторы, срок, WireGuard ключ, HMAC кодов")
    finally:
        BOT_TOKEN = original


def dispatch_cli():
    if len(sys.argv) < 2 or sys.argv[1] not in ("selftest", "generate", "backup", "restore"):
        return
    ap = argparse.ArgumentParser(description="Still VPN auxiliary commands")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    gen = sub.add_parser("generate"); gen.add_argument("directory", nargs="?", default="./shade-deploy")
    bk = sub.add_parser("backup"); bk.add_argument("directory")
    restore = sub.add_parser("restore"); restore.add_argument("filename")
    restore.add_argument("--confirm-restore", action="store_true")
    args = ap.parse_args()
    if args.command == "selftest": command_selftest()
    elif args.command == "generate": command_generate(args.directory)
    elif args.command == "backup": command_backup(args.directory)
    elif args.command == "restore": command_restore(args.filename, args.confirm_restore)
    raise SystemExit(0)

if __name__ == "__main__":
    dispatch_cli()


# BotHost App Data stores SQLite by default; external PostgreSQL is optional.
if MODE == "app":
    from sqlalchemy import (
        BigInteger, Boolean, DateTime, ForeignKey, Integer, String,
        Text, UniqueConstraint, select, func, update, delete, text, event
    )
    from sqlalchemy.types import TypeDecorator
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from aiogram import Bot, Dispatcher, Router, F
    from aiogram.filters import Command, CommandStart
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    from aiogram.types import (
        Message, CallbackQuery, PreCheckoutQuery, WebAppInfo,
        InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice,
        BotCommand, BufferedInputFile
    )
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from html import escape as html_escape
    import httpx

    def _read_bot_meta_state() -> dict[str, Any]:
        try:
            if BOT_META_STATE_PATH.exists():
                data = json.loads(BOT_META_STATE_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception:
            LOG.debug("Cannot read bot profile state", exc_info=True)
        return {}

    def _write_bot_meta_state(data: dict[str, Any]) -> None:
        try:
            BOT_META_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            BOT_META_STATE_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            LOG.debug("Cannot write bot profile state", exc_info=True)

    async def sync_bot_profile(bot: Bot) -> None:
        desired = {
            "name": "Still VPN",
            "short_description": "Still VPN — управление подпиской и VPN-подключениями в Telegram.",
            "description": (
                "Still VPN: личный кабинет, подписки, устройства и безопасные "
                "WireGuard-подключения. Откройте Mini App через /start. "
                "Поддержка: /support."
            ),
        }
        desired_hash = hashlib.sha256(
            json.dumps(desired, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        state = _read_bot_meta_state()
        now_ts = int(time.time())
        if state.get("desired_hash") == desired_hash and now_ts < int(state.get("next_attempt_after", 0) or 0):
            return
        try:
            await bot.set_my_name(name=desired["name"])
            await bot.set_my_short_description(short_description=desired["short_description"])
            await bot.set_my_description(description=desired["description"])
            _write_bot_meta_state({
                "desired_hash": desired_hash,
                "updated_at": now_ts,
                "next_attempt_after": now_ts + 86400,
            })
        except TelegramRetryAfter as exc:
            retry_after = int(getattr(exc, "retry_after", 3600) or 3600)
            LOG.warning(
                "Telegram ограничил обновление имени/описания бота; повтор позже через %s сек.",
                retry_after,
            )
            _write_bot_meta_state({
                "desired_hash": desired_hash,
                "updated_at": now_ts,
                "next_attempt_after": now_ts + retry_after + 60,
            })
        except Exception as exc:
            LOG.warning("Не удалось обновить имя/описание бота через Telegram: %s", exc)
            _write_bot_meta_state({
                "desired_hash": desired_hash,
                "updated_at": now_ts,
                "next_attempt_after": now_ts + 21600,
            })

    class UTCDateTime(TypeDecorator):
        """UTC-aware timestamps for BOTH SQLite and PostgreSQL.

        sqlite3 returns naive datetime values even for timezone=True. Comparing them
        to aware UTC now() otherwise raises TypeError and disables subscriptions.
        """
        impl = DateTime(timezone=True)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            value = value.astimezone(UTC)
            return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
        username: Mapped[str] = mapped_column(String(128), default="")
        first_name: Mapped[str] = mapped_column(String(200), default="")
        last_name: Mapped[str] = mapped_column(String(200), default="")
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        blocked: Mapped[bool] = mapped_column(Boolean, default=False)
        traffic_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    class Plan(Base):
        __tablename__ = "plans"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        title: Mapped[str] = mapped_column(String(120))
        days: Mapped[int] = mapped_column(Integer)
        stars: Mapped[int] = mapped_column(Integer)
        devices: Mapped[int] = mapped_column(Integer)
        traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    class Subscription(Base):
        __tablename__ = "subscriptions"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        name: Mapped[str] = mapped_column(String(120))
        starts_at: Mapped[datetime] = mapped_column(UTCDateTime())
        ends_at: Mapped[datetime] = mapped_column(UTCDateTime())
        days: Mapped[int] = mapped_column(Integer)
        devices: Mapped[int] = mapped_column(Integer)
        traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        baseline_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        source: Mapped[str] = mapped_column(String(20))
        payment_id: Mapped[str | None] = mapped_column(ForeignKey("payments.id"), unique=True, nullable=True)
        revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    class Trial(Base):
        __tablename__ = "trials"
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
        started_at: Mapped[datetime] = mapped_column(UTCDateTime())
        ends_at: Mapped[datetime] = mapped_column(UTCDateTime())
        baseline_bytes: Mapped[int] = mapped_column(BigInteger)
        traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        devices: Mapped[int] = mapped_column(Integer)

    class Payment(Base):
        __tablename__ = "payments"
        id: Mapped[str] = mapped_column(String(36), primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        kind: Mapped[str] = mapped_column(String(12))  # subscription / gift
        plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
        plan_title: Mapped[str] = mapped_column(String(120))
        days: Mapped[int] = mapped_column(Integer)
        devices: Mapped[int] = mapped_column(Integer)
        traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        amount: Mapped[int] = mapped_column(Integer)
        status: Mapped[str] = mapped_column(String(20), default="pending")
        telegram_charge_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        promo_id: Mapped[int | None] = mapped_column(ForeignKey("promos.id"), nullable=True)
        refunded_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        refund_reason: Mapped[str] = mapped_column(Text, default="")

    class ServerNode(Base):
        __tablename__ = "server_nodes"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        location: Mapped[str] = mapped_column(String(80))
        endpoint: Mapped[str] = mapped_column(String(255))
        public_key: Mapped[str] = mapped_column(String(44))
        cidr: Mapped[str] = mapped_column(String(36))
        agent_url: Mapped[str] = mapped_column(String(255))
        next_host: Mapped[int] = mapped_column(Integer, default=2)
        enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    class Device(Base):
        __tablename__ = "devices"
        id: Mapped[str] = mapped_column(String(36), primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        server_id: Mapped[int] = mapped_column(ForeignKey("server_nodes.id"))
        name: Mapped[str] = mapped_column(String(60))
        platform: Mapped[str] = mapped_column(String(24))
        public_key: Mapped[str] = mapped_column(String(44), unique=True)
        peer_ip: Mapped[str] = mapped_column(String(46), unique=True)
        enabled: Mapped[bool] = mapped_column(Boolean, default=True)
        provisioned: Mapped[bool] = mapped_column(Boolean, default=False)
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        last_handshake: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        peer_rx: Mapped[int] = mapped_column(BigInteger, default=0)
        peer_tx: Mapped[int] = mapped_column(BigInteger, default=0)

    class Gift(Base):
        __tablename__ = "gifts"
        id: Mapped[str] = mapped_column(String(36), primary_key=True)
        buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), unique=True)
        code_hash: Mapped[str] = mapped_column(String(64), unique=True)
        code_encrypted: Mapped[str] = mapped_column(Text)
        days: Mapped[int] = mapped_column(Integer)
        devices: Mapped[int] = mapped_column(Integer)
        traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        name: Mapped[str] = mapped_column(String(120))
        expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
        used_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
        subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), unique=True, nullable=True)
        used_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        invalid: Mapped[bool] = mapped_column(Boolean, default=False)

    class Promo(Base):
        __tablename__ = "promos"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        code_hash: Mapped[str] = mapped_column(String(64), unique=True)
        days: Mapped[int] = mapped_column(Integer)
        max_uses: Mapped[int] = mapped_column(Integer)
        uses: Mapped[int] = mapped_column(Integer, default=0)
        expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
        enabled: Mapped[bool] = mapped_column(Boolean, default=True)
        devices: Mapped[int] = mapped_column(Integer, default=1)
        discount_percent: Mapped[int] = mapped_column(Integer, default=0)

    class PromoUse(Base):
        __tablename__ = "promo_uses"
        __table_args__ = (UniqueConstraint("promo_id", "user_id"),)
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        promo_id: Mapped[int] = mapped_column(ForeignKey("promos.id"))
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    class PromoReservation(Base):
        __tablename__ = "promo_reservations"
        payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), primary_key=True)
        promo_id: Mapped[int] = mapped_column(ForeignKey("promos.id"), index=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        status: Mapped[str] = mapped_column(String(20), default="pending")
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    class NodeHealth(Base):
        __tablename__ = "node_health"
        server_id: Mapped[int] = mapped_column(ForeignKey("server_nodes.id"), primary_key=True)
        last_seen: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        cpu_percent: Mapped[float | None] = mapped_column(nullable=True)
        memory_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        memory_total: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        disk_free: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        network_rx: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        network_tx: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        peer_count: Mapped[int] = mapped_column(Integer, default=0)
        error: Mapped[str] = mapped_column(String(160), default="")

    class Ticket(Base):
        __tablename__ = "tickets"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        title: Mapped[str] = mapped_column(String(140), default="Обращение")
        priority: Mapped[str] = mapped_column(String(16), default="normal")
        status: Mapped[str] = mapped_column(String(20), default="open")  # open / answered / closed
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        assigned_admin: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    class TicketMessage(Base):
        __tablename__ = "ticket_messages"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
        sender: Mapped[str] = mapped_column(String(12))
        staff_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
        text: Mapped[str] = mapped_column(Text)
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    TICKET_PRIORITIES = {"normal": "Обычный", "medium": "Средний", "critical": "Критический"}

    def ticket_public(t: Ticket) -> dict:
        return {"id": t.id, "user_id": t.user_id, "title": t.title,
                "priority": t.priority, "status": t.status,
                "created_at": dt_iso(t.created_at), "updated_at": dt_iso(t.updated_at),
                "closed_at": dt_iso(t.closed_at), "assigned_admin": t.assigned_admin}

    def ticket_event_details(t: Ticket) -> str:
        # Never forward the full support conversation to the Telegram log group.
        return (f"Тикет #{t.id} · {TICKET_PRIORITIES.get(t.priority, 'Обычный')} · "
                f"{t.title[:110]}")

    class Admin(Base):
        __tablename__ = "admins"
        user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
        role: Mapped[str] = mapped_column(String(20))

    class Setting(Base):
        __tablename__ = "settings"
        key: Mapped[str] = mapped_column(String(100), primary_key=True)
        value: Mapped[str] = mapped_column(String(512))

    class Audit(Base):
        __tablename__ = "audit"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        admin_id: Mapped[int] = mapped_column(BigInteger)
        action: Mapped[str] = mapped_column(String(60))
        target: Mapped[str] = mapped_column(String(140))
        details: Mapped[str] = mapped_column(Text)
        result: Mapped[str] = mapped_column(String(20), default="ok")
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    class ActivityEvent(Base):
        """Durable, privacy-limited outbox for the owner's Telegram activity group."""
        __tablename__ = "activity_events"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        kind: Mapped[str] = mapped_column(String(64))
        user_id: Mapped[int] = mapped_column(BigInteger)
        details: Mapped[str] = mapped_column(String(700), default="")
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
        sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        attempts: Mapped[int] = mapped_column(Integer, default=0)

    class Referral(Base):
        """Invite attribution only; no auto-bonuses, to avoid trial farming."""
        __tablename__ = "referrals"
        invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
        inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    class WebAccount(Base):
        """Independent site account bound to a User (negative ID unless explicitly linked)."""
        __tablename__ = "web_accounts"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
        login: Mapped[str] = mapped_column(String(32), unique=True, index=True)
        password_salt: Mapped[str] = mapped_column(String(32))
        password_hash: Mapped[str] = mapped_column(String(64))
        recovery_hash: Mapped[str] = mapped_column(String(64))
        email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True)
        email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
        failed_logins: Mapped[int] = mapped_column(Integer, default=0)
        locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    class WebSession(Base):
        __tablename__ = "web_sessions"
        token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
        account_id: Mapped[int] = mapped_column(ForeignKey("web_accounts.id"), index=True)
        expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
        created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)

    class WebEmailChallenge(Base):
        __tablename__ = "web_email_challenges"
        account_id: Mapped[int] = mapped_column(ForeignKey("web_accounts.id"), primary_key=True)
        code_hash: Mapped[str] = mapped_column(String(64))
        expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
        sent_at: Mapped[datetime] = mapped_column(UTCDateTime())
        attempts: Mapped[int] = mapped_column(Integer, default=0)

    class WebLinkCode(Base):
        __tablename__ = "web_link_codes"
        code_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
        telegram_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        expires_at: Mapped[datetime] = mapped_column(UTCDateTime())

    class Notice(Base):
        __tablename__ = "notices"
        __table_args__ = (UniqueConstraint("user_id", "kind", "ref"),)
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
        kind: Mapped[str] = mapped_column(String(50))
        ref: Mapped[str] = mapped_column(String(40))
        text: Mapped[str] = mapped_column(Text)
        sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # A single SQLite connection serializes concurrent transactions in this one-process
    # deployment. WAL permits consistent external online backups/read-only inspection.
    if DATABASE_IS_SQLITE:
        engine = create_async_engine(DATABASE_URL, pool_pre_ping=True,
                                     pool_size=1, max_overflow=0, pool_timeout=60,
                                     connect_args={"timeout": 60})
        @event.listens_for(engine.sync_engine, "connect")
        def configure_sqlite(connection, record):
            cursor = connection.cursor()
            try:
                cursor.execute("PRAGMA busy_timeout=60000")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
            finally:
                cursor.close()
    else:
        engine = create_async_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
    Session = async_sessionmaker(engine, expire_on_commit=False) if engine else None
    bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
    dp = Dispatcher()
    router = Router()
    dp.include_router(router)
    try:
        fernet = Fernet(GIFT_FERNET_KEY.encode()) if GIFT_FERNET_KEY else None
    except (ValueError, TypeError):
        # A malformed optional key must not take down the entire VPN service.
        # Gift code retrieval and new Stars invoices remain disabled.
        LOG.error("GIFT_FERNET_KEY некорректен: подарочные коды и новые платежи отключены")
        fernet = None

    def payments_ready() -> bool:
        # Only valid, complete payment configuration may create/accept new invoices.
        # Existing successful_payment callbacks are still processed for idempotent fulfillment.
        return bool(ENABLE_PAYMENTS and TERMS_URL.startswith("https://")
                    and fernet is not None and len(WG_AGENT_SECRET) >= 32)

    async def db_session():
        async with Session() as s:
            yield s

    async def upsert_user(s: AsyncSession, tg: Any) -> User:
        uid = int(tg.id if hasattr(tg, "id") else tg["id"])
        user = await s.get(User, uid)
        username = (tg.username if hasattr(tg, "username") else tg.get("username")) or ""
        first = (tg.first_name if hasattr(tg, "first_name") else tg.get("first_name")) or ""
        last = (tg.last_name if hasattr(tg, "last_name") else tg.get("last_name")) or ""
        if not user:
            user = User(id=uid, username=username[:128], first_name=first[:200], last_name=last[:200])
            s.add(user)
            record_event(s, "registration_telegram", uid, "Новый пользователь Telegram")
        else:
            user.username = username[:128]
            user.first_name = first[:200]
            user.last_name = last[:200]
        await s.flush()
        return user

    async def role_of(s: AsyncSession, uid: int) -> str | None:
        if uid in OWNER_IDS:
            return "owner"
        record = await s.get(Admin, uid)
        return record.role if record else None

    async def require_role(uid: int, permitted: set[str]) -> bool:
        async with Session() as s:
            role = await role_of(s, uid)
        return role in permitted

    def record_event(s: AsyncSession, kind: str, user_id: int, details: str = "") -> None:
        # Never include passwords, .conf/private keys, auth tokens, email, or traffic contents.
        if LOG_CHAT_ID:
            s.add(ActivityEvent(kind=kind[:64], user_id=int(user_id), details=details[:700]))

    def audit(s: AsyncSession, admin_id: int, action: str, target: Any, details: str = ""):
        s.add(Audit(admin_id=admin_id, action=action, target=str(target)[:140], details=details[:4000]))
        record_event(s, "admin_" + action[:55], admin_id, "Цель: " + str(target)[:100] +
                     (" · " + details[:190] if details else ""))

    async def deliver_group_events() -> None:
        """Committed event outbox: retries without holding DB connection over Telegram I/O."""
        if not LOG_CHAT_ID or not bot:
            return
        async with Session() as s:
            events = (await s.scalars(select(ActivityEvent).where(
                ActivityEvent.sent_at.is_(None)
            ).order_by(ActivityEvent.id).limit(25))).all()
            outgoing = []
            for evt in events:
                user = await s.get(User, evt.user_id)
                if user:
                    full_name = html_escape((user.first_name + " " + user.last_name).strip() or "Имя не указано")
                    username = "@" + html_escape(user.username) if user.username and not user.username.startswith("web:") else "без @username"
                    if user.id > 0:
                        identity = f'<a href="tg://user?id={user.id}">{full_name}</a> · {username}'
                    else:
                        identity = f"{full_name} · сайт (без Telegram)"
                else:
                    identity = "Пользователь неизвестен"
                text = (f"<b>STILL / {html_escape(evt.kind.replace('_', ' ').upper())}</b>\n"
                        f"👤 {identity}\n🆔 <code>{evt.user_id}</code>\n"
                        f"🕒 {evt.created_at:%d.%m.%Y %H:%M} UTC"
                        + ("\n📝 " + html_escape(evt.details) if evt.details else ""))
                outgoing.append((evt.id, text))
        for event_id, text in outgoing:
            try:
                await bot.send_message(LOG_CHAT_ID, text, parse_mode="HTML",
                                       disable_web_page_preview=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                async with Session.begin() as s:
                    evt = await s.get(ActivityEvent, event_id)
                    if evt: evt.attempts += 1
                LOG.warning("Activity group delivery failed (chat %s, event %s): %s",
                            LOG_CHAT_ID, event_id, str(exc)[:180])
                break
            async with Session.begin() as s:
                evt = await s.get(ActivityEvent, event_id)
                if evt and evt.sent_at is None:
                    evt.sent_at = now()
        async with Session.begin() as s:
            await s.execute(delete(ActivityEvent).where(
                ActivityEvent.sent_at < now() - timedelta(days=30)))

    async def setting(s: AsyncSession, key: str, default: str) -> str:
        item = await s.get(Setting, key)
        return item.value if item else default

    def subs_select(uid: int):
        return select(Subscription).where(Subscription.user_id == uid, Subscription.revoked.is_(False)).order_by(Subscription.starts_at, Subscription.id)

    async def entitlement(s: AsyncSession, user: User) -> dict | None:
        if user.blocked:
            return None
        current = now()
        rows = (await s.scalars(subs_select(user.id))).all()
        for sub in rows:
            if sub.starts_at <= current < sub.ends_at:
                baseline = sub.baseline_bytes if sub.baseline_bytes is not None else user.traffic_bytes
                used = max(0, user.traffic_bytes - baseline)
                if sub.traffic_bytes is not None and used >= sub.traffic_bytes:
                    return None
                return {"type": "paid", "name": sub.name, "end": sub.ends_at, "devices": sub.devices,
                        "limit": sub.traffic_bytes, "used": used, "sub_id": sub.id}
        trial = await s.get(Trial, user.id)
        if trial and current < trial.ends_at:
            used = max(0, user.traffic_bytes - trial.baseline_bytes)
            if trial.traffic_bytes is None or used < trial.traffic_bytes:
                return {"type": "trial", "name": "Пробный", "end": trial.ends_at,
                        "devices": trial.devices, "limit": trial.traffic_bytes, "used": used}
        return None

    async def add_subscription(s: AsyncSession, user: User, name: str, days: int,
                               devices: int, traffic: int | None, source: str,
                               payment_id: str | None = None) -> Subscription:
        rows = (await s.scalars(subs_select(user.id))).all()
        end = max([now()] + [x.ends_at for x in rows])
        sub = Subscription(user_id=user.id, name=name, days=days, starts_at=end,
                           ends_at=end + timedelta(days=days), devices=devices,
                           traffic_bytes=traffic, baseline_bytes=user.traffic_bytes if end <= now() else None,
                           source=source, payment_id=payment_id)
        s.add(sub)
        record_event(s, "subscription_issued", user.id,
                     f"Источник: {source} · {name} · {days} дней · {devices} устройств")
        await s.flush()
        return sub

    async def compact_future_subscriptions(s: AsyncSession, uid: int) -> None:
        """On refund close holes in the future subscription queue, preserving paid days."""
        live = (await s.scalars(select(Subscription).where(
            Subscription.user_id == uid, Subscription.revoked.is_(False)
        ).order_by(Subscription.starts_at, Subscription.id))).all()
        cursor = now()
        for sub in live:
            if sub.starts_at <= now() < sub.ends_at:
                cursor = max(cursor, sub.ends_at)
            elif sub.starts_at > now():
                sub.starts_at = cursor
                sub.ends_at = cursor + timedelta(days=sub.days)
                sub.baseline_bytes = None
                cursor = sub.ends_at

    async def queue_notice(s: AsyncSession, uid: int, kind: str, ref: str, text: str):
        # Browser-only accounts have no Telegram chat. Do not schedule undeliverable bot messages.
        if uid <= 0:
            return
        # A unique constraint guarantees idempotent scheduling.
        if DATABASE_IS_SQLITE:
            from sqlalchemy.dialects.sqlite import insert
        else:
            from sqlalchemy.dialects.postgresql import insert
        stmt = insert(Notice).values(user_id=uid, kind=kind, ref=ref, text=text, sent=False)
        result = await s.execute(stmt.on_conflict_do_nothing(index_elements=["user_id", "kind", "ref"]))
        if result.rowcount and kind in ("trial_ended", "expired", "traffic_exhausted"):
            record_event(s, kind, uid, "Серверное событие: " + text[:150])

    async def get_node(s: AsyncSession, node_id: int) -> ServerNode:
        node = await s.get(ServerNode, node_id)
        if not node:
            bad(503, "VPN-сервер не найден")
        return node

    def node_agent_secret(node: ServerNode) -> str:
        secret = WG_AGENT_SECRETS.get(str(node.id), WG_AGENT_SECRET if node.id == 1 else "")
        if not isinstance(secret, str) or len(secret) < 32:
            raise RuntimeError(f"No secure WG agent secret configured for node {node.id}")
        return secret

    def agent_signature(ts: str, nonce: str, method: str, path: str, body: bytes, secret: str) -> str:
        msg = b"\n".join([ts.encode(), nonce.encode(), method.encode(), path.encode(), body])
        return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

    async def agent_request(node: ServerNode, method: str, path: str, payload: dict | None = None) -> dict:
        if not node.agent_url.startswith("https://"):
            raise RuntimeError("Агент не настроен: HTTPS обязателен")
        secret = node_agent_secret(node)
        body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else b""
        ts = str(int(time.time()))
        nonce = secrets.token_hex(16)
        headers = {"X-Shade-Ts": ts, "X-Shade-Nonce": nonce,
                   "X-Shade-Sign": agent_signature(ts, nonce, method, path, body, secret)}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.request(method, node.agent_url + path, content=body, headers=headers)
            response.raise_for_status()
            return response.json()

    async def apply_peer(device: Device, node: ServerNode, allow: bool,
                         valid_until: datetime | None = None) -> None:
        payload = {"public_key": device.public_key, "ip": device.peer_ip, "allow": allow}
        if allow:
            # Lease renewal is sent every minute; if BotHost goes offline, the VPS
            # automatically removes access after at most WG_PEER_LEASE_SECONDS.
            deadline = now() + timedelta(seconds=WG_PEER_LEASE_SECONDS)
            if valid_until is not None:
                deadline = min(deadline, valid_until)
            payload["expires_at"] = int(deadline.timestamp())
        await agent_request(node, "POST", "/agent/peer", payload)

    async def ensure_access(s: AsyncSession, uid: int):
        user = await s.get(User, uid)
        if not user:
            return
        granted = await entitlement(s, user)
        devices = (await s.scalars(select(Device).where(Device.user_id == uid))).all()
        for dev in devices:
            node = await s.get(ServerNode, dev.server_id)
            if not node:
                continue
            should = bool(granted and dev.enabled)
            # Active devices must renew their short-lived leases even when
            # already provisioned; inactive devices need a single revocation.
            if not should and not dev.provisioned:
                continue
            try:
                previously_active = bool(dev.provisioned)
                await apply_peer(dev, node, should, granted["end"] if should else None)
                dev.provisioned = should
                if previously_active and not should:
                    record_event(s, "vpn_access_ended", uid,
                                 f"Доступ закрыт: {dev.name} · {dev.peer_ip}")
            except Exception as exc:
                LOG.warning("Peer reconcile failed (%s): %s", dev.id, exc)

    async def refresh_stats(s: AsyncSession, node: ServerNode):
        result = await agent_request(node, "GET", "/agent/stats")
        remote = {x["public_key"]: x for x in result["peers"]}
        devices = (await s.scalars(select(Device).where(Device.server_id == node.id))).all()
        for dev in devices:
            p = remote.get(dev.public_key)
            if p:
                rx, tx = int(p["rx"]), int(p["tx"])
                delta = max(0, rx - dev.peer_rx) + max(0, tx - dev.peer_tx)
                # Counter reset on wg restart: count current totals from zero.
                if rx < dev.peer_rx or tx < dev.peer_tx:
                    delta = rx + tx
                user = await s.get(User, dev.user_id)
                if user:
                    user.traffic_bytes += delta
                dev.peer_rx, dev.peer_tx = rx, tx
                hs = int(p.get("handshake") or 0)
                if hs:
                    latest = datetime.fromtimestamp(hs, UTC)
                    if dev.last_handshake is None:
                        record_event(s, "vpn_connected", dev.user_id,
                                     f"Первое WireGuard-соединение: {dev.name} · {dev.peer_ip}")
                    elif (latest - dev.last_handshake).total_seconds() > 600:
                        # A reconnect after a real gap, not normal WireGuard
                        # key re-handshakes during an uninterrupted session.
                        record_event(s, "vpn_reconnected", dev.user_id,
                                     f"Снова подключился: {dev.name} · {dev.peer_ip}")
                    dev.last_handshake = latest
                # Presence on the VPN server is independent of the local desired state.
                # This is essential to detect/revoke stale peers for blocked users.
                dev.provisioned = True
            else:
                dev.provisioned = False
                # The old kernel counters are no longer valid after removal;
                # fresh peers start from zero, preventing missed traffic.
                dev.peer_rx = 0
                dev.peer_tx = 0
        health = await s.get(NodeHealth, node.id)
        if not health:
            health = NodeHealth(server_id=node.id)
            s.add(health)
        health.last_seen = now()
        health.cpu_percent = result.get("cpu_percent")
        memory = result.get("memory", {})
        health.memory_total = memory.get("MemTotal")
        health.memory_used = (memory["MemTotal"] - memory["MemAvailable"]
                              if "MemTotal" in memory and "MemAvailable" in memory else None)
        health.disk_free = result.get("disk_free")
        health.network_rx = result.get("network_rx")
        health.network_tx = result.get("network_tx")
        health.peer_count = len(result["peers"])
        health.error = ""
        await s.flush()
        return result

    async def process_background():
        async with Session() as s:
            nodes = (await s.scalars(select(ServerNode))).all()
            for node in nodes:
                try:
                    await refresh_stats(s, node)
                except Exception as exc:
                    LOG.warning("Agent %s unavailable: %s", node.id, exc)
                    health = await s.get(NodeHealth, node.id)
                    if not health:
                        health = NodeHealth(server_id=node.id)
                        s.add(health)
                    health.error = str(exc)[:160]
            # Clear expired web sessions and one-time web codes.
            await s.execute(delete(WebSession).where(WebSession.expires_at < now()))
            await s.execute(delete(WebLinkCode).where(WebLinkCode.expires_at < now()))
            await s.execute(delete(WebEmailChallenge).where(WebEmailChallenge.expires_at < now()))
            # Expire unpaid invoices and discount slot reservations after one hour.
            cutoff = now() - timedelta(hours=1)
            await s.execute(update(Payment).where(Payment.status == "pending", Payment.created_at < cutoff)
                            .values(status="expired"))
            await s.execute(update(PromoReservation).where(PromoReservation.status == "pending",
                       PromoReservation.created_at < cutoff).values(status="expired"))
            await s.commit()
        async with Session() as s:
            users = (await s.scalars(select(User))).all()
            for user in users:
                # Future subscriptions start with the traffic baseline of activation.
                pending = (await s.scalars(select(Subscription).where(
                    Subscription.user_id == user.id,
                    Subscription.starts_at <= now(), Subscription.ends_at > now(),
                    Subscription.baseline_bytes.is_(None)))).all()
                for sub in pending:
                    sub.baseline_bytes = user.traffic_bytes
                rows = (await s.scalars(subs_select(user.id))).all()
                grant = await entitlement(s, user)
                if not grant:
                    for sub in rows:
                        if sub.starts_at <= now() < sub.ends_at and sub.traffic_bytes is not None:
                            baseline = sub.baseline_bytes if sub.baseline_bytes is not None else user.traffic_bytes
                            if user.traffic_bytes - baseline >= sub.traffic_bytes:
                                await queue_notice(s, user.id, "traffic_exhausted", str(sub.id),
                                                   "Still VPN: лимит трафика исчерпан, доступ отключён.")
                has_renewal = any(x.starts_at > now() and not x.revoked for x in rows)
                configured_hours = await setting(s, "notice_hours", "72,24,3")
                try:
                    hours_list = sorted({int(h) for h in configured_hours.split(",") if 1 <= int(h) <= 168}, reverse=True)
                except ValueError:
                    hours_list = [72, 24, 3]
                for sub in rows:
                    remaining = (sub.ends_at - now()).total_seconds()
                    if sub.starts_at <= now() and 0 < remaining and not has_renewal:
                        for h in hours_list:
                            if remaining <= h * 3600:
                                await queue_notice(s, user.id, "ends_in_hours_" + str(h), str(sub.id),
                                                   f"Still VPN: до окончания подписки осталось менее {h} ч.")
                    if remaining <= 0 and not grant:
                        await queue_notice(s, user.id, "expired", str(sub.id), "Still VPN: подписка закончилась. VPN-доступ отключён.")
                tr = await s.get(Trial, user.id)
                if tr and tr.ends_at <= now() and not grant:
                    await queue_notice(s, user.id, "trial_ended", str(user.id), "Still VPN: пробный период завершён.")
                await ensure_access(s, user.id)
            await s.commit()
        async with Session() as s:
            unsent = (await s.scalars(select(Notice).where(Notice.sent.is_(False)).order_by(Notice.id).limit(40))).all()
            for n in unsent:
                try:
                    notice_msg = ("<b>✦ STILL / УВЕДОМЛЕНИЕ</b>\n"
                                  "━━━━━━━━━━━━━━━━━━\n\n" + html_escape(n.text))
                    await bot.send_message(n.user_id, notice_msg, parse_mode="HTML")
                    n.sent = True
                    await s.commit()
                except Exception:
                    LOG.warning("Failed to send notification %s", n.id)

    sqlite_background_lock = asyncio.Lock()

    async def locked_background():
        if DATABASE_IS_SQLITE:
            # Only one bot+API process may access this SQLite deployment.
            if sqlite_background_lock.locked():
                return
            async with sqlite_background_lock:
                await process_background()
            return
        # PostgreSQL advisory lock is held by this dedicated database connection
        # for the full reconciliation; another replica skips the same job.
        async with engine.connect() as guard:
            acquired = await guard.scalar(text("SELECT pg_try_advisory_lock(829132401)"))
            if not acquired:
                return
            try:
                await process_background()
            finally:
                await guard.execute(text("SELECT pg_advisory_unlock(829132401)"))

    async def periodic_worker():
        while True:
            try:
                await locked_background()
                await deliver_group_events()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("Worker error")
            await asyncio.sleep(60)

    async def initialize_db():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            # New database: create_all installs the complete schema. Existing databases:
            # add only missing columns, with the appropriate syntax per SQL dialect.
            migration_columns = {
                "users": {"last_name": "VARCHAR(200) NOT NULL DEFAULT ''"},
                "payments": {
                    "promo_id": "INTEGER REFERENCES promos(id)",
                    "refunded_at": "TIMESTAMP",
                    "refund_reason": "TEXT NOT NULL DEFAULT ''",
                },
                "promos": {"discount_percent": "INTEGER NOT NULL DEFAULT 0"},
                "tickets": {"assigned_admin": "BIGINT",
                            "title": "VARCHAR(140) NOT NULL DEFAULT 'Обращение'",
                            "priority": "VARCHAR(16) NOT NULL DEFAULT 'normal'",
                            "updated_at": "TIMESTAMP",
                            "closed_at": "TIMESTAMP"},
                "ticket_messages": {"staff_id": "BIGINT"},
                "audit": {"result": "VARCHAR(20) NOT NULL DEFAULT 'ok'"},
            }
            if DATABASE_IS_SQLITE:
                for table, cols in migration_columns.items():
                    existing = {row[1] for row in (await connection.exec_driver_sql(
                        f"PRAGMA table_info({table})")).all()}
                    for col, column_type in cols.items():
                        if col not in existing:
                            await connection.exec_driver_sql(
                                f"ALTER TABLE {table} ADD COLUMN {col} {column_type}")
            else:
                for table, cols in migration_columns.items():
                    for col, column_type in cols.items():
                        await connection.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {column_type}"))
        # Backfill timestamps on old tickets without touching existing messages or status.
        async with Session.begin() as backfill_session:
            await backfill_session.execute(text(
                "UPDATE tickets SET updated_at = created_at WHERE updated_at IS NULL"))
        if WG_AGENT_URL and WG_SERVER_ENDPOINT and WG_SERVER_PUBLIC_KEY:
            if not validate_wg_key(WG_SERVER_PUBLIC_KEY):
                raise RuntimeError("WG_SERVER_PUBLIC_KEY incorrect")
            if not WG_AGENT_URL.startswith("https://"):
                raise RuntimeError("WG_AGENT_URL must use HTTPS")
            async with Session.begin() as s:
                node = await s.get(ServerNode, 1)
                if not node:
                    s.add(ServerNode(id=1, location=WG_SERVER_LOCATION, endpoint=WG_SERVER_ENDPOINT,
                                     public_key=WG_SERVER_PUBLIC_KEY, cidr=WG_SERVER_CIDR,
                                     agent_url=WG_AGENT_URL, next_host=2))
                else:
                    # Previously this applied only on first startup, leaving a
                    # stale Funnel URL in existing App Data after changing env.
                    node.agent_url = WG_AGENT_URL
                    node.endpoint = WG_SERVER_ENDPOINT
                    node.public_key = WG_SERVER_PUBLIC_KEY
                    node.cidr = WG_SERVER_CIDR

    @router.message.middleware()
    async def private_only_middleware(handler, event: Message, data: dict):
        # Group / supergroup / channel updates must never trigger a reply, a ticket,
        # a payment handler, or any other command. Outbound admin log delivery is unchanged.
        if not event.chat or event.chat.type != "private":
            return None
        return await handler(event, data)

    @router.callback_query.middleware()
    async def private_callbacks_only(handler, event: CallbackQuery, data: dict):
        if event.message and event.message.chat.type != "private":
            return None
        return await handler(event, data)

    def mini_url(section: str = "home") -> str:
        # WebAppInfo URL is opened inside the same Telegram bot WebView.
        # Keep navigation parameters separate from Telegram auth initData.
        return WEBAPP_URL + "/?tab=" + section

    def invite_link(uid: int) -> str:
        username = BOT_USERNAME["value"] or "StillVPNapp_bot"
        return f"https://t.me/{username}?start=ref_{uid}"

    def user_menu(admin: bool = False) -> InlineKeyboardMarkup:
        links = [
            [InlineKeyboardButton(text="✦ Открыть Mini App", web_app=WebAppInfo(url=mini_url()))],
            [InlineKeyboardButton(text="◈ Тарифы", web_app=WebAppInfo(url=mini_url("plans"))),
             InlineKeyboardButton(text="⌁ Подключить", web_app=WebAppInfo(url=mini_url("connect")))],
            [InlineKeyboardButton(text="🌐 Перейти на сайт", url=WEBAPP_URL + "/web"),
             InlineKeyboardButton(text="↗ Поделиться", callback_data="user:share")],
            [InlineKeyboardButton(text="📣 Наш канал · необязательно", url=CHANNEL_URL),
             InlineKeyboardButton(text="✉ Поддержка", web_app=WebAppInfo(url=mini_url("tickets")))],
        ]
        if admin:
            links.append([InlineKeyboardButton(text="⚙ Панель управления", web_app=WebAppInfo(url=mini_url("admin")))])
        return InlineKeyboardMarkup(inline_keyboard=links)

    async def send_user_menu(message: Message, focus: str = "home") -> None:
        if not message.from_user or message.chat.type != "private":
            return
        async with Session.begin() as s:
            await upsert_user(s, message.from_user)
            role = await role_of(s, message.from_user.id)
            banner = await setting(s, "start_photo_file_id", "")
        name = html_escape(message.from_user.first_name or "друг")
        if focus == "home":
            text_msg = (
                "<b>STILL VPN</b>  /  PRIVATE NETWORK\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"Привет, <b>{name}</b>! 👋\n\n"
                "<b>Один VPN — для всего интернета.</b>\n"
                "Подключай устройства, следи за трафиком и управляй подпиской без лишних шагов.\n\n"
                "🌍 <b>Сервер:</b> Нидерланды\n"
                "🔐 <b>Протокол:</b> WireGuard\n\n"
                "<i>Новости и обновления — в нашем канале. Подписка добровольная.</i>"
            )
        else:
            names = {"plans": "Тарифы и подписка", "account": "Личный кабинет", "connect": "Подключение"}
            text_msg = (f"<b>STILL / {names.get(focus, 'VPN')}</b>\n"
                        "━━━━━━━━━━━━━━━━━━\n\n"
                        "Открой раздел в Mini App или перейди на сайт. Все устройства и подписки привязаны к одному аккаунту.")
        markup = user_menu(bool(role))
        if focus == "home" and banner:
            try:
                await message.answer_photo(banner, caption=text_msg, parse_mode="HTML", reply_markup=markup)
                return
            except Exception as exc:
                LOG.warning("START photo invalid; falling back to text: %s", str(exc)[:160])
        await message.answer(text_msg, parse_mode="HTML", reply_markup=markup)

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        if not message.from_user or message.chat.type != "private":
            return
        # Attribution only on first registration. No rewards for self invites/trial farms.
        match = re.fullmatch(r"/start(?:@\w+)?\s+ref_([1-9][0-9]{0,18})\s*", message.text or "")
        if match:
            inviter_id = int(match.group(1))
            invitee_id = message.from_user.id
            if inviter_id != invitee_id:
                async with Session.begin() as s:
                    existing = await s.get(User, invitee_id)
                    inviter = await s.get(User, inviter_id)
                    if existing is None and inviter is not None and inviter_id > 0:
                        await upsert_user(s, message.from_user)
                        s.add(Referral(invitee_id=invitee_id, inviter_id=inviter_id))
                        record_event(s, "referral_joined", inviter_id,
                                     f"Приглашён новый пользователь · ID {invitee_id}")
        async with Session.begin() as s:
            record_event(s, "bot_start", message.from_user.id, "Открыл /start в Telegram")
        await send_user_menu(message)

    @router.message(Command("invite"))
    async def cmd_invite(message: Message):
        if not message.from_user or message.chat.type != "private": return
        link = invite_link(message.from_user.id)
        async with Session() as s:
            count = await s.scalar(select(func.count()).select_from(Referral).where(
                Referral.inviter_id == message.from_user.id)) or 0
        await message.answer(
            "<b>STILL / ПРИГЛАСИ ДРУГА</b>\n━━━━━━━━━━━━━━━━━━\n\n"
            f"Твоя ссылка:\n<code>{html_escape(link)}</code>\n\n"
            f"👥 Зарегистрировались по приглашению: <b>{count}</b>\n"
            "<i>Пока без бонусных дней: так мы защищаем пробные доступы от накрутки.</i>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↗ Поделиться в Telegram",
                                      url="https://t.me/share/url?url=" +
                                          quote(link, safe='') +
                                          "&text=Still%20VPN%20%E2%80%94%20%D0%BC%D0%BE%D0%B9%20VPN")]
            ]))

    @router.callback_query(F.data == "user:share")
    async def user_share_callback(callback: CallbackQuery):
        await callback.answer()
        if callback.message and callback.from_user:
            link = invite_link(callback.from_user.id)
            await callback.message.answer(
                "<b>Пригласи друга в Still VPN</b>\n\n"
                "Отправь ссылку ниже — она привязана к твоему аккаунту.\n"
                f"<code>{html_escape(link)}</code>", parse_mode="HTML")

    @router.message(Command("adm_start_photo"))
    async def adm_start_photo(message: Message):
        if not message.from_user or message.chat.type != "private": return
        if not await require_role(message.from_user.id, {"owner"}):
            await message.answer("⛔ Только владелец может менять приветственную картинку.")
            return
        source = (message.reply_to_message if message.reply_to_message and
                  message.reply_to_message.photo else message)
        if not source.photo:
            await message.answer("<b>Баннер /start</b>\n\n"
                                 "1. Отправь боту картинку как <b>фото</b>.\n"
                                 "2. Ответь на неё командой <code>/adm_start_photo</code>.\n\n"
                                 "Или отправь фото с подписью <code>/adm_start_photo</code>.",
                                 parse_mode="HTML")
            return
        file_id = source.photo[-1].file_id
        async with Session.begin() as s:
            row = await s.get(Setting, "start_photo_file_id")
            if row: row.value = file_id
            else: s.add(Setting(key="start_photo_file_id", value=file_id))
            audit(s, message.from_user.id, "start_photo_set", "welcome", "Баннер /start обновлён")
        await message.answer("✅ Картинка установлена. Напиши /start, чтобы увидеть её.")

    @router.message(Command("adm_start_photo_off"))
    async def adm_start_photo_off(message: Message):
        if not message.from_user or message.chat.type != "private": return
        if not await require_role(message.from_user.id, {"owner"}): return
        async with Session.begin() as s:
            row = await s.get(Setting, "start_photo_file_id")
            if row: await s.delete(row)
            audit(s, message.from_user.id, "start_photo_remove", "welcome")
        await message.answer("✅ Приветственная картинка убрана. /start снова отправляет текст.")

    @router.message(Command("adm_log_test"))
    async def adm_log_test(message: Message):
        if not message.from_user or message.chat.type != "private": return
        if not await require_role(message.from_user.id, {"owner"}): return
        async with Session.begin() as s:
            record_event(s, "test_delivery", message.from_user.id,
                         "Проверка доставки в закрытую служебную группу")
        await deliver_group_events()
        async with Session() as s:
            pending = await s.scalar(select(func.count()).select_from(ActivityEvent).where(
                ActivityEvent.sent_at.is_(None))) or 0
        await message.answer("<b>STILL / ЖУРНАЛ</b>\n━━━━━━━━━━━━━━━━━━\n\n"
                             f"Чат: <code>{LOG_CHAT_ID}</code>\n"
                             f"Событий в очереди: <b>{pending}</b>\n\n"
                             "Если тестового сообщения нет в группе, добавь бота и разреши ему отправлять сообщения. "
                             "Повторная отправка запланирована автоматически.", parse_mode="HTML")

    @router.message(Command("profile"))
    async def cmd_profile(message: Message):
        await send_user_menu(message, "account")

    @router.message(Command("plans"))
    async def cmd_plans(message: Message):
        await send_user_menu(message, "plans")

    @router.message(Command("connect"))
    async def cmd_connect(message: Message):
        await send_user_menu(message, "connect")

    @router.callback_query(F.data == "user:support")
    async def user_support_callback(callback: CallbackQuery):
        if callback.message and callback.message.chat.type == "private":
            await callback.message.answer(
                "<b>STILL / ПОДДЕРЖКА</b>\n\nСоздайте обращение и переписывайтесь "
                "с поддержкой в Mini App.\nНе отправляйте в тикеты приватные VPN-ключи.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Открыть тикеты", web_app=WebAppInfo(url=mini_url("tickets")))
                ]]))
        await callback.answer()

    @router.message(Command("help"))
    async def cmd_help(message: Message):
        await message.answer(
            "<b>STILL / НАВИГАЦИЯ</b>\n━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Быстрые команды</b>\n"
            "/start — открыть приложение\n"
            "/profile — профиль\n"
            "/plans — тарифы\n"
            "/connect — устройства и VPN\n"
            "/support — открыть тикеты в Mini App\n"
            "/terms — условия использования\n"
            "/linkweb — привязка к веб-кабинету\n"
            "/paysupport — оплата и возвраты\n"
            "/invite — пригласить друга\n\n"
            f'🌐 <a href="{html_escape(WEBAPP_URL)}/web">Сайт Still VPN</a>\n'
            f'📣 <a href="{CHANNEL_URL}">Новости и обновления</a>\n\n'
            "<i>Управление подпиской, QR-коды и VPN-конфигурации доступны в Mini App.</i>",
            parse_mode="HTML", reply_markup=user_menu(False))

    @router.message(Command("terms"))
    async def cmd_terms(message: Message):
        if TERMS_URL.startswith("https://"):
            msg = "<b>Условия Still VPN</b>\n\n" + html_escape(TERMS_URL)
        else:
            msg = "<b>Условия Still VPN</b>\n\nДокумент пока не опубликован. Новые платежи отключены."
        await message.answer(msg, parse_mode="HTML")

    @router.message(Command("paysupport"))
    async def cmd_paysupport(message: Message):
        await message.answer(
            "<b>Оплата и возвраты</b>\n\n"
            "Still VPN принимает Telegram Stars только после серверного подтверждения платежа.\n"
            "Если возникла проблема, отправьте /support и укажите ID платежа из раздела «Тарифы».\n\n"
            "<i>Не отправляйте пароли, ключи и банковские данные.</i>",
            parse_mode="HTML")

    @router.message(Command("support"))
    async def cmd_support(message: Message):
        await message.answer(
            "<b>STILL / ЦЕНТР ПОДДЕРЖКИ</b>\n\n"
            "Откройте Mini App, выберите тему, важность и опишите проблему. "
            "Все ответы и история переписки доступны там же.\n\n"
            "<i>Никому не отправляйте приватные ключи и пароли.</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✉ Открыть тикеты", web_app=WebAppInfo(url=mini_url("tickets")))
            ]]))

    @router.pre_checkout_query()
    async def pre_checkout(query: PreCheckoutQuery):
        payload = query.invoice_payload
        if not payload.startswith("shade:") or not payments_ready():
            await query.answer(ok=False, error_message="Оплата временно недоступна")
            return
        pid = payload[6:]
        async with Session() as s:
            p = await s.get(Payment, pid)
            active_server = await s.scalar(select(ServerNode.id).where(ServerNode.enabled.is_(True)).limit(1))
            valid = bool(active_server and p and p.user_id == query.from_user.id and p.status == "pending" and
                         p.amount == query.total_amount and query.currency == "XTR" and
                         (now() - p.created_at).total_seconds() < 3600)
            if valid and p.promo_id:
                reservation = await s.get(PromoReservation, p.id)
                valid = bool(reservation and reservation.status == "pending")
        await query.answer(ok=valid, error_message="Счёт устарел или недействителен" if not valid else None)

    @router.message(F.successful_payment)
    async def successful_payment(message: Message):
        sp = message.successful_payment
        if not message.from_user or not sp or sp.currency != "XTR" or not sp.invoice_payload.startswith("shade:"):
            return
        pid = sp.invoice_payload[6:]
        gift_code = None
        newly_paid = False
        async with Session.begin() as s:
            payment = await s.scalar(select(Payment).where(Payment.id == pid).with_for_update())
            if not payment or payment.user_id != message.from_user.id or payment.amount != sp.total_amount:
                LOG.error("Unmatched successful Telegram payment %s / charge %s", pid, sp.telegram_payment_charge_id)
                return
            if payment.status == "paid" and payment.telegram_charge_id == sp.telegram_payment_charge_id:
                return  # idempotent
            if payment.status not in ("pending", "expired"):
                LOG.error("Payment %s already in state %s", pid, payment.status)
                return
            known = await s.scalar(select(Payment).where(Payment.telegram_charge_id == sp.telegram_payment_charge_id))
            if known:
                LOG.error("Duplicate payment charge %s", sp.telegram_payment_charge_id)
                return
            payment.status = "paid"
            payment.paid_at = now()
            payment.telegram_charge_id = sp.telegram_payment_charge_id
            if payment.promo_id:
                promo = await s.get(Promo, payment.promo_id, with_for_update=True)
                reservation = await s.get(PromoReservation, payment.id, with_for_update=True)
                if reservation:
                    reservation.status = "applied"
                if promo:
                    prior_use = await s.scalar(select(PromoUse.id).where(
                        PromoUse.promo_id == promo.id, PromoUse.user_id == payment.user_id))
                    if not prior_use:
                        promo.uses += 1
                        s.add(PromoUse(promo_id=promo.id, user_id=payment.user_id))
                    else:
                        LOG.warning("Paid overlapping promo invoice for user %s", payment.user_id)
            user = await s.get(User, payment.user_id, with_for_update=True)
            if payment.kind == "subscription":
                await add_subscription(s, user, payment.plan_title, payment.days, payment.devices,
                                       payment.traffic_bytes, "payment", payment.id)
            else:
                if not fernet:
                    raise RuntimeError("GIFT_FERNET_KEY missing, cannot fulfill paid gift")
                gift_code = "STILL-" + secrets.token_urlsafe(20).replace("-", "A").replace("_", "B").upper()
                s.add(Gift(id=str(uuid.uuid4()), buyer_id=user.id, payment_id=payment.id,
                           code_hash=code_hash(gift_code), code_encrypted=fernet.encrypt(gift_code.encode()).decode(),
                           name=payment.plan_title, days=payment.days, devices=payment.devices,
                           traffic_bytes=payment.traffic_bytes, expires_at=now() + timedelta(days=90)))
            await queue_notice(s, user.id, "paid", payment.id, "✅ Оплата Still VPN подтверждена. " +
                               ("Подарок создан — заберите код в Mini App → Подарки." if payment.kind == "gift" else "Подписка активирована/продлена."))
            record_event(s, "stars_paid", user.id,
                         f"{payment.kind} · {payment.plan_title} · {payment.amount} Stars · заказ {payment.id}")
            newly_paid = True
        if newly_paid:
            await message.answer("<b>✦ STILL / ОПЛАТА ПРИНЯТА</b>\n━━━━━━━━━━━━━━━━━━\n\n"
                                 "Спасибо! Оплата подтверждена сервером Telegram.\n"
                                 "Твоя подписка готова в Mini App. ✨", parse_mode="HTML",
                                 reply_markup=user_menu(False))

    ADMIN_ROLES = {"owner", "administrator", "support", "finance", "viewer"}
    WRITERS = {"owner", "administrator"}
    ADMIN_PERMS = {
        "owner": {"stats", "users", "support", "plans", "servers", "finance", "audit", "staff", "settings"},
        "administrator": {"stats", "users", "support", "plans", "servers", "finance", "audit", "settings"},
        "support": {"users", "support"},
        "finance": {"stats", "finance"},
        "viewer": {"stats"},
    }
    def can(role: str | None, permission: str) -> bool:
        return bool(role and permission in ADMIN_PERMS.get(role, set()))

    async def dashboard_text(s: AsyncSession) -> str:
        users = await s.scalar(select(func.count()).select_from(User)) or 0
        subscriptions = await s.scalar(select(func.count()).select_from(Subscription).where(
            Subscription.ends_at > now(), Subscription.starts_at <= now(), Subscription.revoked.is_(False))) or 0
        expired = await s.scalar(select(func.count()).select_from(Subscription).where(
            Subscription.ends_at <= now(), Subscription.revoked.is_(False))) or 0
        trials = await s.scalar(select(func.count()).select_from(Trial).where(Trial.ends_at > now())) or 0
        devices = await s.scalar(select(func.count()).select_from(Device).where(Device.enabled.is_(True))) or 0
        payments = await s.scalar(select(func.count()).select_from(Payment).where(Payment.status == "paid")) or 0
        refunds = await s.scalar(select(func.count()).select_from(Payment).where(Payment.status == "refunded")) or 0
        stars = await s.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "paid")) or 0
        servers = await s.scalar(select(func.count()).select_from(ServerNode).where(ServerNode.enabled.is_(True))) or 0
        registrations = await s.scalar(select(func.count()).select_from(User).where(User.created_at >= now() - timedelta(days=1))) or 0
        live_nodes = await s.scalar(select(func.count()).select_from(NodeHealth).where(
            NodeHealth.last_seen >= now() - timedelta(minutes=3))) or 0
        tickets = await s.scalar(select(func.count()).select_from(Ticket).where(Ticket.status.in_(["open", "answered"]))) or 0
        return ("STILL VPN · Администрирование\n\n"
                "ПОЛЬЗОВАТЕЛИ\n"
                f"Всего: {users} · новых за 24 ч: {registrations}\n"
                f"Подписки: {subscriptions} активных, {expired} истёкших\n"
                f"Пробные периоды: {trials} активных\n"
                f"VPN-устройства: {devices}\n\n"
                "ИНФРАСТРУКТУРА\n"
                f"Серверы: {live_nodes}/{servers} отвечали за 3 минуты\n"
                f"Открытые обращения: {tickets}\n\n"
                "ПЛАТЕЖИ\n"
                f"Подтверждено: {payments} · возвраты: {refunds}\n"
                f"Получено Stars (без возвратов): {stars} ⭐\n\n"
                "Полные данные и управление — кнопка «Открыть админ-панель».")

    def admin_keyboard(role: str):
        lines = []
        if can(role, "stats") or can(role, "plans"):
            first = []
            if can(role, "stats"):
                first.append(InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats"))
            if can(role, "plans"):
                first.append(InlineKeyboardButton(text="💳 Тарифы", callback_data="adm:plans"))
            lines.append(first)
        if can(role, "support") or can(role, "servers"):
            second = []
            if can(role, "support"):
                second.append(InlineKeyboardButton(text="🆘 Обращения", callback_data="adm:tickets"))
            if can(role, "servers"):
                second.append(InlineKeyboardButton(text="🖥 Серверы", callback_data="adm:servers"))
            lines.append(second)
        lines.append([InlineKeyboardButton(text="Открыть админ-панель", web_app=WebAppInfo(url=mini_url("admin")))])
        lines.append([InlineKeyboardButton(text="🧾 Команды управления", callback_data="adm:help")])
        return InlineKeyboardMarkup(inline_keyboard=lines)

    ADMIN_HELP = (
        "Управление (все операции с журналом):\n"
        "/adm_plan 30 100 2 0 Название — создать тариф (дни, Stars, устройства, ГБ; 0=безлимит)\n"
        "/adm_plan_off ID — выключить тариф\n"
        "/adm_user TELEGRAM_ID — карточка пользователя\n"
        "/adm_give ID ДНИ УСТРОЙСТВА ГБ Причина — выдать подписку\n"
        "/adm_block ID Причина и /adm_unblock ID Причина\n"
        "/adm_revoke ID Причина — выключить все устройства пользователя\n"
        "/adm_reply TICKET_ID ответ — написать в поддержку\n"
        "/adm_close TICKET_ID — закрыть обращение\n"
        "/adm_refund PAYMENT_ID причина — возврат Stars\n"
        "/adm_promo ДНИ МАКС_АКТИВАЦИЙ ЧАСОВ_ДЕЙСТВИЯ — +дни\n"
        "/adm_promo_discount ПРОЦЕНТ МАКС_АКТИВАЦИЙ ЧАСОВ — скидка Stars\n"
        "/adm_promos и /adm_promo_off ID — список / блокировка\n"
        "/adm_trial on|off — включить/выключить пробный доступ\n"
        "/adm_staff ID ROLE — роли administrator/support/finance/viewer (только owner)\n"
        "/adm_audit — последние изменения\n"
        "/adm_user_subs ID, /adm_user_payments ID — подписки / история\n"
        "/adm_trial_users — история пробных периодов\n"
        "/adm_peer_list ID, /adm_peer_revoke UUID причина — устройства / отзыв\n"
        "/adm_server_status ID — живые CPU/RAM/диск/сеть/Peer\n"
        "/adm_diag — проверить БД, Telegram-настройки, VPN-агент и платежи\n"
        "/adm_server_edit ID LOCATION HOST:PORT — обновить местоположение и endpoint\n"
        "/adm_server_delete ID причина — удалить сервер без устройств\n"
        "/adm_plan_on ID — показать тариф\n"
        "/adm_claim ID — взять обращение\n"
        "/adm_staff_off ID — снять роль (только owner)\n"
        "/adm_maintenance ТЕКСТ — уведомить всех о работах (owner)\n"
        "/adm_trial_config ЧАСЫ ГБ УСТРОЙСТВА — настройка пробного доступа\n"
        "/adm_notice_hours 72 24 3 — часы уведомлений о завершении\n"
        "/adm_start_photo — ответьте на фото командой, чтобы поставить баннер /start (owner)\n"
        "/adm_start_photo_off — убрать баннер (owner)\n"
        "/adm_log_test — проверить доставку событий в группу (owner)\n"
        "/invite — своя реферальная ссылка\n"
        "/adm_plan_edit ID ДНИ STARS УСТРОЙСТВА ГБ Название — изменить будущие продажи\n"
        "/adm_find username — поиск\n"
        "/adm_ticket ID — история обращения\n"
        "/adm_payments и /adm_payment UUID — оплаты (finance)\n"
        "/adm_server_off ID и /adm_server_on ID — доступность локации\n"
        "Адрес первого VPN-сервера задаётся через окружение; новую локацию — /adm_server."
    )

    @router.message(Command("admin"))
    async def cmd_admin(message: Message):
        if not await require_role(message.from_user.id, ADMIN_ROLES):
            return
        async with Session.begin() as s:
            role = await role_of(s, message.from_user.id)
            audit(s, message.from_user.id, "admin_login", message.from_user.id, f"role={role}")
            if can(role, "stats"):
                txt = await dashboard_text(s)
            elif can(role, "support"):
                tickets = await s.scalar(select(func.count()).select_from(Ticket).where(Ticket.status.in_(["open", "answered"]))) or 0
                txt = f"STILL · Поддержка\nОткрытых обращений: {tickets}\nИспользуйте кнопки и /adm_reply."
            else:
                txt = "STILL · Доступ по роли " + str(role)
        await message.answer("<b>STILL / АДМИН-ПАНЕЛЬ</b>\n━━━━━━━━━━━━━━━━━━\n\n"
                             + "<pre>" + html_escape(txt[:3700]) + "</pre>",
                             parse_mode="HTML", reply_markup=admin_keyboard(role))

    @router.callback_query(F.data.startswith("adm:"))
    async def admin_callback(callback: CallbackQuery):
        if callback.message.chat.type != "private":
            await callback.answer("Только в личном чате", show_alert=True)
            return
        if not await require_role(callback.from_user.id, ADMIN_ROLES):
            await callback.answer("Нет доступа", show_alert=True)
            return
        action = callback.data[4:]
        requested = {"stats": "stats", "plans": "plans", "tickets": "support", "servers": "servers", "help": "stats"}.get(action)
        async with Session() as s:
            role = await role_of(s, callback.from_user.id)
            if not requested or (action != "help" and not can(role, requested)):
                await callback.answer("Недостаточно прав", show_alert=True)
                return
            if action == "stats":
                txt = await dashboard_text(s)
            elif action == "plans":
                plans = (await s.scalars(select(Plan).order_by(Plan.id))).all()
                txt = "Тарифы:\n" + "\n".join(f"#{p.id} {p.title}: {p.days}д, {p.stars}⭐, {p.devices} устр. {'✅' if p.enabled else '⛔'}" for p in plans)
            elif action == "tickets":
                tickets = (await s.scalars(select(Ticket).where(Ticket.status.in_(["open", "answered"])).order_by(Ticket.id.desc()).limit(15))).all()
                txt = "Обращения:\n" + "\n".join(
                    f"#{t.id} · Telegram {t.user_id} · ответственный: {t.assigned_admin or '—'}"
                    for t in tickets)
            elif action == "servers":
                nodes = (await s.scalars(select(ServerNode))).all()
                txt = "VPN-серверы:\n" + "\n".join(f"#{x.id} {x.location} ({x.endpoint}) {'✅' if x.enabled else '⛔'}" for x in nodes)
            else:
                txt = ADMIN_HELP
        await callback.message.answer("<b>STILL / " + html_escape(action.upper()) + "</b>\n"
                                      "━━━━━━━━━━━━━━━━━━\n\n<pre>" +
                                      html_escape(txt[:3600]) + "</pre>", parse_mode="HTML")
        await callback.answer()

    @router.message(Command("adm_user"))
    async def adm_user(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        try:
            uid = int(message.text.split()[1])
        except (ValueError, IndexError):
            await message.answer("Формат: /adm_user TELEGRAM_ID"); return
        async with Session() as s:
            user = await s.get(User, uid)
            if not user:
                await message.answer("Не найден"); return
            sub = await entitlement(s, user)
            device_count = await s.scalar(select(func.count()).select_from(Device).where(Device.user_id == uid, Device.enabled.is_(True)))
            trial = await s.get(Trial, uid)
            payments = await s.scalar(select(func.count()).select_from(Payment).where(Payment.user_id == uid)) or 0
            await message.answer(f"{uid} @{user.username}\nЗарегистрирован: {user.created_at:%d.%m.%Y}\n"
                                 f"Блокировка: {user.blocked}\nДоступ: {sub['name'] if sub else 'нет'}\n"
                                 f"Пробный использован: {trial is not None}\nУстройства: {device_count}\n"
                                 f"Платежей: {payments}\nТрафик всего: {user.traffic_bytes // (1024**2)} MiB")

    @router.message(Command("adm_plan"))
    async def adm_plan(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, days, price, devices, gb, *title = message.text.split()
            days, price, devices, gb = map(int, (days, price, devices, gb))
            assert 1 <= days <= 730 and 1 <= price <= 250000 and 1 <= devices <= 20 and 0 <= gb <= 100000
            assert title
        except (ValueError, AssertionError):
            await message.answer("Формат: /adm_plan 30 100 2 0 Месяц"); return
        async with Session.begin() as s:
            p = Plan(title=" ".join(title)[:120], days=days, stars=price, devices=devices,
                     traffic_bytes=gb * 1024**3 if gb else None)
            s.add(p); await s.flush()
            audit(s, message.from_user.id, "plan_create", p.id, message.text)
            pid = p.id
        await message.answer(f"Тариф #{pid} создан")

    @router.message(Command("adm_plan_edit"))
    async def adm_plan_edit(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, pid, days, stars, devices, gb, *title = message.text.split()
            pid, days, stars, devices, gb = map(int, (pid, days, stars, devices, gb))
            assert 1 <= days <= 730 and 1 <= stars <= 250000 and 1 <= devices <= 20 and 0 <= gb <= 100000 and title
        except (ValueError, AssertionError):
            await message.answer("/adm_plan_edit ID 30 100 2 0 Название"); return
        async with Session.begin() as s:
            p = await s.get(Plan, pid)
            if not p: await message.answer("Нет тарифа"); return
            p.title, p.days, p.stars, p.devices = " ".join(title)[:120], days, stars, devices
            p.traffic_bytes = gb * 1024**3 if gb else None
            audit(s, message.from_user.id, "plan_edit", pid, message.text)
        await message.answer("Изменены только будущие продажи; купленные параметры остаются прежними")

    @router.message(Command("adm_plan_off"))
    async def adm_plan_off(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try: pid = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.answer("/adm_plan_off ID"); return
        async with Session.begin() as s:
            p = await s.get(Plan, pid)
            if not p: await message.answer("Нет тарифа"); return
            p.enabled = False
            audit(s, message.from_user.id, "plan_disable", pid)
        await message.answer("Тариф скрыт (старые подписки не изменены)")

    @router.message(Command("adm_find"))
    async def adm_find(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        query = message.text.partition(" ")[2].strip().lstrip("@")[:80]
        if len(query) < 2: await message.answer("/adm_find username"); return
        async with Session() as s:
            rows = (await s.scalars(select(User).where(User.username.ilike("%" + query + "%")).limit(15))).all()
        await message.answer("Поиск:\n" + "\n".join(f"{x.id} @{x.username}" for x in rows))

    @router.message(Command("adm_give"))
    async def adm_give(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, uid, days, devices, gb, *reason = message.text.split()
            uid, days, devices, gb = map(int, (uid, days, devices, gb))
            assert 1 <= days <= 365 and 1 <= devices <= 20 and 0 <= gb <= 10000 and len(" ".join(reason)) >= 3
        except (ValueError, AssertionError):
            await message.answer("/adm_give ID ДНИ УСТРОЙСТВА ГБ Причина"); return
        async with Session.begin() as s:
            user = await s.get(User, uid, with_for_update=True)
            if not user: await message.answer("Пользователь не найден"); return
            sub = await add_subscription(s, user, "Выдано администратором", days, devices,
                                         gb * 1024**3 if gb else None, "admin")
            audit(s, message.from_user.id, "subscription_give", uid, " ".join(reason))
            await queue_notice(s, uid, "manual", str(sub.id), "Администратор выдал подписку Still VPN.")
        await message.answer("Подписка выдана")

    async def change_block(message: Message, blocked: bool):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, uid, *reason = message.text.split()
            uid = int(uid)
            assert len(" ".join(reason)) >= 3
        except (ValueError, AssertionError):
            await message.answer("Нужен ID и причина"); return
        async with Session.begin() as s:
            user = await s.get(User, uid, with_for_update=True)
            if not user: await message.answer("Пользователь не найден"); return
            user.blocked = blocked
            audit(s, message.from_user.id, "block" if blocked else "unblock", uid, " ".join(reason))
        async with Session.begin() as s: await ensure_access(s, uid)
        await message.answer("Изменено")

    @router.message(Command("adm_block"))
    async def adm_block(message: Message): await change_block(message, True)
    @router.message(Command("adm_unblock"))
    async def adm_unblock(message: Message): await change_block(message, False)

    @router.message(Command("adm_revoke"))
    async def adm_revoke(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, uid, *reason = message.text.split()
            uid = int(uid); assert len(" ".join(reason)) >= 3
        except (ValueError, AssertionError):
            await message.answer("/adm_revoke ID Причина"); return
        async with Session.begin() as s:
            await s.execute(update(Device).where(Device.user_id == uid).values(enabled=False))
            audit(s, message.from_user.id, "revoke_all_peers", uid, " ".join(reason))
        async with Session.begin() as s: await ensure_access(s, uid)
        await message.answer("Устройства отозваны")

    @router.message(Command("adm_trial"))
    async def adm_trial(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        val = message.text.split()[-1].lower()
        if val not in ("on", "off"):
            await message.answer("/adm_trial on|off"); return
        async with Session.begin() as s:
            st = await s.get(Setting, "trial_enabled")
            if st: st.value = "1" if val == "on" else "0"
            else: s.add(Setting(key="trial_enabled", value="1" if val == "on" else "0"))
            audit(s, message.from_user.id, "trial_toggle", val)
        await message.answer("Пробный доступ: " + val)

    @router.message(Command("adm_trial_config"))
    async def adm_trial_config(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, hours, gb, devices = message.text.split()
            hours, gb, devices = map(int, (hours, gb, devices))
            assert 1 <= hours <= 720 and 0 <= gb <= 10000 and 1 <= devices <= 20
        except (ValueError, AssertionError):
            await message.answer("/adm_trial_config ЧАСЫ ГБ УСТРОЙСТВА"); return
        async with Session.begin() as s:
            for key, val in {"trial_hours": hours, "trial_gb": gb, "trial_devices": devices}.items():
                st = await s.get(Setting, key)
                if st: st.value = str(val)
                else: s.add(Setting(key=key, value=str(val)))
            audit(s, message.from_user.id, "trial_config", "global", message.text)
        await message.answer("Новые пробные периоды используют новые ограничения")

    @router.message(Command("adm_promo"))
    async def adm_promo(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, days, max_uses, hours = message.text.split()
            days, max_uses, hours = map(int, (days, max_uses, hours))
            assert 1 <= days <= 365 and 1 <= max_uses <= 10000 and 1 <= hours <= 8760
        except (ValueError, AssertionError):
            await message.answer("/adm_promo ДНИ МАКС_АКТИВАЦИЙ ЧАСОВ_ДЕЙСТВИЯ"); return
        code = "SH-" + secrets.token_urlsafe(16).upper()
        async with Session.begin() as s:
            p = Promo(code_hash=code_hash(code), days=days, max_uses=max_uses,
                      expires_at=now() + timedelta(hours=hours), devices=1)
            s.add(p); await s.flush()
            audit(s, message.from_user.id, "promo_create", p.id, f"{days}days {max_uses}uses")
        await message.answer(f"Код (показывается один раз):\n<code>{code}</code>", parse_mode="HTML")

    @router.message(Command("adm_notice_hours"))
    async def adm_notice_hours(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            values = sorted({int(v) for v in message.text.split()[1:]}, reverse=True)
            assert 1 <= len(values) <= 5 and all(1 <= h <= 168 for h in values)
        except (ValueError, AssertionError):
            await message.answer("/adm_notice_hours 72 24 3 (1-5 значений от 1 до 168 ч)"); return
        async with Session.begin() as s:
            entry = await s.get(Setting, "notice_hours")
            val = ",".join(map(str, values))
            if entry: entry.value = val
            else: s.add(Setting(key="notice_hours", value=val))
            audit(s, message.from_user.id, "notice_hours", "service", val)
        await message.answer("Новые уведомления отправляются при порогах: " + ", ".join(map(str, values)))

    @router.message(Command("adm_promo_discount"))
    async def adm_promo_discount(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, percent, max_uses, hours = message.text.split()
            percent, max_uses, hours = map(int, (percent, max_uses, hours))
            assert 1 <= percent <= 95 and 1 <= max_uses <= 100000 and 1 <= hours <= 8760
        except (ValueError, AssertionError):
            await message.answer("/adm_promo_discount ПРОЦЕНТ МАКС_АКТИВАЦИЙ ЧАСОВ_ДЕЙСТВИЯ"); return
        code = "SHD-" + secrets.token_urlsafe(18).upper()
        async with Session.begin() as s:
            promo = Promo(code_hash=code_hash(code), days=0, discount_percent=percent,
                          max_uses=max_uses, expires_at=now() + timedelta(hours=hours))
            s.add(promo); await s.flush()
            audit(s, message.from_user.id, "promo_discount_create", promo.id, f"{percent}% {max_uses} uses")
        await message.answer(f"Скидочный код ({percent}%, показывается один раз):\n<code>{code}</code>", parse_mode="HTML")

    @router.message(Command("adm_promo_off"))
    async def adm_promo_off(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try: pid = int(message.text.split()[1])
        except (ValueError, IndexError): await message.answer("/adm_promo_off ID"); return
        async with Session.begin() as s:
            promo = await s.get(Promo, pid)
            if not promo: await message.answer("Не найден"); return
            promo.enabled = False
            audit(s, message.from_user.id, "promo_disable", pid)
        await message.answer("Промокод отключён для новых покупок и активаций")

    @router.message(Command("adm_promos"))
    async def adm_promos(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        async with Session() as s:
            items = (await s.scalars(select(Promo).order_by(Promo.id.desc()).limit(25))).all()
        await message.answer("Промокоды (коды не раскрываются):\n" + "\n".join(
            f"#{p.id} {'-' + str(p.discount_percent) + '%' if p.discount_percent else '+' + str(p.days) + 'д'} "
            f"{p.uses}/{p.max_uses}, до {p.expires_at:%d.%m.%Y}, {'вкл' if p.enabled else 'выкл'}"
            for p in items) or "Пусто")

    @router.message(Command("adm_staff"))
    async def adm_staff(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        try:
            _, uid, role = message.text.split()
            uid = int(uid); assert role in ADMIN_ROLES - {"owner"} and uid not in OWNER_IDS
        except (ValueError, AssertionError):
            await message.answer("/adm_staff ID administrator|support|finance|viewer"); return
        async with Session.begin() as s:
            a = await s.get(Admin, uid)
            if a: a.role = role
            else: s.add(Admin(user_id=uid, role=role))
            audit(s, message.from_user.id, "staff_role", uid, role)
        await message.answer("Роль назначена")

    @router.message(Command("adm_reply"))
    @router.message(Command("adm_ticket"))
    async def adm_ticket_redirect(message: Message):
        if not await require_role(message.from_user.id, ADMIN_ROLES): return
        await message.answer(
            "<b>STILL / ТИКЕТЫ</b>\n\nОтветы сотрудников доступны только в Mini App.",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Открыть обращения", web_app=WebAppInfo(url=mini_url("admin")))
            ]]))

    @router.message(Command("adm_payments"))
    async def adm_payments(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "finance"}): return
        async with Session() as s:
            pays = (await s.scalars(select(Payment).order_by(Payment.created_at.desc()).limit(15))).all()
        await message.answer("Платежи (полные ID для /adm_refund):\n" + "\n".join(
            f"{p.id}\n  {p.user_id} · {p.amount}⭐ · {p.status} · {p.plan_title}" for p in pays))

    @router.message(Command("adm_payment"))
    async def adm_payment(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "finance"}): return
        pid = message.text.partition(" ")[2].strip()
        if not pid: await message.answer("/adm_payment UUID"); return
        async with Session() as s:
            pay = await s.get(Payment, pid)
            if not pay: await message.answer("Платёж не найден"); return
            await message.answer(f"Платёж {pay.id}\nTelegram ID: {pay.user_id}\nТариф: {pay.plan_title}\n"
                                 f"Stars: {pay.amount}\nСтатус: {pay.status}\n"
                                 f"Создан: {pay.created_at:%d.%m.%Y %H:%M} UTC\n"
                                 f"Charge ID: {pay.telegram_charge_id or 'нет'}\n"
                                 f"Возврат: {pay.refunded_at or 'нет'}\n"
                                 f"Причина возврата: {pay.refund_reason or '—'}")

    @router.message(Command("adm_close"))
    async def adm_close_redirect(message: Message):
        if not await require_role(message.from_user.id, ADMIN_ROLES): return
        await message.answer("Закрытие и повторное открытие тикетов доступны только в Mini App.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                 InlineKeyboardButton(text="Открыть обращения", web_app=WebAppInfo(url=mini_url("admin")))
                             ]]))

    @router.message(Command("adm_refund"))
    async def adm_refund(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        try:
            _, pid, *reason_parts = message.text.split()
            reason = " ".join(reason_parts)
            assert len(reason) >= 3
        except (ValueError, AssertionError):
            await message.answer("/adm_refund PAYMENT_UUID причина"); return
        # 1. Persistent intent; crash afterward leaves review state, not a repeatable charge.
        async with Session.begin() as s:
            pay = await s.scalar(select(Payment).where(Payment.id == pid).with_for_update())
            if not pay or pay.status != "paid" or not pay.telegram_charge_id:
                await message.answer("Платёж не найден, не подтверждён, уже возвращён или в проверке"); return
            pay.status = "refund_processing"
            pay.refund_reason = reason[:3000]
            uid, charge_id = pay.user_id, pay.telegram_charge_id
            audit(s, message.from_user.id, "refund_requested", pid, reason)
        # 2. Telegram is the source of truth. Do not automatically retry ambiguous timeouts.
        try:
            confirmed = await bot.refund_star_payment(user_id=uid, telegram_payment_charge_id=charge_id)
            if confirmed is not True:
                raise RuntimeError("Bot API did not confirm refund")
        except Exception:
            LOG.exception("Refund status ambiguous, manual Telegram reconciliation needed: %s", pid)
            async with Session.begin() as s:
                pay = await s.get(Payment, pid, with_for_update=True)
                if pay and pay.status == "refund_processing": pay.status = "refund_review"
                audit(s, message.from_user.id, "refund_review", pid,
                      "Проверить возврат вручную в Telegram перед дальнейшими действиями")
            await message.answer("Возврат не подтверждён однозначно. Статус refund_review: проверьте транзакцию в Telegram и не повторяйте возврат вслепую.")
            return
        # 3. Revoke linked entitlements after Telegram confirmed refund.
        async with Session.begin() as s:
            pay = await s.get(Payment, pid, with_for_update=True)
            if not pay or pay.status != "refund_processing":
                raise RuntimeError("Refund was acknowledged but local payment state changed; operator action needed")
            pay.status = "refunded"
            pay.refunded_at = now()
            subs = (await s.scalars(select(Subscription).where(Subscription.payment_id == pid))).all()
            for sub in subs: sub.revoked = True
            gift = await s.scalar(select(Gift).where(Gift.payment_id == pid))
            if gift:
                gift.invalid = True
                if gift.subscription_id:
                    gifted = await s.get(Subscription, gift.subscription_id)
                    if gifted: gifted.revoked = True
            affected = {pay.user_id} | ({gift.used_by} if gift and gift.used_by else set())
            for affected_uid in affected:
                await compact_future_subscriptions(s, affected_uid)
            audit(s, message.from_user.id, "payment_refund_confirmed", pid, reason)
            await queue_notice(s, pay.user_id, "refund", pay.id,
                               f"Still VPN: подтверждён возврат {pay.amount} Stars по платежу {pay.id}.")
        # 4. Revoke VPN at once if available; worker retries if agent is down.
        for affected_uid in affected:
            async with Session.begin() as s:
                await ensure_access(s, affected_uid)
        await message.answer("Telegram подтвердил возврат. Подписки отозваны; WireGuard синхронизирован (или будет повторён воркером).")

    @router.message(Command("adm_audit"))
    async def adm_audit(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "viewer"}): return
        async with Session() as s:
            events = (await s.scalars(select(Audit).order_by(Audit.id.desc()).limit(15))).all()
        await message.answer("Журнал:\n" + "\n".join(f"{a.created_at:%d.%m %H:%M} / {a.admin_id}: {a.action} ({a.target})" for a in events))

    @router.message(Command("adm_server"))
    async def adm_server(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        try:
            _, location, endpoint, pubkey, cidr, agent_url = message.text.split()
            assert validate_wg_key(pubkey)
            assert ipaddress.ip_network(cidr, strict=True).version == 4
            assert urlparse(agent_url).scheme == "https" and urlparse(agent_url).hostname
            assert re.fullmatch(r"[A-Za-z0-9.\-]+:[0-9]{2,5}", endpoint)
        except (ValueError, AssertionError):
            await message.answer("/adm_server Локация host:51820 WG_PUBKEY 10.14.0.0/24 https://agent.example.org"); return
        async with Session.begin() as s:
            s.add(ServerNode(location=location[:80], endpoint=endpoint, public_key=pubkey,
                             cidr=cidr, agent_url=agent_url, next_host=2, enabled=False))
            audit(s, message.from_user.id, "server_add", location, endpoint)
        await message.answer("VPN-сервер добавлен, но выключен для новых устройств. "
                             "Настройте отдельный секрет для его ID в WG_AGENT_SECRETS на BotHost, "
                             "затем проверьте /adm_server_status ID и включите /adm_server_on ID.")

    async def change_server_enabled(message: Message, state: bool):
        if not await require_role(message.from_user.id, WRITERS): return
        try: node_id = int(message.text.split()[1])
        except (ValueError, IndexError):
            await message.answer("Укажите ID сервера"); return
        async with Session.begin() as s:
            node = await s.get(ServerNode, node_id)
            if not node: await message.answer("Не найдено"); return
            if state:
                try:
                    node_agent_secret(node)
                    await agent_request(node, "GET", "/agent/stats")
                except Exception as exc:
                    await message.answer("Нельзя включить: агент/секрет не подтверждён: " + str(exc)[:160]); return
            node.enabled = state
            audit(s, message.from_user.id, "server_enabled", node_id, str(state))
        await message.answer("Включен для новых устройств" if state else "Выключен для новых устройств")

    @router.message(Command("adm_server_off"))
    async def adm_server_off(message: Message): await change_server_enabled(message, False)
    @router.message(Command("adm_server_on"))
    async def adm_server_on(message: Message): await change_server_enabled(message, True)

    @router.message(Command("adm_user_subs"))
    async def adm_user_subs(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        try: uid = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_user_subs TELEGRAM_ID"); return
        async with Session() as s:
            rows = (await s.scalars(select(Subscription).where(Subscription.user_id == uid)
                                    .order_by(Subscription.id.desc()).limit(20))).all()
        await message.answer("Подписки:\n" + ("\n".join(
            f"#{x.id} {x.name} · {x.starts_at:%d.%m.%Y}—{x.ends_at:%d.%m.%Y} "
            f"{x.devices} устр., {'отозвана' if x.revoked else x.source}" for x in rows) or "Нет"))

    @router.message(Command("adm_user_payments"))
    async def adm_user_payments(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "finance"}): return
        try: uid = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_user_payments TELEGRAM_ID"); return
        async with Session() as s:
            rows = (await s.scalars(select(Payment).where(Payment.user_id == uid)
                                    .order_by(Payment.created_at.desc()).limit(20))).all()
        await message.answer("История платежей:\n" + ("\n".join(
            f"{x.id} {x.amount}⭐ {x.status} · {x.plan_title} ({x.created_at:%d.%m})" for x in rows) or "Нет"))

    @router.message(Command("adm_trial_users"))
    async def adm_trial_users(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        async with Session() as s:
            cnt = await s.scalar(select(func.count()).select_from(Trial)) or 0
            rows = (await s.scalars(select(Trial).order_by(Trial.started_at.desc()).limit(20))).all()
        await message.answer(f"Активировали пробный период всего: {cnt}\n" + "\n".join(
            f"{t.user_id} {t.started_at:%d.%m}—{t.ends_at:%d.%m}"
            for t in rows))

    @router.message(Command("adm_peer_list"))
    async def adm_peer_list(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        try: uid = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_peer_list TELEGRAM_ID"); return
        async with Session() as s:
            rows = (await s.scalars(select(Device).where(Device.user_id == uid)
                                    .order_by(Device.created_at.desc()).limit(25))).all()
        await message.answer("WireGuard Peer (UUID, адрес, состояние):\n" + ("\n".join(
            f"{x.id} · {x.name} · {x.peer_ip} · {'вкл' if x.enabled else 'отозван'} "
            f"· {'выдан' if x.provisioned else 'не выдан'}" for x in rows) or "Нет"))

    @router.message(Command("adm_peer_revoke"))
    async def adm_peer_revoke(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, device_id, *reason = message.text.split()
            uuid.UUID(device_id)
            assert len(" ".join(reason)) >= 3
        except (IndexError, ValueError, AssertionError):
            await message.answer("/adm_peer_revoke DEVICE_UUID причина"); return
        async with Session.begin() as s:
            d = await s.get(Device, device_id, with_for_update=True)
            if not d: await message.answer("Peer не найден"); return
            d.enabled = False
            uid = d.user_id
            audit(s, message.from_user.id, "peer_revoke", device_id, " ".join(reason))
        async with Session.begin() as s:
            await ensure_access(s, uid)
        await message.answer("Peer отозван (если агент недоступен, повторит воркер)")

    @router.message(Command("adm_diag"))
    async def adm_diag(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator"}):
            return
        lines = ["Still VPN · диагностика без изменения данных"]
        try:
            async with Session() as check:
                await check.execute(text("SELECT 1"))
                node = await check.get(ServerNode, 1)
            lines.append("База данных: OK")
        except Exception as exc:
            node = None
            lines.append("База данных: ошибка (" + type(exc).__name__ + ")")
        lines.append("Mini App HTTPS: " + ("OK" if WEBAPP_URL.startswith("https://") else "НЕ НАСТРОЕН"))
        lines.append("Платежи Stars: " + ("ГОТОВЫ К ТЕСТАМ" if payments_ready() else "ВЫКЛЮЧЕНЫ/НЕ ГОТОВЫ"))
        if node:
            try:
                stats = await agent_request(node, "GET", "/agent/stats")
                lines.append("VPN агент HTTPS/HMAC: OK")
                lines.append("Версия агента: " + str(stats.get("agent_version", "старая (<4)")))
                lines.append("Активных Peer: " + str(len(stats.get("peers", []))))
            except Exception as exc:
                lines.append("VPN агент: ошибка " + type(exc).__name__ + " — " + str(exc)[:100])
        else:
            lines.append("VPN сервер #1: отсутствует в БД")
        await message.answer("\n".join(lines))

    @router.message(Command("adm_server_status"))
    async def adm_server_status(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "viewer"}): return
        try: node_id = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_server_status SERVER_ID"); return
        async with Session() as s:
            node = await s.get(ServerNode, node_id)
            if not node: await message.answer("Сервер не найден"); return
            location = node.location
            health = await s.get(NodeHealth, node_id)
            last = health.last_seen.isoformat() if health and health.last_seen else "ещё нет измерений"
            try:
                stats = await agent_request(node, "GET", "/agent/stats")
                peer_count = len(stats.get("peers", []))
                mem = stats.get("memory") or {}
                memory = f"{(mem['MemTotal'] - mem['MemAvailable']) / 2**30:.2f} / {mem['MemTotal'] / 2**30:.2f} ГиБ" if "MemTotal" in mem and "MemAvailable" in mem else "нет данных"
                txt = (f"{location} · сервер #{node_id}\nСостояние: доступен\n"
                       f"WireGuard Peer: {peer_count}\nCPU: {stats.get('cpu_percent')!s}%\nRAM: {memory}\n"
                       f"Свободный диск: {stats.get('disk_free', 0)/2**30:.2f} ГиБ\n"
                       f"Сеть RX/TX: {stats.get('network_rx', 0)/2**20:.1f} / {stats.get('network_tx', 0)/2**20:.1f} МиБ")
            except Exception as exc:
                txt = f"{location} · сервер #{node_id}\nСостояние: ошибка связи\nПоследнее измерение: {last}\n{str(exc)[:100]}"
        await message.answer(txt)

    @router.message(Command("adm_server_edit"))
    async def adm_server_edit(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try:
            _, node_id, location, endpoint = message.text.split()
            node_id = int(node_id)
            assert 1 <= len(location) <= 80
            assert re.fullmatch(r"[A-Za-z0-9.\-]+:[0-9]{2,5}", endpoint)
        except (ValueError, AssertionError):
            await message.answer("/adm_server_edit ID LOCATION host:51820"); return
        async with Session.begin() as s:
            node = await s.get(ServerNode, node_id)
            if not node: await message.answer("Сервер не найден"); return
            node.location, node.endpoint = location, endpoint
            audit(s, message.from_user.id, "server_edit", node_id, f"{location} {endpoint}")
        await message.answer("Метаданные сервера изменены; Peer не затронуты")

    @router.message(Command("adm_server_delete"))
    async def adm_server_delete(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        try:
            _, node_id, *reason = message.text.split()
            node_id = int(node_id)
            assert len(" ".join(reason)) >= 3
        except (ValueError, AssertionError):
            await message.answer("/adm_server_delete ID причина"); return
        async with Session.begin() as s:
            node = await s.get(ServerNode, node_id, with_for_update=True)
            if not node: await message.answer("Сервер не найден"); return
            device_count = await s.scalar(select(func.count()).select_from(Device).where(Device.server_id == node_id))
            if device_count:
                await message.answer(f"Удаление запрещено: есть {device_count} привязанных устройств (включая отозванные). Выключите для новых подключений.")
                return
            await s.execute(delete(NodeHealth).where(NodeHealth.server_id == node_id))
            await s.delete(node)
            audit(s, message.from_user.id, "server_delete", node_id, " ".join(reason))
        await message.answer("Сервер удалён")

    @router.message(Command("adm_plan_on"))
    async def adm_plan_on(message: Message):
        if not await require_role(message.from_user.id, WRITERS): return
        try: pid = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_plan_on ID"); return
        async with Session.begin() as s:
            plan = await s.get(Plan, pid)
            if not plan: await message.answer("Не найден"); return
            plan.enabled = True
            audit(s, message.from_user.id, "plan_enable", pid)
        await message.answer("Тариф опубликован")

    @router.message(Command("adm_staff_off"))
    async def adm_staff_off(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        try:
            uid = int(message.text.split()[1]); assert uid not in OWNER_IDS
        except (IndexError, ValueError, AssertionError):
            await message.answer("/adm_staff_off TELEGRAM_ID"); return
        async with Session.begin() as s:
            await s.execute(delete(Admin).where(Admin.user_id == uid))
            audit(s, message.from_user.id, "staff_remove", uid)
        await message.answer("Роль сотрудника удалена")

    @router.message(Command("adm_claim"))
    async def adm_claim(message: Message):
        if not await require_role(message.from_user.id, {"owner", "administrator", "support"}): return
        try: tid = int(message.text.split()[1])
        except (IndexError, ValueError): await message.answer("/adm_claim TICKET_ID"); return
        async with Session.begin() as s:
            ticket = await s.get(Ticket, tid, with_for_update=True)
            if not ticket or ticket.status != "open": await message.answer("Обращение не открыто"); return
            if ticket.assigned_admin not in (None, message.from_user.id):
                await message.answer(f"Уже назначено сотруднику {ticket.assigned_admin}"); return
            ticket.assigned_admin = message.from_user.id
            audit(s, message.from_user.id, "ticket_claim", tid)
        await message.answer("Обращение назначено вам")

    @router.message(Command("adm_maintenance"))
    async def adm_maintenance(message: Message):
        if not await require_role(message.from_user.id, {"owner"}): return
        body = message.text.partition(" ")[2].strip()
        if not 10 <= len(body) <= 1500:
            await message.answer("/adm_maintenance Текст от 10 до 1500 символов"); return
        ref = str(uuid.uuid4())
        async with Session.begin() as s:
            rows = (await s.scalars(select(User.id))).all()
            for uid in rows:
                await queue_notice(s, uid, "maintenance", ref, "Still VPN · Работы: " + body)
            audit(s, message.from_user.id, "maintenance_broadcast", ref, f"recipients={len(rows)}")
        await message.answer(f"Уведомление поставлено в очередь для {len(rows)} пользователей")

    @router.message(F.text & ~F.text.startswith("/"))
    async def support_text(message: Message):
        # Do not silently turn every private text message into ticket content.
        await message.answer(
            "Чтобы обратиться в поддержку, откройте раздел «Тикеты» в Mini App. "
            "Ответить на тикет можно только там.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✉ Тикеты", web_app=WebAppInfo(url=mini_url("tickets")))
            ]]))

    # HTTP Mini App API
    app = FastAPI(title="Still VPN")
    rate: dict[str, tuple[float, int]] = {}

    async def current_user(req: Request, s: AsyncSession = Depends(db_session)) -> User:
        raw = req.headers.get("x-telegram-init-data", "")
        person = validate_init_data(raw)
        uid = person["id"]
        key = str(uid) + ":" + req.url.path
        if len(rate) > 10000:
            cutoff = time.monotonic() - 60
            for old_key, (started, _) in list(rate.items()):
                if started < cutoff:
                    rate.pop(old_key, None)
        t, n = rate.get(key, (time.monotonic(), 0))
        if time.monotonic() - t >= 60:
            t, n = time.monotonic(), 0
        if n >= 50: bad(429, "Слишком много запросов")
        rate[key] = (t, n + 1)
        user = await s.get(User, uid)
        if not user:
            bad(403, "Сначала отправьте боту /start")
        # Telegram initData is verified. Keep displayed identity current, including surname.
        if user.blocked:
            bad(403, "Аккаунт заблокирован. Обратитесь в поддержку.")
        user.username = (person.get("username") or "")[:128]
        user.first_name = (person.get("first_name") or "")[:200]
        user.last_name = (person.get("last_name") or "")[:200]
        # `get()` begins an implicit transaction. End it before write endpoints use s.begin().
        await s.commit()
        return user

    @app.middleware("http")
    async def security_headers(req: Request, call_next):
        response = await call_next(req)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        if req.url.path == "/" or req.url.path.startswith("/api/") or req.url.path.startswith("/web/api/"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if req.url.path == "/":
            # Telegram Web renders Mini Apps in an iframe; X-Frame-Options SAMEORIGIN would break it.
            inline_js = MINI_APP_HTML.rsplit("<script>", 1)[-1].split("</script>", 1)[0]
            js_digest = base64.b64encode(hashlib.sha256(inline_js.encode()).digest()).decode()
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src https://telegram.org https://cdnjs.cloudflare.com 'sha256-" + js_digest + "'; "
                "style-src 'unsafe-inline'; img-src data: blob:; connect-src 'self'; "
                "base-uri 'none'; object-src 'none'; "
                "frame-ancestors https://web.telegram.org https://*.telegram.org"
            )
        elif req.url.path.rstrip("/") == "/web":
            web_js = STILL_WEB_HTML.rsplit("<script>", 1)[-1].split("</script>", 1)[0]
            digest = base64.b64encode(hashlib.sha256(web_js.encode()).digest()).decode()
            # JSON-LD must be included in CSP hashes as well as the main inline script.
            schema_json = seo_public_html().split('<script type="application/ld+json">', 1)[1].split('</script>', 1)[0]
            schema_digest = base64.b64encode(hashlib.sha256(schema_json.encode()).digest()).decode()
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'sha256-" + digest + "' 'sha256-" + schema_digest + "'; "
                "style-src 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'; form-action 'self'; base-uri 'none'; "
                "object-src 'none'; frame-ancestors 'none'"
            )
            response.headers["X-Frame-Options"] = "DENY"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/health")
    async def health():
        async with Session() as check:
            await check.execute(text("SELECT 1"))
        return {"status": "ok", "component": "still-app", "database": "ok", "release": RELEASE}

    @app.get("/build")
    async def build_info():
        return {"release": RELEASE, "site": "/web", "mini_app": "/",
                "agent": "совместимо с WireGuard-агентом v4"}

    async def server_public_data(s: AsyncSession) -> list[dict]:
        nodes = (await s.scalars(select(ServerNode).where(
            ServerNode.enabled.is_(True)).order_by(ServerNode.id).limit(12))).all()
        result = []
        for n in nodes:
            h = await s.get(NodeHealth, n.id)
            healthy = bool(h and h.last_seen and h.last_seen > now() - timedelta(minutes=3)
                           and not h.error)
            loc = n.location if n.location and n.location.lower() not in ("primary", "main") else PUBLIC_SERVER_COUNTRY
            result.append({"id": n.id, "location": loc,
                           "country": PUBLIC_SERVER_COUNTRY if n.id == 1 else loc,
                           "provider": PUBLIC_SERVER_PROVIDER if n.id == 1 else "VPN-узел",
                           "protocol": "WireGuard", "status": "online" if healthy else "checking"})
        return result

    @app.get("/api/servers/public")
    async def public_servers(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        return await server_public_data(s)

    @app.get("/api/referrals")
    async def referral_summary(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        count = await s.scalar(select(func.count()).select_from(Referral).where(
            Referral.inviter_id == user.id)) or 0
        paid = await s.scalar(select(func.count(func.distinct(Referral.invitee_id))).select_from(Referral).join(
            Payment, Payment.user_id == Referral.invitee_id).where(
            Referral.inviter_id == user.id, Payment.status == "paid", Payment.kind == "subscription")) or 0
        return {"link": invite_link(user.id) if user.id > 0 else None,
                "registered": count, "paid": paid, "rewards_enabled": False}

    @app.get("/api/me")
    async def api_me(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        e = await entitlement(s, user)
        count = await s.scalar(select(func.count()).select_from(Device).where(
            Device.user_id == user.id, Device.enabled.is_(True)))
        tr = await s.get(Trial, user.id)
        enabled_nodes = await s.scalar(select(func.count()).select_from(ServerNode).where(ServerNode.enabled.is_(True))) or 0
        responsive_nodes = await s.scalar(select(func.count()).select_from(NodeHealth).join(
            ServerNode, NodeHealth.server_id == ServerNode.id).where(
            ServerNode.enabled.is_(True), NodeHealth.last_seen >= now() - timedelta(minutes=3))) or 0
        return {"service": {"enabled_nodes": enabled_nodes, "responsive_nodes": responsive_nodes},
                "account_status": "active" if not user.blocked else "blocked",
                "id": user.id, "username": user.username, "first_name": user.first_name,
                "created_at": user.created_at, "traffic_total": user.traffic_bytes,
                "device_count": count, "trial_used": tr is not None,
                "subscription": e and {**e, "end": e["end"].isoformat()},
                "payments_enabled": payments_ready(),
                "admin_role": await role_of(s, user.id), "release": RELEASE,
                "site_url": WEBAPP_URL + "/web", "channel_url": CHANNEL_URL}

    @app.get("/api/plans")
    async def api_plans(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        plans = (await s.scalars(select(Plan).where(Plan.enabled.is_(True)).order_by(Plan.days))).all()
        return [{"id": p.id, "title": p.title, "days": p.days, "stars": p.stars,
                 "devices": p.devices, "traffic_bytes": p.traffic_bytes} for p in plans]

    @app.post("/api/trial")
    async def api_trial(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        node = await s.scalar(select(ServerNode).where(ServerNode.enabled.is_(True)).limit(1))
        if not node: bad(503, "VPN-сервер пока не настроен")
        try:
            await agent_request(node, "GET", "/agent/stats")
        except Exception:
            bad(503, "VPN-сервер временно недоступен; пробный период не активирован")
        await s.commit()
        async with s.begin():
            u = await s.get(User, user.id, with_for_update=True)
            if await setting(s, "trial_enabled", "1") != "1": bad(403, "Пробный доступ выключен")
            if await s.get(Trial, u.id): bad(409, "Пробный период уже использован")
            if await s.scalar(select(Subscription.id).where(Subscription.user_id == u.id).limit(1)):
                bad(409, "Для аккаунта уже оформлялась подписка")
            hours = int(await setting(s, "trial_hours", "24"))
            gb = int(await setting(s, "trial_gb", "1"))
            max_devices = int(await setting(s, "trial_devices", "1"))
            t = Trial(user_id=u.id, started_at=now(), ends_at=now() + timedelta(hours=hours),
                      baseline_bytes=u.traffic_bytes, traffic_bytes=gb * 1024**3 if gb else None,
                      devices=max_devices)
            s.add(t)
            record_event(s, "trial_started", u.id, f"Пробник: {hours} ч · {gb} ГБ · {max_devices} устройств")
            await queue_notice(s, u.id, "trial", str(u.id), f"Пробный Still VPN активирован на {hours} ч.")
        return {"ok": True}

    class InvoiceIn(BaseModel):
        plan_id: int
        kind: str = "subscription"
        promo_code: str | None = Field(default=None, max_length=80)

    @app.post("/api/invoice")
    async def api_invoice(data: InvoiceIn, user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        if not payments_ready():
            bad(503, "Оплата ещё не настроена администратором")
        if data.kind not in ("subscription", "gift"):
            bad(422, "Неизвестный тип покупки")
        node = await s.scalar(select(ServerNode).where(ServerNode.enabled.is_(True)).limit(1))
        if not node: bad(503, "VPN-сервер не настроен; оплата недоступна")
        try:
            await agent_request(node, "GET", "/agent/stats")
        except Exception:
            bad(503, "VPN-сервер временно недоступен; оплата отключена")
        await s.commit()
        pid = str(uuid.uuid4())
        async with s.begin():
            plan = await s.scalar(select(Plan).where(Plan.id == data.plan_id).with_for_update(read=True))
            if not plan or not plan.enabled: bad(404, "Тариф не найден")
            promo_id = None
            amount = plan.stars
            if data.promo_code:
                promo = await s.scalar(select(Promo).where(
                    Promo.code_hash == code_hash(data.promo_code.strip().upper())).with_for_update())
                if not promo or not promo.enabled or not promo.discount_percent or promo.expires_at <= now():
                    bad(409, "Скидочный промокод недоступен")
                if await s.scalar(select(PromoUse.id).where(PromoUse.promo_id == promo.id,
                                                            PromoUse.user_id == user.id)):
                    bad(409, "Вы уже использовали этот промокод")
                reserved = await s.scalar(select(func.count()).select_from(PromoReservation).where(
                    PromoReservation.promo_id == promo.id,
                    PromoReservation.status == "pending",
                    PromoReservation.created_at > now() - timedelta(hours=1))) or 0
                previous_pending = await s.scalar(select(PromoReservation).where(
                    PromoReservation.promo_id == promo.id,
                    PromoReservation.user_id == user.id,
                    PromoReservation.status == "pending",
                    PromoReservation.created_at > now() - timedelta(hours=1)))
                if previous_pending:
                    bad(409, "У вас уже есть неоплаченный счёт с этим промокодом; дождитесь истечения часа")
                if promo.uses + reserved >= promo.max_uses:
                    bad(409, "Промокод полностью использован")
                promo_id = promo.id
                amount = max(1, (plan.stars * (100 - promo.discount_percent) + 99) // 100)
            s.add(Payment(id=pid, user_id=user.id, kind=data.kind, plan_id=plan.id,
                          plan_title=plan.title, days=plan.days, devices=plan.devices,
                          traffic_bytes=plan.traffic_bytes, amount=amount, promo_id=promo_id))
            if promo_id:
                s.add(PromoReservation(payment_id=pid, promo_id=promo_id, user_id=user.id))
            title, days = plan.title, plan.days
        try:
            link = await bot.create_invoice_link(
                title=f"Still VPN · {title}"[:32],
                description=("Подарочный код" if data.kind == "gift" else f"Подписка на {days} дней"),
                payload="shade:" + pid, currency="XTR",
                prices=[LabeledPrice(label=title[:32], amount=amount)])
        except Exception:
            LOG.exception("Failed to create Stars invoice")
            # Mark failed invoice as unusable to avoid orphaned discount reservations.
            async with Session.begin() as fail_session:
                payment = await fail_session.get(Payment, pid)
                if payment and payment.status == "pending": payment.status = "invoice_error"
                reservation = await fail_session.get(PromoReservation, pid)
                if reservation: reservation.status = "released"
            bad(502, "Не удалось создать счёт Telegram")
        return {"url": link, "payment_id": pid, "amount": amount}

    @app.get("/api/payments")
    async def api_payments(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        rows = (await s.scalars(select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(50))).all()
        return [{"id": x.id, "date": x.created_at, "plan": x.plan_title,
                 "amount": x.amount, "kind": x.kind, "status": x.status,
                 "charge_id": x.telegram_charge_id} for x in rows]

    @app.get("/api/gifts")
    async def api_gifts(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        rows = (await s.scalars(select(Gift).where(Gift.buyer_id == user.id).order_by(Gift.expires_at.desc()))).all()
        result = []
        for x in rows:
            code = None
            if fernet and not x.invalid and not x.used_by:
                try:
                    code = fernet.decrypt(x.code_encrypted.encode()).decode()
                except Exception:
                    # Wrong/rotated key must not cause a 500 for the whole profile.
                    LOG.error("Gift %s decrypt failed: restore original GIFT_FERNET_KEY", x.id)
            result.append({"id": x.id, "name": x.name, "code": code,
                           "expires_at": x.expires_at, "used": bool(x.used_by), "invalid": x.invalid})
        return result

    class RedeemIn(BaseModel):
        code: str = Field(min_length=8, max_length=80)

    @app.post("/api/redeem")
    async def api_redeem(data: RedeemIn, user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        code = data.code.strip().upper()
        h = code_hash(code)
        async with s.begin():
            u = await s.get(User, user.id, with_for_update=True)
            gift = await s.scalar(select(Gift).where(Gift.code_hash == h).with_for_update())
            if gift:
                if gift.invalid or gift.used_by is not None or gift.expires_at <= now():
                    bad(409, "Подарок использован или истёк")
                if gift.buyer_id == u.id:
                    bad(409, "Нельзя активировать собственный подарок")
                gift.used_by = u.id; gift.used_at = now()
                redeemed = await add_subscription(s, u, gift.name, gift.days, gift.devices, gift.traffic_bytes, "gift")
                gift.subscription_id = redeemed.id
                return {"ok": True, "days": gift.days, "source": "gift"}
            promo = await s.scalar(select(Promo).where(Promo.code_hash == h).with_for_update())
            if not promo or not promo.enabled or promo.expires_at <= now() or promo.uses >= promo.max_uses:
                bad(404, "Код не найден или больше недействителен")
            if promo.discount_percent or promo.days <= 0:
                bad(409, "Это скидочный промокод. Введите его при покупке тарифа.")
            already = await s.scalar(select(PromoUse).where(PromoUse.promo_id == promo.id, PromoUse.user_id == u.id))
            if already: bad(409, "Промокод уже использован")
            promo.uses += 1
            s.add(PromoUse(promo_id=promo.id, user_id=u.id))
            await add_subscription(s, u, "Промокод", promo.days, promo.devices, None, "promo")
            return {"ok": True, "days": promo.days, "source": "promo"}

    @app.get("/api/devices")
    async def api_devices(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        rows = (await s.scalars(select(Device).where(Device.user_id == user.id)
                                                       .order_by(Device.created_at.desc()).limit(100))).all()
        return [{"id": d.id, "name": d.name, "platform": d.platform,
                 "created_at": d.created_at, "last_handshake": d.last_handshake,
                 "provisioned": d.provisioned, "enabled": d.enabled} for d in rows]

    class DeviceIn(BaseModel):
        name: str = Field(min_length=1, max_length=60)
        platform: str
        public_key: str

    @app.post("/api/devices")
    async def api_add_device(data: DeviceIn, user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        if data.platform not in ("android", "ios", "windows", "macos", "linux"):
            bad(422, "Некорректная платформа")
        if not validate_wg_key(data.public_key): bad(422, "Некорректный публичный WireGuard-ключ")
        if not re.fullmatch(r"[\w\- .А-Яа-яЁё]{1,60}", data.name, re.UNICODE):
            bad(422, "Некорректное имя")
        async with s.begin():
            u = await s.get(User, user.id, with_for_update=True)
            entitlement_data = await entitlement(s, u)
            if not entitlement_data: bad(403, "Нет активного доступа")
            used = await s.scalar(select(func.count()).select_from(Device).where(
                Device.user_id == u.id, Device.enabled.is_(True)))
            if used >= entitlement_data["devices"]:
                bad(409, "Достигнут лимит устройств")
            existing = await s.scalar(select(Device).where(Device.public_key == data.public_key))
            if existing: bad(409, "Этот ключ уже зарегистрирован")
            node = await s.scalar(select(ServerNode).where(ServerNode.enabled.is_(True)).order_by(ServerNode.id).with_for_update())
            if not node: bad(503, "VPN-сервер пока не настроен")
            subnet = ipaddress.ip_network(node.cidr)
            next_ip = int(subnet.network_address) + node.next_host
            if next_ip >= int(subnet.broadcast_address): bad(503, "Адреса VPN закончились")
            peer_ip = str(ipaddress.ip_address(next_ip))
            node.next_host += 1
            d = Device(id=str(uuid.uuid4()), user_id=u.id, server_id=node.id, name=data.name,
                       platform=data.platform, public_key=data.public_key, peer_ip=peer_ip)
            s.add(d)
            record_event(s, "device_created", u.id,
                         f"{d.name} · {d.platform} · {peer_ip} · сервер #{node.id}")
            await s.flush()
            response = {"id": d.id, "address": peer_ip + "/32", "dns": "1.1.1.1",
                        "server_key": node.public_key, "endpoint": node.endpoint,
                        "status": "provisioning"}
        try:
            await apply_peer(d, node, True, entitlement_data["end"])
            async with Session.begin() as s2:
                created = await s2.get(Device, d.id)
                if created: created.provisioned = True
            response["status"] = "ready"
        except Exception:
            LOG.exception("Provisioning failed for device %s; background task will retry", d.id)
        return response

    class ConfToTelegramIn(BaseModel):
        # Only the WireGuard private key is accepted: server rebuilds the rest from trusted DB values.
        private_key: str = Field(min_length=44, max_length=44, pattern=r"^[A-Za-z0-9+/]{43}=$")

    conf_send_rate: dict[int, list[float]] = {}

    async def deliver_conf_to_telegram(
        device_id: str, data: ConfToTelegramIn, user: User, session: AsyncSession
    ) -> dict[str, bool]:
        """Secure one-time user-requested delivery; never persist or log a private key."""
        if user.id <= 0:
            bad(403, "Сначала привяжите Telegram к веб-аккаунту через /linkweb")
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", device_id):
            bad(404, "Устройство не найдено")
        dev = await session.get(Device, device_id)
        if not dev or dev.user_id != user.id or not dev.enabled:
            bad(404, "Активное устройство не найдено")
        if not dev.provisioned:
            bad(409, "Устройство ещё не подтверждено VPN-сервером")
        if not await entitlement(session, user):
            bad(403, "Для отправки профиля нужен активный VPN-доступ")
        node = await session.get(ServerNode, dev.server_id)
        if not node or not node.enabled:
            bad(503, "VPN-сервер сейчас недоступен")
        try:
            secret_bytes = base64.b64decode(data.private_key, validate=True)
            if len(secret_bytes) != 32:
                raise ValueError("invalid key length")
            derived = base64.b64encode(X25519PrivateKey.from_private_bytes(
                secret_bytes).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            ).decode("ascii")
        except Exception:
            bad(422, "Некорректный приватный ключ WireGuard")
        if not hmac.compare_digest(derived, dev.public_key):
            bad(422, "Ключ не соответствует выбранному устройству")
        # Enforce strict rate limit for sending secret-bearing documents to Telegram.
        tick = time.monotonic()
        if len(conf_send_rate) > 10000:
            for uid, events in list(conf_send_rate.items()):
                if not events or events[-1] < tick - 3600:
                    conf_send_rate.pop(uid, None)
        recent = [x for x in conf_send_rate.get(user.id, []) if x > tick - 3600]
        if len(recent) >= 6:
            bad(429, "Лимит отправок: максимум 6 профилей в час")
        conf_send_rate[user.id] = recent + [tick]
        config = (
            "[Interface]\n"
            f"PrivateKey = {data.private_key}\n"
            f"Address = {dev.peer_ip}/32\n"
            "DNS = 1.1.1.1\n"
            "MTU = 1280\n\n"
            "[Peer]\n"
            f"PublicKey = {node.public_key}\n"
            f"Endpoint = {node.endpoint}\n"
            "AllowedIPs = 0.0.0.0/0\n"
            "PersistentKeepalive = 25\n"
        )
        filename = "still-" + dev.id[:8] + ".conf"
        try:
            await bot.send_document(
                chat_id=user.id,
                document=BufferedInputFile(config.encode("utf-8"), filename=filename),
                caption=("🔐 <b>Still VPN · конфигурация</b>\n"
                         "Откройте файл в WireGuard и включите туннель.\n"
                         "⚠️ Файл содержит приватный ключ: не пересылайте его другим."),
                parse_mode="HTML",
                # Keep downloading enabled: protected Telegram messages can prevent file saving.
                protect_content=False,
            )
        except TelegramAPIError:
            bad(409, "Не удалось отправить файл. Откройте личный чат с ботом, нажмите /start и повторите. Если бот заблокирован, разблокируйте его.")
        # Event contains only public metadata; never include private key or full config.
        try:
            async with Session.begin() as audit_session:
                record_event(audit_session, "config_sent_to_owner", user.id,
                             f"Личный чат · устройство {dev.id[:8]} · {dev.platform}")
        except Exception:
            LOG.warning("Failed to audit configuration delivery, id=%s", dev.id[:8])
        return {"ok": True, "sent": True}

    @app.post("/api/devices/{device_id}/send-conf")
    async def api_send_conf(device_id: str, data: ConfToTelegramIn,
                            user: User = Depends(current_user),
                            session: AsyncSession = Depends(db_session)):
        return await deliver_conf_to_telegram(device_id, data, user, session)

    @app.delete("/api/devices/{device_id}")
    async def api_delete_device(device_id: str, user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        async with s.begin():
            d = await s.get(Device, device_id)
            if not d or d.user_id != user.id: bad(404, "Устройство не найдено")
            d.enabled = False
            record_event(s, "device_revoked", user.id, f"{d.name} · {d.peer_ip}")
            node = await s.get(ServerNode, d.server_id)
        try:
            await apply_peer(d, node, False)
            async with Session.begin() as s2:
                found = await s2.get(Device, d.id)
                if found: found.provisioned = False
        except Exception:
            LOG.exception("Peer revoke will be retried by background task")
        return {"ok": True, "status": "revocation_pending"}

    class RenameIn(BaseModel):
        name: str = Field(min_length=1, max_length=60)

    @app.patch("/api/devices/{device_id}")
    async def api_rename(device_id: str, data: RenameIn, user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        if not re.fullmatch(r"[\w\- .А-Яа-яЁё]{1,60}", data.name, re.UNICODE):
            bad(422, "Некорректное имя")
        async with s.begin():
            d = await s.get(Device, device_id)
            if not d or d.user_id != user.id or not d.enabled: bad(404, "Нет устройства")
            d.name = data.name
        return {"ok": True}

    # Administrative Mini App API. No admin endpoint trusts a role from the browser;
    # role/permission is resolved from the authenticated Telegram ID on every request.
    def admin_scope(permission: str):
        async def check(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
            role = await role_of(s, user.id)
            if role not in ADMIN_ROLES or (permission != "access" and not can(role, permission)):
                bad(403, "Недостаточно прав для этого раздела")
            return (user.id, role)
        return check

    def dt_iso(v):
        return v.isoformat() if v else None

    class AdminReason(BaseModel):
        reason: str = Field(min_length=3, max_length=500)

    class AdminBlock(AdminReason):
        blocked: bool

    class AdminGrant(AdminReason):
        days: int = Field(ge=1, le=365)
        devices: int = Field(ge=1, le=20)
        traffic_gb: int = Field(ge=0, le=10000, default=0)

    class AdminPlanData(BaseModel):
        title: str = Field(min_length=2, max_length=120)
        days: int = Field(ge=1, le=3650)
        stars: int = Field(ge=1, le=250000)
        devices: int = Field(ge=1, le=20)
        traffic_gb: int = Field(ge=0, le=10000, default=0)
        enabled: bool = True

    class AdminServerState(AdminReason):
        enabled: bool

    class AdminReply(BaseModel):
        text: str = Field(min_length=1, max_length=3500)

    class AdminTrialSettings(BaseModel):
        enabled: bool
        hours: int = Field(ge=1, le=720)
        traffic_gb: int = Field(ge=0, le=10000)
        devices: int = Field(ge=1, le=20)

    class AdminStaffRole(AdminReason):
        role: str

    class AdminTrialShorten(AdminReason):
        # 0 = expire now; 5 = expire no later than five minutes from now.
        # Never extend an already earlier expiry.
        remaining_minutes: int = Field(ge=0, le=1440)

    def plan_dict(p: Plan):
        return {"id": p.id, "title": p.title, "days": p.days, "stars": p.stars,
                "devices": p.devices, "traffic_gb": (p.traffic_bytes // 1024**3 if p.traffic_bytes else 0),
                "enabled": p.enabled}

    @app.get("/api/admin/summary")
    async def admin_summary(actor=Depends(admin_scope("access")), s: AsyncSession = Depends(db_session)):
        uid, role = actor
        output = {"role": role, "permissions": sorted(ADMIN_PERMS.get(role, set()))}
        if can(role, "stats"):
            output["stats"] = {
                "users": await s.scalar(select(func.count()).select_from(User)) or 0,
                "new_users": await s.scalar(select(func.count()).select_from(User).where(User.created_at >= now()-timedelta(days=1))) or 0,
                "subscriptions": await s.scalar(select(func.count()).select_from(Subscription).where(
                    Subscription.starts_at <= now(), Subscription.ends_at > now(), Subscription.revoked.is_(False))) or 0,
                "trials": await s.scalar(select(func.count()).select_from(Trial).where(Trial.ends_at > now())) or 0,
                "devices": await s.scalar(select(func.count()).select_from(Device).where(Device.enabled.is_(True))) or 0,
                "servers": await s.scalar(select(func.count()).select_from(ServerNode).where(ServerNode.enabled.is_(True))) or 0,
                "healthy_servers": await s.scalar(select(func.count()).select_from(NodeHealth).join(
                    ServerNode, NodeHealth.server_id == ServerNode.id).where(
                    ServerNode.enabled.is_(True), NodeHealth.last_seen >= now()-timedelta(minutes=3))) or 0,
                "expired_subs": await s.scalar(select(func.count()).select_from(Subscription).where(
                    Subscription.ends_at <= now(), Subscription.revoked.is_(False))) or 0,
                "tickets": await s.scalar(select(func.count()).select_from(Ticket).where(Ticket.status.in_(["open", "answered"]))) or 0,
            }
        if can(role, "finance"):
            output["finance"] = {
                "payments": await s.scalar(select(func.count()).select_from(Payment).where(Payment.status == "paid")) or 0,
                "stars": await s.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.status == "paid")) or 0,
                "refunds": await s.scalar(select(func.count()).select_from(Payment).where(Payment.status == "refunded")) or 0,
            }
        if can(role, "support") and "stats" not in output:
            output["support"] = {"open_tickets": await s.scalar(select(func.count()).select_from(Ticket).where(Ticket.status.in_(["open", "answered"]))) or 0}
        if can(role, "audit"):
            events = (await s.scalars(select(Audit).order_by(Audit.id.desc()).limit(8))).all()
            output["events"] = [{"date": dt_iso(x.created_at), "action": x.action, "target": x.target,
                                 "admin_id": x.admin_id} for x in events]
        return output

    @app.get("/api/admin/users")
    async def admin_users(q: str = "", actor=Depends(admin_scope("users")), s: AsyncSession = Depends(db_session)):
        q = q.strip().lstrip("@")[:80]
        stmt = select(User)
        if q:
            stmt = stmt.where(User.id == int(q)) if q.isdigit() else stmt.where(User.username.ilike("%" + q + "%"))
        rows = (await s.scalars(stmt.order_by(User.created_at.desc()).limit(30))).all()
        return [{"id": u.id, "username": u.username, "first_name": u.first_name,
                 "blocked": u.blocked, "created_at": dt_iso(u.created_at)} for u in rows]

    @app.get("/api/admin/users/{user_id}")
    async def admin_user_detail(user_id: int, actor=Depends(admin_scope("users")), s: AsyncSession = Depends(db_session)):
        u = await s.get(User, user_id)
        if not u: bad(404, "Пользователь не найден")
        subscriptions = (await s.scalars(select(Subscription).where(Subscription.user_id == user_id)
                                          .order_by(Subscription.id.desc()).limit(30))).all()
        devices = (await s.scalars(select(Device).where(Device.user_id == user_id)
                                    .order_by(Device.created_at.desc()).limit(50))).all()
        tr = await s.get(Trial, user_id)
        output = {"id": u.id, "username": u.username, "first_name": u.first_name,
                  "created_at": dt_iso(u.created_at), "blocked": u.blocked,
                  "trial": ({"starts_at": dt_iso(tr.started_at), "ends_at": dt_iso(tr.ends_at)} if tr else None),
                  "subscriptions": [{"id": x.id,"name":x.name,"starts_at":dt_iso(x.starts_at),
                                     "ends_at":dt_iso(x.ends_at),"revoked":x.revoked,"source":x.source} for x in subscriptions],
                  "devices": [{"id":x.id,"name":x.name,"ip":x.peer_ip,"enabled":x.enabled,
                               "provisioned":x.provisioned,"last_handshake":dt_iso(x.last_handshake)} for x in devices]}
        if can(actor[1], "finance"):
            pays = (await s.scalars(select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc()).limit(20))).all()
            output["payments"] = [{"id":p.id,"amount":p.amount,"status":p.status} for p in pays]
        return output

    @app.post("/api/admin/users/{user_id}/trial/shorten")
    async def admin_trial_shorten(
        user_id: int,
        data: AdminTrialShorten,
        actor=Depends(admin_scope("users")),
    ):
        # Test-only administrative control: owner, explicit audit reason, only shorten.
        admin_id, role = actor
        if role != "owner":
            bad(403, "Завершить действующий пробный период может только владелец")
        if len(data.reason.strip()) < 5:
            bad(422, "Укажите причину не короче 5 символов")
        async with Session.begin() as s:
            tr = await s.get(Trial, user_id, with_for_update=True)
            if tr is None:
                bad(404, "Пробный период пользователя не найден")
            old_end = tr.ends_at
            if old_end <= now():
                bad(409, "Пробный период уже завершён")
            target_end = now() + timedelta(minutes=data.remaining_minutes)
            tr.ends_at = min(old_end, target_end)
            if data.remaining_minutes == 0:
                # Ensure it is strictly expired even with timestamp rounding.
                tr.ends_at = min(tr.ends_at, now() - timedelta(seconds=1))
            audit(s, admin_id, "trial_shortened", user_id,
                  f"old={old_end.isoformat()}; new={tr.ends_at.isoformat()}; "
                  f"remaining_minutes={data.remaining_minutes}; reason={data.reason.strip()}")
            if data.remaining_minutes == 0 and user_id > 0:
                await queue_notice(s, user_id, "trial_admin_expired", str(int(now().timestamp())),
                                   "Still VPN: ваш пробный доступ завершён администрацией.")
            new_end = tr.ends_at
        # A failed network request must never undo the earlier committed expiry.
        # The periodic worker / agent's short-lived lease will reconcile/revoke it.
        async with Session.begin() as s:
            await ensure_access(s, user_id)
        return {"ok": True, "ends_at": dt_iso(new_end),
                "note": "Проверьте удаление Peer на SKRIME. Платная подписка, если есть, продолжит действовать."}

    @app.post("/api/admin/users/{user_id}/block")
    async def admin_user_block(user_id: int, data: AdminBlock, actor=Depends(admin_scope("users"))):
        admin_id, role = actor
        if role not in WRITERS: bad(403, "Блокировки разрешены только управляющим")
        if user_id in OWNER_IDS or user_id == admin_id: bad(403, "Нельзя заблокировать владельца или самого себя")
        async with Session.begin() as s:
            u = await s.get(User, user_id, with_for_update=True)
            if not u: bad(404, "Пользователь не найден")
            u.blocked = data.blocked
            audit(s, admin_id, "block" if data.blocked else "unblock", user_id, data.reason)
        async with Session.begin() as s: await ensure_access(s, user_id)
        return {"ok": True}

    @app.post("/api/admin/users/{user_id}/grant")
    async def admin_user_grant(user_id: int, data: AdminGrant, actor=Depends(admin_scope("users"))):
        admin_id, role = actor
        if role not in WRITERS: bad(403, "Выдавать подписки могут только управляющие")
        async with Session.begin() as s:
            u = await s.get(User, user_id, with_for_update=True)
            if not u: bad(404, "Пользователь не найден")
            sub = await add_subscription(s, u, "Выдано администратором", data.days,
                                         data.devices, data.traffic_gb * 1024**3 if data.traffic_gb else None, "admin")
            audit(s, admin_id, "subscription_give", user_id, data.reason)
            await queue_notice(s, user_id, "manual", str(sub.id), "Администратор выдал подписку Still VPN.")
        async with Session.begin() as s: await ensure_access(s, user_id)
        return {"ok": True}

    @app.post("/api/admin/devices/{device_id}/revoke")
    async def admin_device_revoke(device_id: str, data: AdminReason, actor=Depends(admin_scope("users"))):
        admin_id, role = actor
        if role not in WRITERS: bad(403, "Отзыв Peer разрешён только управляющим")
        async with Session.begin() as s:
            d = await s.get(Device, device_id, with_for_update=True)
            if not d: bad(404, "Устройство не найдено")
            d.enabled = False
            uid = d.user_id
            audit(s, admin_id, "peer_revoke", device_id, data.reason)
        async with Session.begin() as s: await ensure_access(s, uid)
        return {"ok": True}

    @app.post("/api/admin/users/{user_id}/revoke")
    async def admin_revoke_all(user_id: int, data: AdminReason, actor=Depends(admin_scope("users"))):
        admin_id, role = actor
        if role not in WRITERS: bad(403, "Отзыв Peer разрешён только управляющим")
        async with Session.begin() as s:
            if not await s.get(User, user_id): bad(404, "Пользователь не найден")
            await s.execute(update(Device).where(Device.user_id == user_id).values(enabled=False))
            audit(s, admin_id, "revoke_all_peers", user_id, data.reason)
        async with Session.begin() as s: await ensure_access(s, user_id)
        return {"ok": True}

    @app.get("/api/admin/plans")
    async def admin_plans(actor=Depends(admin_scope("plans")), s: AsyncSession = Depends(db_session)):
        rows = (await s.scalars(select(Plan).order_by(Plan.days, Plan.id))).all()
        return [plan_dict(p) for p in rows]

    @app.post("/api/admin/plans")
    async def admin_plan_create(data: AdminPlanData, actor=Depends(admin_scope("plans"))):
        if actor[1] not in WRITERS: bad(403, "Недостаточно прав")
        async with Session.begin() as s:
            p = Plan(title=data.title.strip(),days=data.days,stars=data.stars,devices=data.devices,
                     traffic_bytes=data.traffic_gb*1024**3 if data.traffic_gb else None,enabled=data.enabled)
            s.add(p)
            await s.flush()
            audit(s, actor[0], "plan_create", p.id, p.title)
            pid = p.id
        return {"ok":True, "id":pid}

    @app.put("/api/admin/plans/{plan_id}")
    async def admin_plan_update(plan_id: int, data: AdminPlanData, actor=Depends(admin_scope("plans"))):
        if actor[1] not in WRITERS: bad(403, "Недостаточно прав")
        async with Session.begin() as s:
            p = await s.get(Plan, plan_id, with_for_update=True)
            if not p: bad(404, "Тариф не найден")
            p.title=data.title.strip();p.days=data.days;p.stars=data.stars;p.devices=data.devices
            p.traffic_bytes=data.traffic_gb*1024**3 if data.traffic_gb else None
            p.enabled=data.enabled
            audit(s, actor[0], "plan_update", plan_id, "Изменены только будущие продажи")
        return {"ok": True}

    class AdminPromoIn(BaseModel):
        kind: str
        days_or_percent: int = Field(ge=1, le=365)
        max_uses: int = Field(ge=1, le=10000)
        hours: int = Field(ge=1, le=8760)

    @app.get("/api/admin/promos")
    async def admin_promos(actor=Depends(admin_scope("plans")),s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Promo).order_by(Promo.id.desc()).limit(60))).all()
        return [{"id":p.id,"type":"discount" if p.discount_percent else "days",
                 "value":p.discount_percent if p.discount_percent else p.days,
                 "uses":p.uses,"max_uses":p.max_uses,"enabled":p.enabled,
                 "expires_at":dt_iso(p.expires_at)} for p in rows]

    @app.post("/api/admin/promos")
    async def admin_promo_create(data:AdminPromoIn,actor=Depends(admin_scope("plans"))):
        if actor[1] not in WRITERS:bad(403,"Недостаточно прав")
        if data.kind not in ("days","discount"):bad(422,"Неверный тип")
        if data.kind=="discount" and not (1<=data.days_or_percent<=95):bad(422,"Скидка должна быть от 1 до 95%")
        code=("STILL-" if data.kind=="days" else "STILL-D-")+secrets.token_urlsafe(18).upper()
        async with Session.begin() as s:
            p=Promo(code_hash=code_hash(code),days=data.days_or_percent if data.kind=="days" else 0,
                    discount_percent=data.days_or_percent if data.kind=="discount" else 0,
                    max_uses=data.max_uses,expires_at=now()+timedelta(hours=data.hours),devices=1)
            s.add(p);await s.flush()
            audit(s,actor[0],"promo_create",p.id,f"{data.kind} {data.days_or_percent}; limit={data.max_uses}")
        return {"id":p.id,"code":code,"display_once":True}

    @app.post("/api/admin/promos/{promo_id}/disable")
    async def admin_promo_disable(promo_id:int,data:AdminReason,actor=Depends(admin_scope("plans"))):
        if actor[1] not in WRITERS:bad(403,"Недостаточно прав")
        async with Session.begin() as s:
            p=await s.get(Promo,promo_id,with_for_update=True)
            if not p:bad(404,"Промокод не найден")
            p.enabled=False
            audit(s,actor[0],"promo_disable",promo_id,data.reason)
        return {"ok":True}

    @app.get("/api/admin/servers")
    async def admin_servers(actor=Depends(admin_scope("servers")), s: AsyncSession = Depends(db_session)):
        nodes = (await s.scalars(select(ServerNode).order_by(ServerNode.id))).all()
        out=[]
        for n in nodes:
            h = await s.get(NodeHealth,n.id)
            online=bool(h and h.last_seen and h.last_seen >= now()-timedelta(minutes=3))
            out.append({"id":n.id,"location":n.location,"enabled":n.enabled,"online":online,
                        "endpoint":n.endpoint,"peer_count":h.peer_count if h else None,
                        "cpu":round(h.cpu_percent,1) if h and h.cpu_percent is not None else None,
                        "ram_used":h.memory_used if h else None,"ram_total":h.memory_total if h else None,
                        "disk_free":h.disk_free if h else None,"network_rx":h.network_rx if h else None,
                        "network_tx":h.network_tx if h else None,"last_seen":dt_iso(h.last_seen) if h else None,
                        "error":h.error if h else ""})
        return out

    @app.post("/api/admin/servers/{server_id}/state")
    async def admin_server_state(server_id:int, data:AdminServerState, actor=Depends(admin_scope("servers"))):
        if actor[1] not in WRITERS: bad(403, "Недостаточно прав")
        async with Session.begin() as s:
            node=await s.get(ServerNode,server_id,with_for_update=True)
            if not node: bad(404,"Сервер не найден")
            if data.enabled:
                try: await agent_request(node,"GET","/agent/stats")
                except Exception: bad(503,"Агент недоступен; включение отменено")
            node.enabled=data.enabled
            audit(s,actor[0],"server_enabled",server_id,data.reason+" enabled="+str(data.enabled))
        return {"ok":True}

    @app.get("/api/admin/payments")
    async def admin_payments(actor=Depends(admin_scope("finance")),s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Payment).order_by(Payment.created_at.desc()).limit(80))).all()
        return [{"id":p.id,"user_id":p.user_id,"plan":p.plan_title,"amount":p.amount,
                 "status":p.status,"date":dt_iso(p.created_at),"charge_id":p.telegram_charge_id,
                 "refund_date":dt_iso(p.refunded_at)} for p in rows]

    class TicketCreateIn(BaseModel):
        title: str = Field(min_length=4, max_length=140)
        description: str = Field(min_length=10, max_length=3500)
        priority: str = Field(default="normal", max_length=16)

    class TicketReplyIn(BaseModel):
        text: str = Field(min_length=2, max_length=3500)

    class TicketPriorityIn(BaseModel):
        priority: str = Field(max_length=16)

    @app.get("/api/tickets")
    async def api_user_tickets(user: User = Depends(current_user), s: AsyncSession = Depends(db_session)):
        rows = (await s.scalars(select(Ticket).where(Ticket.user_id == user.id)
                                 .order_by(Ticket.updated_at.desc(), Ticket.id.desc()).limit(60))).all()
        return [ticket_public(t) for t in rows]

    @app.post("/api/tickets")
    async def api_ticket_create(data: TicketCreateIn, user: User = Depends(current_user)):
        title, description = data.title.strip(), data.description.strip()
        if len(title) < 4 or len(description) < 10: bad(422, "Укажите тему и описание проблемы")
        if data.priority not in TICKET_PRIORITIES: bad(422, "Недопустимая важность")
        async with Session.begin() as s:
            # No more than 3 simultaneous open/answered cases and 4 new cases/hour.
            active = await s.scalar(select(func.count()).select_from(Ticket).where(
                Ticket.user_id == user.id, Ticket.status.in_(["open", "answered"]))) or 0
            recent = await s.scalar(select(func.count()).select_from(Ticket).where(
                Ticket.user_id == user.id, Ticket.created_at >= now()-timedelta(hours=1))) or 0
            if active >= 3: bad(429, "Сначала завершите одно из трёх активных обращений")
            if recent >= 4: bad(429, "Слишком много обращений за час")
            t = Ticket(user_id=user.id, title=title, priority=data.priority,
                       status="open", updated_at=now())
            s.add(t)
            await s.flush()
            s.add(TicketMessage(ticket_id=t.id, sender="user", text=description))
            record_event(s, "ticket_opened", user.id, ticket_event_details(t))
            tid = t.id
        return {"ok": True, "id": tid}

    @app.get("/api/tickets/{ticket_id}")
    async def api_ticket_detail(ticket_id: int, user: User = Depends(current_user),
                                s: AsyncSession = Depends(db_session)):
        t = await s.get(Ticket, ticket_id)
        if not t or t.user_id != user.id: bad(404, "Обращение не найдено")
        messages = (await s.scalars(select(TicketMessage).where(TicketMessage.ticket_id==ticket_id)
                                    .order_by(TicketMessage.id).limit(200))).all()
        return {**ticket_public(t), "messages": [{"id": m.id, "sender": m.sender,
                 "text": m.text, "date": dt_iso(m.created_at)} for m in messages]}

    @app.post("/api/tickets/{ticket_id}/reply")
    async def api_ticket_reply(ticket_id: int, data: TicketReplyIn,
                               user: User = Depends(current_user)):
        body = data.text.strip()
        if len(body) < 2: bad(422, "Сообщение слишком короткое")
        async with Session.begin() as s:
            t = await s.get(Ticket, ticket_id, with_for_update=True)
            if not t or t.user_id != user.id: bad(404, "Обращение не найдено")
            if t.status == "closed": bad(409, "Обращение закрыто. Сначала откройте его снова")
            count = await s.scalar(select(func.count()).select_from(TicketMessage)
                                   .where(TicketMessage.ticket_id==ticket_id)) or 0
            if count >= 200: bad(409, "Лимит сообщений. Создайте новое обращение")
            s.add(TicketMessage(ticket_id=t.id, sender="user", text=body))
            t.status = "open"; t.updated_at = now()
            record_event(s, "ticket_user_reply", user.id, ticket_event_details(t))
        return {"ok": True}

    @app.post("/api/tickets/{ticket_id}/close")
    async def api_ticket_close(ticket_id: int, user: User = Depends(current_user)):
        async with Session.begin() as s:
            t = await s.get(Ticket, ticket_id, with_for_update=True)
            if not t or t.user_id != user.id: bad(404, "Обращение не найдено")
            if t.status == "closed": return {"ok": True}
            t.status = "closed"; t.closed_at = now(); t.updated_at = now()
            record_event(s, "ticket_closed_by_user", user.id, ticket_event_details(t))
        return {"ok": True}

    @app.post("/api/tickets/{ticket_id}/reopen")
    async def api_ticket_reopen(ticket_id: int, user: User = Depends(current_user)):
        async with Session.begin() as s:
            t = await s.get(Ticket, ticket_id, with_for_update=True)
            if not t or t.user_id != user.id: bad(404, "Обращение не найдено")
            if t.status != "closed": bad(409, "Обращение уже открыто")
            active = await s.scalar(select(func.count()).select_from(Ticket).where(
                Ticket.user_id==user.id, Ticket.status.in_(["open", "answered"]))) or 0
            if active >= 3: bad(429, "Уже открыто три обращения")
            t.status = "open"; t.closed_at = None; t.updated_at = now()
            record_event(s, "ticket_reopened_by_user", user.id, ticket_event_details(t))
        return {"ok": True}

    @app.get("/api/admin/tickets")
    async def admin_tickets(actor=Depends(admin_scope("support")), s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Ticket).order_by(Ticket.updated_at.desc(), Ticket.id.desc())
                              .limit(160))).all()
        out=[]
        for t in rows:
            u=await s.get(User,t.user_id)
            out.append({**ticket_public(t), "user_name":
                        ((u.first_name+" "+u.last_name).strip() if u else "") or "Пользователь",
                        "username": (u.username if u else "")})
        return out

    @app.get("/api/admin/tickets/{ticket_id}")
    async def admin_ticket_detail(ticket_id:int, actor=Depends(admin_scope("support")),
                                  s:AsyncSession=Depends(db_session)):
        t=await s.get(Ticket,ticket_id)
        if not t: bad(404,"Обращение не найдено")
        u=await s.get(User,t.user_id)
        rows=(await s.scalars(select(TicketMessage).where(TicketMessage.ticket_id==ticket_id)
                              .order_by(TicketMessage.id).limit(200))).all()
        return {**ticket_public(t), "user_name":
                ((u.first_name+" "+u.last_name).strip() if u else "") or "Пользователь",
                "username": (u.username if u else ""),
                "messages":[{"sender":m.sender,"staff_id":m.staff_id,
                             "text":m.text,"date":dt_iso(m.created_at)} for m in rows]}

    @app.post("/api/admin/tickets/{ticket_id}/reply")
    async def admin_ticket_reply(ticket_id:int,data:AdminReply,actor=Depends(admin_scope("support"))):
        body=data.text.strip()
        if len(body)<2: bad(422,"Напишите ответ")
        async with Session.begin() as s:
            t=await s.get(Ticket,ticket_id,with_for_update=True)
            if not t or t.status=="closed": bad(409,"Обращение закрыто")
            count=await s.scalar(select(func.count()).select_from(TicketMessage)
                                 .where(TicketMessage.ticket_id==ticket_id)) or 0
            if count>=200: bad(409,"Достигнут лимит переписки")
            t.status="answered";t.updated_at=now()
            if t.assigned_admin is None: t.assigned_admin=actor[0]
            s.add(TicketMessage(ticket_id=ticket_id,sender="admin",staff_id=actor[0],text=body))
            audit(s,actor[0],"ticket_reply",ticket_id,"Ответ сохранён в Mini App")
            record_event(s,"ticket_staff_reply",t.user_id,
                         ticket_event_details(t)+f" · сотрудник {actor[0]}")
            if t.user_id>0:
                await queue_notice(s,t.user_id,"ticket_answer",str(ticket_id)+"-"+str(int(time.time()*1000)),
                                   f"✉ Still VPN · Поддержка ответила по обращению #{ticket_id}. Откройте Mini App → Тикеты.")
        return {"ok":True}

    @app.post("/api/admin/tickets/{ticket_id}/close")
    async def admin_ticket_close(ticket_id:int,data:AdminReason,actor=Depends(admin_scope("support"))):
        async with Session.begin() as s:
            t=await s.get(Ticket,ticket_id,with_for_update=True)
            if not t: bad(404,"Обращение не найдено")
            if t.status=="closed": return {"ok":True}
            t.status="closed";t.closed_at=now();t.updated_at=now()
            audit(s,actor[0],"ticket_close",ticket_id,data.reason)
            record_event(s,"ticket_closed_by_staff",t.user_id,ticket_event_details(t))
            if t.user_id>0:
                await queue_notice(s,t.user_id,"ticket_closed",str(ticket_id)+"-"+str(int(time.time()*1000)),
                                   f"✉ Still VPN · Обращение #{ticket_id} закрыто. При необходимости откройте его снова в Mini App.")
        return {"ok":True}

    @app.post("/api/admin/tickets/{ticket_id}/reopen")
    async def admin_ticket_reopen(ticket_id:int,actor=Depends(admin_scope("support"))):
        async with Session.begin() as s:
            t=await s.get(Ticket,ticket_id,with_for_update=True)
            if not t: bad(404,"Обращение не найдено")
            if t.status=="closed":
                t.status="open";t.updated_at=now();t.closed_at=None
                audit(s,actor[0],"ticket_reopen",ticket_id)
                record_event(s,"ticket_reopened_by_staff",t.user_id,ticket_event_details(t))
        return {"ok":True}

    @app.post("/api/admin/tickets/{ticket_id}/priority")
    async def admin_ticket_priority(ticket_id:int,data:TicketPriorityIn,
                                    actor=Depends(admin_scope("support"))):
        if data.priority not in TICKET_PRIORITIES: bad(422,"Неизвестная важность")
        async with Session.begin() as s:
            t=await s.get(Ticket,ticket_id,with_for_update=True)
            if not t: bad(404,"Обращение не найдено")
            t.priority=data.priority;t.updated_at=now()
            audit(s,actor[0],"ticket_priority",ticket_id,data.priority)
            record_event(s,"ticket_priority_changed",t.user_id,ticket_event_details(t))
        return {"ok":True}

    @app.get("/api/admin/audit")
    async def admin_audit(actor=Depends(admin_scope("audit")),s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Audit).order_by(Audit.id.desc()).limit(80))).all()
        return [{"id":x.id,"admin":x.admin_id,"action":x.action,"target":x.target,
                 "details":x.details,"result":x.result,"date":dt_iso(x.created_at)} for x in rows]

    @app.get("/api/admin/trial-settings")
    async def admin_trial_get(actor=Depends(admin_scope("settings")),s:AsyncSession=Depends(db_session)):
        return {"enabled":await setting(s,"trial_enabled","1")=="1",
                "hours":int(await setting(s,"trial_hours","24")),
                "traffic_gb":int(await setting(s,"trial_gb","1")),
                "devices":int(await setting(s,"trial_devices","1"))}

    @app.put("/api/admin/trial-settings")
    async def admin_trial_put(data:AdminTrialSettings,actor=Depends(admin_scope("settings"))):
        if actor[1] not in WRITERS: bad(403,"Недостаточно прав")
        values={"trial_enabled":"1" if data.enabled else "0","trial_hours":str(data.hours),
                "trial_gb":str(data.traffic_gb),"trial_devices":str(data.devices)}
        async with Session.begin() as s:
            for k,v in values.items():
                st=await s.get(Setting,k)
                if st: st.value=v
                else: s.add(Setting(key=k,value=v))
            audit(s,actor[0],"trial_settings","trial",json.dumps(values))
        return {"ok":True}

    @app.get("/api/admin/staff")
    async def admin_staff_list(actor=Depends(admin_scope("staff")),s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Admin).order_by(Admin.user_id))).all()
        return {"owners":sorted(OWNER_IDS),"members":[{"id":x.user_id,"role":x.role} for x in rows]}

    @app.put("/api/admin/staff/{user_id}")
    async def admin_staff_set(user_id:int,data:AdminStaffRole,actor=Depends(admin_scope("staff"))):
        if actor[1]!="owner": bad(403,"Только владелец")
        if user_id in OWNER_IDS: bad(403,"Роль владельца меняется только через OWNER_IDS")
        if data.role not in ADMIN_ROLES-{"owner"}: bad(422,"Некорректная роль")
        async with Session.begin() as s:
            st=await s.get(Admin,user_id)
            if st:st.role=data.role
            else:s.add(Admin(user_id=user_id,role=data.role))
            audit(s,actor[0],"staff_role",user_id,data.role+": "+data.reason)
        return {"ok":True}

    @app.delete("/api/admin/staff/{user_id}")
    async def admin_staff_remove(user_id:int,data:AdminReason,actor=Depends(admin_scope("staff"))):
        if actor[1]!="owner": bad(403,"Только владелец")
        if user_id in OWNER_IDS: bad(403,"Владелец не удаляется")
        async with Session.begin() as s:
            st=await s.get(Admin,user_id)
            if not st: bad(404,"Администратор не найден")
            await s.delete(st)
            audit(s,actor[0],"staff_remove",user_id,data.reason)
        return {"ok":True}

    # ------------------------------------------------------------
    # Standalone browser access. Telegram Mini App and /api/* remain unchanged.
    # Separate credentials, same User / Subscription / Trial / Device tables.
    # ------------------------------------------------------------
    WEB_REGISTRATION_ENABLED = os.getenv("WEB_REGISTRATION_ENABLED", "1") == "1"
    WEB_TRIAL_ENABLED = os.getenv("WEB_TRIAL_ENABLED", "0") == "1"
    BOT_USERNAME = {"value": re.sub(r"[^A-Za-z0-9_]", "", os.getenv("BOT_USERNAME", ""))}
    WEB_COOKIE = "still_web_session"
    WEB_SESSION_DAYS = 7
    LOGIN_RE = re.compile(r"^[a-z][a-z0-9_]{2,31}$")
    EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    web_rate: dict[str, tuple[float, int]] = {}

    def site_rate(request: Request, action: str, subject: str = "", limit: int = 20, window: int = 60):
        """Local fail-closed throttle for the single-process BotHost deployment."""
        key = (action + ":" + (request.client.host if request.client else "unknown")
               + ":" + subject.lower()[:64])
        tick = time.monotonic()
        if len(web_rate) > 20000:
            for k, (started, _) in list(web_rate.items()):
                if tick - started > 3600:
                    web_rate.pop(k, None)
        started, count = web_rate.get(key, (tick, 0))
        if tick - started > window:
            started, count = tick, 0
        if count >= limit:
            bad(429, "Слишком много попыток. Повторите позже.")
        web_rate[key] = (started, count + 1)

    def check_web_origin(req: Request):
        """Require same-origin writes even without relying on SameSite cookies."""
        origin = (req.headers.get("origin") or "").rstrip("/")
        configured = urlparse(WEBAPP_URL)
        base = f"{configured.scheme}://{configured.netloc}"
        if origin and origin != base:
            bad(403, "Неверный источник запроса")
        if not origin:
            ref = req.headers.get("referer") or ""
            fetch_site = req.headers.get("sec-fetch-site") or ""
            if (ref and not (ref == base or ref.startswith(base + "/"))) or fetch_site not in ("", "same-origin", "none"):
                bad(403, "Неверный источник запроса")
        if req.method not in ("GET", "HEAD") and "application/json" not in req.headers.get("content-type", ""):
            bad(415, "Требуется application/json")

    def web_password_hash(password: str, salt_hex: str) -> str:
        return hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
                              n=16384, r=8, p=1, dklen=32).hex()

    def valid_web_password(password: str):
        if not (12 <= len(password) <= 128 and re.search(r"[A-Za-zА-Яа-яЁё]", password)
                and re.search(r"\d", password)):
            bad(422, "Пароль: 12–128 символов, минимум одна буква и цифра")

    def digest_web(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def web_csrf(raw_token: str) -> str:
        return hmac.new(CODE_PEPPER.encode(), ("webcsrf:" + raw_token).encode(), hashlib.sha256).hexdigest()

    def web_recovery_hash(code: str) -> str:
        return hmac.new(CODE_PEPPER.encode(), ("web-recovery:" + code.strip().upper()).encode(), hashlib.sha256).hexdigest()

    def web_email_hash(account_id: int, code: str) -> str:
        return hmac.new(CODE_PEPPER.encode(), f"web-email:{account_id}:{code}".encode(), hashlib.sha256).hexdigest()

    def web_link_hash(code: str) -> str:
        return hmac.new(CODE_PEPPER.encode(), ("web-link:" + code.strip().upper()).encode(), hashlib.sha256).hexdigest()

    def web_session_response(data: dict, token: str) -> JSONResponse:
        response = JSONResponse(data)
        response.set_cookie(WEB_COOKIE, token, max_age=WEB_SESSION_DAYS*86400,
                            httponly=True, secure=True, samesite="lax", path="/web")
        return response

    async def make_web_session(s: AsyncSession, account: WebAccount) -> tuple[str, str]:
        token = secrets.token_urlsafe(40)
        s.add(WebSession(token_hash=digest_web(token), account_id=account.id,
                         expires_at=now() + timedelta(days=WEB_SESSION_DAYS)))
        return token, web_csrf(token)

    async def web_authorized(request: Request, s: AsyncSession = Depends(db_session)):
        cookie = request.cookies.get(WEB_COOKIE, "")
        if len(cookie) < 40 or len(cookie) > 128:
            bad(401, "Войдите в кабинет Still VPN")
        websession = await s.get(WebSession, digest_web(cookie))
        if not websession or websession.expires_at <= now():
            bad(401, "Сессия завершилась. Войдите снова.")
        account = await s.get(WebAccount, websession.account_id)
        user = await s.get(User, account.user_id) if account else None
        if not user or user.blocked:
            bad(403, "Доступ к аккаунту заблокирован")
        if request.method not in ("GET", "HEAD"):
            check_web_origin(request)
            provided = request.headers.get("x-csrf-token", "")
            if not hmac.compare_digest(web_csrf(cookie), provided):
                bad(403, "Неверный CSRF-токен")
        site_rate(request, "account-api", subject=str(account.id), limit=120, window=60)
        # Read-only identity was loaded; write endpoints may now begin a transaction.
        await s.commit()
        return user, account, web_csrf(cookie)

    class WebCredentials(BaseModel):
        login: str = Field(min_length=3, max_length=32)
        password: str = Field(min_length=1, max_length=128)

    class WebRegistration(WebCredentials):
        email: str | None = Field(default=None, max_length=254)
        agreed: bool

    @app.get("/web/api/config")
    async def web_public_config():
        username = BOT_USERNAME["value"]
        return {"bot_url": "https://t.me/" + username if username else None,
                "registration_enabled": WEB_REGISTRATION_ENABLED,
                "trial_enabled": WEB_TRIAL_ENABLED,
                "email_enabled": bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM")),
                "terms_url": TERMS_URL if TERMS_URL.startswith("https://") else "/web/terms",
                "channel_url": CHANNEL_URL, "release": RELEASE,
                "servers": [{"country": PUBLIC_SERVER_COUNTRY,
                             "provider": PUBLIC_SERVER_PROVIDER, "protocol": "WireGuard"}]}

    @app.post("/web/api/register")
    async def web_register(data: WebRegistration, req: Request):
        check_web_origin(req)
        site_rate(req, "registration", limit=8, window=3600)
        if not WEB_REGISTRATION_ENABLED: bad(503, "Регистрация на сайте временно закрыта")
        login = data.login.strip().lower()
        if not LOGIN_RE.fullmatch(login): bad(422, "Логин: латинские буквы, цифры и _, от 3 до 32")
        valid_web_password(data.password)
        if not data.agreed: bad(422, "Необходимо принять условия тестирования")
        email = data.email.strip().lower() if data.email else None
        if email and (not EMAIL_RE.fullmatch(email) or len(email)>254):
            bad(422, "Неверный email")
        from sqlalchemy.exc import IntegrityError
        try:
            async with Session.begin() as s:
                if await s.scalar(select(WebAccount.id).where(WebAccount.login == login)):
                    bad(409, "Логин уже занят")
                if email and await s.scalar(select(WebAccount.id).where(WebAccount.email == email)):
                    bad(409, "Этот email уже используется")
                uid = - (secrets.randbelow(2**60) + 1)
                while await s.get(User, uid):
                    uid = - (secrets.randbelow(2**60) + 1)
                s.add(User(id=uid, username="web:" + login, first_name=login))
                record_event(s, "registration_web", uid, "Регистрация на отдельном сайте · логин " + login)
                salt = secrets.token_hex(16)
                recovery = "STILL-" + secrets.token_urlsafe(24)
                account = WebAccount(user_id=uid, login=login, password_salt=salt,
                                     password_hash=web_password_hash(data.password, salt),
                                     recovery_hash=web_recovery_hash(recovery), email=email)
                s.add(account)
                await s.flush()
                token, csrf = await make_web_session(s, account)
        except IntegrityError:
            bad(409, "Имя или email уже заняты")
        return web_session_response({"ok": True, "csrf": csrf,
                                     "recovery_code": recovery,
                                     "message": "Сохраните код восстановления — он показывается только один раз"}, token)

    @app.post("/web/api/login")
    async def web_login(data: WebCredentials, req: Request):
        check_web_origin(req)
        login = data.login.strip().lower()
        site_rate(req, "login:ip", limit=35, window=600)
        site_rate(req, "login:user", subject=login, limit=8, window=600)
        async with Session.begin() as s:
            account = await s.scalar(select(WebAccount).where(WebAccount.login == login))
            # Equal-cost check even for an unknown username.
            salt = account.password_salt if account else "0"*32
            expected = account.password_hash if account else "0"*64
            correct = hmac.compare_digest(web_password_hash(data.password, salt), expected)
            if not account or not correct or (account.locked_until and account.locked_until > now()):
                if account:
                    account.failed_logins += 1
                    if account.failed_logins >= 10:
                        account.locked_until = now() + timedelta(minutes=15)
                        account.failed_logins = 0
                # Avoid raising inside transaction so lockouts commit.
                denied = True
            else:
                denied = False
                account.failed_logins = 0
                account.locked_until = None
                user = await s.get(User, account.user_id)
                if not user or user.blocked:
                    denied = True
                else:
                    token, csrf = await make_web_session(s, account)
                    record_event(s, "web_login", user.id, "Успешный вход на сайт")
        if denied: bad(401, "Неверный логин или пароль, либо вход временно ограничен")
        return web_session_response({"ok": True, "csrf": csrf}, token)

    @app.post("/web/api/logout")
    async def web_logout(req: Request, identity=Depends(web_authorized)):
        cookie = req.cookies.get(WEB_COOKIE, "")
        async with Session.begin() as s:
            await s.execute(delete(WebSession).where(WebSession.token_hash == digest_web(cookie)))
        response = JSONResponse({"ok": True})
        response.delete_cookie(WEB_COOKIE, path="/web", secure=True, httponly=True, samesite="lax")
        return response

    @app.get("/web/api/me")
    async def web_me(identity=Depends(web_authorized), s: AsyncSession=Depends(db_session)):
        user, account, csrf = identity
        shared = await api_me(user, s)
        shared["admin_role"] = None  # Telegram-based admin privileges are never inherited by browser sessions.
        shared["username"] = account.login
        shared["auth_type"] = "web"
        shared["email"] = account.email
        shared["email_verified"] = account.email_verified
        shared["can_trial"] = WEB_TRIAL_ENABLED and account.email_verified and bool(os.getenv("SMTP_HOST"))
        shared["csrf"] = csrf
        return shared

    @app.get("/web/api/plans")
    async def web_plans(identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        return await api_plans(identity[0], s)

    @app.get("/web/api/devices")
    async def web_devices(identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        return await api_devices(identity[0], s)

    @app.post("/web/api/devices")
    async def web_create_device(data:DeviceIn, req:Request, identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        site_rate(req,"device-create",subject=str(identity[1].id),limit=12,window=3600)
        return await api_add_device(data, identity[0], s)

    @app.post("/web/api/devices/{device_id}/send-conf")
    async def web_send_conf(device_id: str, data: ConfToTelegramIn, req: Request,
                            identity=Depends(web_authorized),
                            session: AsyncSession=Depends(db_session)):
        site_rate(req, "config-to-tg", subject=str(identity[1].id), limit=6, window=3600)
        return await deliver_conf_to_telegram(device_id, data, identity[0], session)

    @app.patch("/web/api/devices/{device_id}")
    async def web_rename_device(device_id:str, data:RenameIn, identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        return await api_rename(device_id, data, identity[0], s)

    @app.delete("/web/api/devices/{device_id}")
    async def web_revoke_device(device_id:str, identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        return await api_delete_device(device_id, identity[0], s)

    @app.post("/web/api/redeem")
    async def web_redeem(data:RedeemIn, req:Request, identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        site_rate(req,"redeem",subject=str(identity[1].id),limit=12,window=3600)
        return await api_redeem(data, identity[0], s)

    @app.post("/web/api/trial")
    async def web_trial(identity=Depends(web_authorized), s:AsyncSession=Depends(db_session)):
        user, account, _ = identity
        if not WEB_TRIAL_ENABLED or not account.email_verified or not os.getenv("SMTP_HOST"):
            bad(403, "На сайте пробный доступ доступен только с подтверждённым email при включении администратором")
        return await api_trial(user, s)

    class WebEmailUpdate(BaseModel):
        email: str = Field(min_length=5,max_length=254)
        password: str = Field(min_length=1,max_length=128)

    @app.post("/web/api/email/update")
    async def web_email_update(data:WebEmailUpdate,req:Request,identity=Depends(web_authorized)):
        _, account, _ = identity
        site_rate(req,"email-update",subject=str(account.id),limit=4,window=3600)
        email=data.email.strip().lower()
        if not EMAIL_RE.fullmatch(email): bad(422,"Неверный email")
        if not hmac.compare_digest(web_password_hash(data.password,account.password_salt),account.password_hash):
            bad(403,"Неверный пароль")
        from sqlalchemy.exc import IntegrityError
        try:
            async with Session.begin() as s:
                stored=await s.get(WebAccount,account.id)
                stored.email=email
                stored.email_verified=False
                challenge=await s.get(WebEmailChallenge,account.id)
                if challenge: await s.delete(challenge)
        except IntegrityError:
            bad(409,"Этот email уже используется")
        return {"ok":True}

    class WebEmailCode(BaseModel):
        code: str = Field(min_length=6, max_length=6)

    def send_web_mail(recipient: str, code: str):
        import smtplib, ssl
        from email.message import EmailMessage
        host = os.getenv("SMTP_HOST", "").strip()
        sender = os.getenv("SMTP_FROM", "").strip()
        port = int(os.getenv("SMTP_PORT", "587"))
        if not host or not sender or port not in (465, 587):
            raise RuntimeError("SMTP не настроен")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = "Still VPN — подтверждение email"
        msg.set_content(f"Код подтверждения Still VPN: {code}\nКод действует 10 минут. Если вы не запрашивали его, игнорируйте письмо.")
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=12, context=context) as smtp:
                if os.getenv("SMTP_USER"): smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=12) as smtp:
                smtp.starttls(context=context)
                if os.getenv("SMTP_USER"): smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
                smtp.send_message(msg)

    @app.post("/web/api/email/send")
    async def web_email_send(req:Request, identity=Depends(web_authorized)):
        _, account, _ = identity
        site_rate(req,"email-send",subject=str(account.id),limit=5,window=3600)
        if account.email_verified: bad(409,"Email уже подтверждён")
        if not account.email: bad(409,"Email не указан при регистрации")
        if not (os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM")):
            bad(503,"Почта не настроена администратором")
        code = f"{secrets.randbelow(1_000_000):06d}"
        async with Session.begin() as s:
            challenge = await s.get(WebEmailChallenge, account.id)
            if challenge and (now()-challenge.sent_at).total_seconds() < 120:
                bad(429,"Новое письмо можно запросить через 2 минуты")
            if challenge:
                challenge.code_hash=web_email_hash(account.id,code)
                challenge.expires_at=now()+timedelta(minutes=10)
                challenge.sent_at=now()
                challenge.attempts=0
            else:
                s.add(WebEmailChallenge(account_id=account.id,code_hash=web_email_hash(account.id,code),
                                        expires_at=now()+timedelta(minutes=10), sent_at=now()))
        try:
            await asyncio.to_thread(send_web_mail,account.email,code)
        except Exception:
            LOG.exception("Email verification delivery failed")
            bad(502,"Письмо не отправлено. Проверьте SMTP")
        return {"ok":True,"message":"Код отправлен на указанный email"}

    @app.post("/web/api/email/verify")
    async def web_email_verify(data:WebEmailCode, req:Request, identity=Depends(web_authorized)):
        _, account, _ = identity
        site_rate(req,"email-verify",subject=str(account.id),limit=10,window=600)
        denied = False
        async with Session.begin() as s:
            c = await s.get(WebEmailChallenge, account.id)
            if not c or c.expires_at <= now() or c.attempts >= 5:
                denied = True
            else:
                c.attempts += 1
                if not hmac.compare_digest(c.code_hash, web_email_hash(account.id, data.code)):
                    denied = True
                else:
                    a=await s.get(WebAccount,account.id)
                    a.email_verified=True
                    await s.delete(c)
        if denied: bad(422,"Код неверен или устарел")
        return {"ok":True}

    class WebPasswordChange(BaseModel):
        old_password: str = Field(min_length=1, max_length=128)
        new_password: str = Field(min_length=1, max_length=128)

    @app.post("/web/api/password/change")
    async def web_password_change(data:WebPasswordChange, req:Request, identity=Depends(web_authorized)):
        _,account,_=identity
        site_rate(req,"change-password",subject=str(account.id),limit=5,window=600)
        valid_web_password(data.new_password)
        if not hmac.compare_digest(web_password_hash(data.old_password,account.password_salt),account.password_hash):
            bad(403,"Старый пароль неверен")
        salt=secrets.token_hex(16)
        recovery="STILL-"+secrets.token_urlsafe(24)
        async with Session.begin() as s:
            stored=await s.get(WebAccount,account.id)
            stored.password_salt=salt
            stored.password_hash=web_password_hash(data.new_password,salt)
            stored.recovery_hash=web_recovery_hash(recovery)
            # Revoke ALL sessions on password change.
            await s.execute(delete(WebSession).where(WebSession.account_id==account.id))
        response=JSONResponse({"ok":True,"recovery_code":recovery})
        response.delete_cookie(WEB_COOKIE,path="/web",secure=True,httponly=True,samesite="lax")
        return response

    class WebRecoverIn(BaseModel):
        login: str = Field(min_length=3, max_length=32)
        recovery_code: str = Field(min_length=20,max_length=120)
        new_password: str = Field(min_length=1,max_length=128)

    @app.post("/web/api/password/recover")
    async def web_password_recover(data:WebRecoverIn,req:Request):
        check_web_origin(req)
        site_rate(req,"recovery",subject=data.login,limit=6,window=3600)
        valid_web_password(data.new_password)
        denied=False
        async with Session.begin() as s:
            account=await s.scalar(select(WebAccount).where(WebAccount.login==data.login.strip().lower()))
            if not account or not hmac.compare_digest(account.recovery_hash,web_recovery_hash(data.recovery_code)):
                denied=True
            else:
                new_salt=secrets.token_hex(16)
                next_code="STILL-"+secrets.token_urlsafe(24)
                account.password_salt=new_salt
                account.password_hash=web_password_hash(data.new_password,new_salt)
                account.recovery_hash=web_recovery_hash(next_code)
                account.failed_logins=0
                account.locked_until=None
                await s.execute(delete(WebSession).where(WebSession.account_id==account.id))
        if denied: bad(403,"Неверный логин или код восстановления")
        return {"ok":True,"recovery_code":next_code}

    class WebLinkIn(BaseModel):
        code: str = Field(min_length=12,max_length=80)

    @app.post("/web/api/link-telegram")
    async def web_link_telegram(data:WebLinkIn,req:Request,identity=Depends(web_authorized)):
        user,account,_=identity
        site_rate(req,"link",subject=str(account.id),limit=8,window=600)
        if user.id>0: bad(409,"Telegram уже привязан к этому аккаунту")
        h=web_link_hash(data.code)
        async with Session.begin() as s:
            link=await s.get(WebLinkCode,h)
            if not link or link.expires_at <= now():
                bad(403,"Код привязки недействителен или истёк")
            other=await s.scalar(select(WebAccount.id).where(WebAccount.user_id==link.telegram_id))
            if other: bad(409,"Этот Telegram-аккаунт уже связан с другим веб-кабинетом")
            # No automatic merging of existing entitlements / devices: that could lose access.
            existing=await s.scalar(select(Subscription.id).where(Subscription.user_id==user.id).limit(1))
            dev=await s.scalar(select(Device.id).where(Device.user_id==user.id).limit(1))
            tr=await s.get(Trial,user.id)
            gift=await s.scalar(select(Payment.id).where(Payment.user_id==user.id).limit(1))
            if existing or dev or tr or gift:
                bad(409,"Аккаунт уже использовал VPN. Для безопасной привязки обратитесь в поддержку")
            stored=await s.get(WebAccount,account.id)
            stored.user_id=link.telegram_id
            await s.flush()
            old=await s.get(User,user.id)
            await s.delete(old)
            await s.delete(link)
        return {"ok":True,"message":"Telegram привязан. Подписки и устройства теперь общие."}

    @router.message(Command("linkweb"))
    async def linkweb_command(message: Message):
        if message.chat.type != "private" or not message.from_user: return
        site_rate_key = "link-bot:"+str(message.from_user.id)
        tick=time.monotonic()
        stamp,count=web_rate.get(site_rate_key,(tick,0))
        if tick-stamp>600: stamp,count=tick,0
        if count>=4:
            await message.answer("Слишком много кодов. Повторите через 10 минут.")
            return
        web_rate[site_rate_key]=(stamp,count+1)
        code="STILL-"+secrets.token_urlsafe(20)
        async with Session.begin() as s:
            await upsert_user(s,message.from_user)
            s.add(WebLinkCode(code_hash=web_link_hash(code), telegram_id=message.from_user.id,
                              expires_at=now()+timedelta(minutes=10)))
        await message.answer("<b>Привязка Still VPN Web</b>\n\nОткройте сайт и в профиле введите код:\n"
                             f"<code>{html_escape(code)}</code>\n\nКод действует 10 минут и одноразовый. "
                             "Никому не передавайте код.",parse_mode="HTML")

    class WebTicketText(BaseModel):
        text: str = Field(min_length=5,max_length=3500)

    @app.get("/web/api/tickets")
    async def web_tickets(identity=Depends(web_authorized),s:AsyncSession=Depends(db_session)):
        rows=(await s.scalars(select(Ticket).where(Ticket.user_id==identity[0].id)
                              .order_by(Ticket.id.desc()).limit(30))).all()
        return [{"id":t.id,"status":t.status,"date":t.created_at} for t in rows]

    @app.post("/web/api/tickets")
    async def web_ticket_create(data:WebTicketText,req:Request,identity=Depends(web_authorized)):
        site_rate(req,"web-support",subject=str(identity[1].id),limit=8,window=3600)
        async with Session.begin() as s:
            open_count=await s.scalar(select(func.count()).select_from(Ticket).where(
                Ticket.user_id==identity[0].id,Ticket.status.in_(["open", "answered"])))
            if open_count >= 3: bad(429,"У вас уже три открытых обращения")
            t=Ticket(user_id=identity[0].id,title="Обращение с сайта",priority="normal",updated_at=now())
            s.add(t);await s.flush()
            record_event(s, "ticket_opened", identity[0].id, ticket_event_details(t)+" · сайт")
            s.add(TicketMessage(ticket_id=t.id,sender="user",text=data.text.strip()))
            ticket_id=t.id
        return {"ok":True,"id":ticket_id}

    @app.get("/web/api/tickets/{ticket_id}")
    async def web_ticket_detail(ticket_id:int,identity=Depends(web_authorized),s:AsyncSession=Depends(db_session)):
        t=await s.get(Ticket,ticket_id)
        if not t or t.user_id!=identity[0].id: bad(404,"Обращение не найдено")
        messages=(await s.scalars(select(TicketMessage).where(TicketMessage.ticket_id==ticket_id)
                                  .order_by(TicketMessage.id).limit(150))).all()
        return {"id":t.id,"status":t.status,"messages":[{"sender":x.sender,"text":x.text,"date":x.created_at} for x in messages]}

    @app.post("/web/api/tickets/{ticket_id}/reply")
    async def web_ticket_reply(ticket_id:int,data:WebTicketText,req:Request,identity=Depends(web_authorized)):
        site_rate(req,"web-support-reply",subject=str(identity[1].id),limit=25,window=3600)
        async with Session.begin() as s:
            t=await s.get(Ticket,ticket_id)
            if not t or t.user_id!=identity[0].id or t.status=="closed":
                bad(404,"Нет открытого обращения")
            s.add(TicketMessage(ticket_id=t.id,sender="user",text=data.text.strip()))
            t.status="open";t.updated_at=now()
            record_event(s,"ticket_user_reply",t.user_id,ticket_event_details(t)+" · сайт")
        return {"ok":True}

    def seo_site_url() -> str:
        u = urlparse(WEBAPP_URL)
        if u.scheme != "https" or not u.netloc:
            return "https://stillvpn.bothost.tech/web"
        return f"{u.scheme}://{u.netloc}/web"

    def seo_public_html() -> str:
        # Static server response exposes real headings/links even when JS is not executed.
        return STILL_WEB_HTML.replace("__STILL_CANONICAL__", html_escape(seo_site_url(), quote=True))

    # Public Google Search Console verification endpoint, from the original HTML file.
    # Keep the contents exact (including no trailing newline).
    @app.get("/googledbf78c04b92f601b.html", include_in_schema=False)
    async def google_site_verification():
        return Response(
            content="google-site-verification: googledbf78c04b92f601b.html",
            media_type="text/html",
        )

    @app.get("/robots.txt", include_in_schema=False)
    async def robots_txt():
        return Response(
            "User-agent: *\n"
            "Allow: /web\n"
            "Disallow: /api/\n"
            "Disallow: /web/api/\n"
            "Disallow: /health\n"
            "Disallow: /build\n"
            "Sitemap: " + seo_site_url().removesuffix("/web") + "/sitemap.xml\n",
            media_type="text/plain; charset=utf-8",
        )

    @app.get("/sitemap.xml", include_in_schema=False)
    async def sitemap_xml():
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>' + seo_site_url() + '</loc></url></urlset>',
            media_type="application/xml; charset=utf-8",
        )

    @app.get("/web",response_class=HTMLResponse)
    @app.get("/web/",response_class=HTMLResponse)
    async def standalone_site():
        return HTMLResponse(seo_public_html())

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=204)

    @app.get("/site", response_class=HTMLResponse, include_in_schema=False)
    async def standalone_site_alias():
        return HTMLResponse(seo_public_html())

    @app.get("/web/terms",response_class=HTMLResponse)
    async def standalone_terms():
        return HTMLResponse("""<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<body style='font:16px/1.7 system-ui;background:#100D11;color:#F3EEF0;max-width:680px;margin:32px auto;padding:0 20px'>
<h1>Still VPN — условия тестирования</h1>
<p>Сервис находится на этапе тестирования. VPN не гарантирует абсолютную анонимность, доступность всех сайтов или непрерывность соединения.</p>
<p>Для работы сайта хранятся логин, хеш пароля, случайный идентификатор сессии, параметры подписки, устройства и счётчики трафика WireGuard. Содержание пользовательского трафика этим приложением не сохраняется.</p>
<p>При выборе функции «Получить .conf в личный Telegram-чат» приватный ключ однократно передаётся на сервер Still VPN по HTTPS и в Telegram. Still VPN не сохраняет приватный ключ в своей базе или логах, однако копия остаётся в личной переписке Telegram до её удаления.</p>
<p>Для технического учёта владельцам в закрытой служебной группе Telegram могут отправляться уведомления о регистрации, подключениях устройств, оплатах и действиях администраторов с именем, @username и Telegram ID пользователя. Приватные VPN-ключи, пароли и тексты пользовательского трафика в группу не передаются.</p>
<p>Подписка на информационный канал Still VPN добровольная.</p>
<p>Пользователь обязан соблюдать применимое законодательство. Пробный доступ может быть ограничен и отозван при злоупотреблении.</p>
<p>Покупка подписок на этом веб-сайте не реализована. Для платного коммерческого запуска требуются отдельные юридические документы с данными владельца сервиса, условиями возврата и контактами.</p>
<a style='color:#c3a1d5' href='/web'>Вернуться в Still VPN</a></body></html>""")


    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTMLResponse(MINI_APP_HTML)

    async def database_selftest():
        """Exercise the real configured database, then rollback every test record."""
        await initialize_db()
        async with Session() as s:
            transaction = await s.begin()
            try:
                assert (await s.scalar(text("SELECT 1"))) == 1
                if DATABASE_IS_SQLITE:
                    fk = await s.scalar(text("PRAGMA foreign_keys"))
                    journal = await s.scalar(text("PRAGMA journal_mode"))
                    assert fk == 1, "SQLite foreign_keys must be enabled"
                    assert journal.lower() == "wal", "SQLite WAL must be enabled"
                test_id = 8_000_000_000_000_000_000 + secrets.randbelow(1_000_000)
                fake = User(id=test_id, username="shade_dbtest", first_name="Тест")
                s.add(fake)
                await s.flush()
                sub = await add_subscription(s, fake, "Test", 30, 1, None, "test")
                loaded = await s.get(Subscription, sub.id)
                assert loaded.starts_at.tzinfo is not None, "Timestamp should be timezone aware"
                assert loaded.ends_at.tzinfo is not None
                access = await entitlement(s, fake)
                assert access and access["name"] == "Test" and access["devices"] == 1
                await queue_notice(s, fake.id, "dbtest", "duplicate", "test")
                await queue_notice(s, fake.id, "dbtest", "duplicate", "test")
                assert (await s.scalar(select(func.count()).select_from(Notice).where(
                    Notice.user_id == fake.id))) == 1, "Notice idempotency failed"
                print("PASS: SQL database, migrations, UTC, subscription, notice idempotency")
            finally:
                await transaction.rollback()
        if DATABASE_IS_SQLITE:
            import sqlite3
            # This check is independent from the async ORM and verifies on-disk database.
            with sqlite3.connect(str(DATABASE_PATH)) as db:
                assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)
            print("PASS: SQLite App Data integrity", str(DATABASE_PATH))
        await engine.dispose()
        if bot:
            await bot.session.close()
        return True

    async def verify_services():
        """Read-only integration smoke check using configured real services; does not pay/modify."""
        print("Still VPN — проверка подключений (без выдачи доступа и оплаты)")
        issues = []
        if not BOT_TOKEN: issues.append("BOT_TOKEN не задан")
        if not engine: issues.append("DATABASE_URL не задан")
        if not WEBAPP_URL.startswith("https://"): issues.append("WEBAPP_URL должен быть HTTPS")
        if not OWNER_IDS: issues.append("OWNER_IDS не указан")
        if len(CODE_PEPPER) < 32: issues.append("CODE_PEPPER должен иметь >=32 символа")
        if not fernet: issues.append("GIFT_FERNET_KEY отсутствует или неверный")
        if len(WG_AGENT_SECRET) < 32: issues.append("WG_AGENT_SECRET должен иметь >=32 символа")
        if issues:
            for item in issues: print("FAIL:", item)
            return False
        try:
            async with engine.connect() as c:
                await c.execute(text("SELECT 1"))
                if DATABASE_IS_SQLITE:
                    found = await c.scalar(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
                    if found != "users":
                        raise RuntimeError("Нет таблиц Still VPN; запустите бота или `python shade.py dbtest`")
            print("OK: база данных отвечает (" + ("SQLite App Data" if DATABASE_IS_SQLITE else "PostgreSQL") + ")")
        except Exception as exc:
            issues.append("База данных недоступна: " + str(exc)[:120])
        try:
            me = await bot.get_me()
            print("OK: Telegram Bot API @" + str(me.username))
        except Exception as exc:
            issues.append("Bot API недоступен: " + str(exc)[:120])
        if WG_AGENT_URL and WG_SERVER_ENDPOINT and WG_SERVER_PUBLIC_KEY:
            try:
                temp = type("Server", (), {"agent_url": WG_AGENT_URL, "id": 1})()
                stats = await agent_request(temp, "GET", "/agent/stats")
                print(f"OK: WireGuard агент отвечает, peer: {len(stats.get('peers', []))}")
            except Exception as exc:
                issues.append("WireGuard агент недоступен: " + str(exc)[:120])
        else:
            issues.append("WG_AGENT_URL / WG_SERVER_ENDPOINT / WG_SERVER_PUBLIC_KEY не заданы")
        for issue in issues: print("FAIL:", issue)
        print("Итог:", "OK (интеграции не гарантируют качество VPN)" if not issues else "НУЖНО ИСПРАВИТЬ")
        if bot: await bot.session.close()
        if engine: await engine.dispose()
        return not issues

    @asynccontextmanager
    async def lifespan_app(a: FastAPI):
        if not BOT_TOKEN or not WEBAPP_URL.startswith("https://") or not engine or not OWNER_IDS or len(CODE_PEPPER) < 32:
            raise RuntimeError("Нужны BOT_TOKEN, HTTPS WEBAPP_URL, база SQLite/PostgreSQL, OWNER_IDS и CODE_PEPPER (>=32)")
        if ENABLE_PAYMENTS and not payments_ready():
            LOG.warning("Telegram Stars сейчас недоступны: проверьте TERMS_URL (HTTPS), GIFT_FERNET_KEY и WG_AGENT_SECRET >=32; "
                        "бот и VPN продолжат работать, новые счета запрещены")
        await initialize_db()
        # The website's Telegram button is resolved from Bot API or BOT_USERNAME.
        if not BOT_USERNAME["value"]:
            try:
                bot_profile = await bot.get_me()
                BOT_USERNAME["value"] = bot_profile.username or ""
            except Exception as exc:
                LOG.warning("Cannot resolve bot username for site: %s", exc)
        # Update the Telegram display name carefully to avoid flood limits on every restart.
        # Bot API cannot change @username; that is managed separately in BotFather.
        await sync_bot_profile(bot)
        await bot.set_my_commands([
            BotCommand(command="start", description="Открыть Still VPN"),
            BotCommand(command="profile", description="Профиль"),
            BotCommand(command="plans", description="Тарифы"),
            BotCommand(command="connect", description="Подключение"),
            BotCommand(command="support", description="Поддержка"),
            BotCommand(command="help", description="Помощь и ссылки"),
            BotCommand(command="terms", description="Условия"),
            BotCommand(command="linkweb", description="Связать аккаунт с сайтом"),
            BotCommand(command="invite", description="Пригласить друга"),
        ])
        tasks = [asyncio.create_task(dp.start_polling(bot)), asyncio.create_task(periodic_worker())]
        try:
            yield
        finally:
            for task in tasks: task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await bot.session.close()
            await engine.dispose()
    app.router.lifespan_context = lifespan_app

else:
    # Agent mode. NO bot token or application database access is needed on the VPN VPS.
    app = FastAPI(title="Still WireGuard Agent", docs_url=None, redoc_url=None, openapi_url=None)
    used_nonces: dict[str, float] = {}
    lease_lock = asyncio.Lock()
    peer_leases: dict[str, dict[str, Any]] = {}
    SAFE_WG_IFACE = re.compile(r"[a-zA-Z0-9_.\-]{1,15}$")
    if not SAFE_WG_IFACE.fullmatch(WG_INTERFACE):
        raise RuntimeError("Invalid WG_INTERFACE")

    class PeerChange(BaseModel):
        public_key: str
        ip: str
        allow: bool
        expires_at: int | None = None

    async def require_agent(request: Request) -> None:
        if len(WG_AGENT_SECRET) < 32: bad(503, "Secret not configured")
        raw = await request.body()
        ts = request.headers.get("x-shade-ts", "")
        nonce = request.headers.get("x-shade-nonce", "")
        sig = request.headers.get("x-shade-sign", "")
        try:
            if abs(time.time() - int(ts)) > 30: raise ValueError
            if not re.fullmatch(r"[0-9a-f]{32}", nonce): raise ValueError
        except ValueError:
            bad(403, "Invalid timestamp/nonce")
        expected = hmac.new(WG_AGENT_SECRET.encode(), b"\n".join([
            ts.encode(), nonce.encode(), request.method.encode(), request.url.path.encode(), raw
        ]), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): bad(403, "Invalid signature")
        t = time.monotonic()
        for k, v in list(used_nonces.items()):
            if t - v > 65: del used_nonces[k]
        if nonce in used_nonces: bad(403, "Replay")
        used_nonces[nonce] = t

    def wg(*args: str) -> str:
        try:
            p = subprocess.run(["wg", *args], check=True, capture_output=True, text=True,
                               timeout=10)
            return p.stdout
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            LOG.exception("WireGuard command failed")
            bad(503, "WireGuard unavailable")

    def read_peer_leases() -> dict[str, dict[str, Any]]:
        if not WG_AGENT_LEASE_PATH.exists():
            return {}
        try:
            raw = json.loads(WG_AGENT_LEASE_PATH.read_text())
            if not isinstance(raw, dict):
                raise ValueError("lease file is not an object")
            result = {}
            for key, obj in raw.items():
                if not (validate_wg_key(key) and isinstance(obj, dict)
                        and isinstance(obj.get("expires_at"), int)
                        and isinstance(obj.get("ip"), str)):
                    continue
                result[key] = {"expires_at": obj["expires_at"], "ip": obj["ip"]}
            return result
        except (OSError, ValueError, TypeError) as exc:
            LOG.error("Agent lease file invalid. Failing closed: %s", exc)
            return {}

    def save_peer_leases() -> None:
        WG_AGENT_LEASE_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = WG_AGENT_LEASE_PATH.with_name(WG_AGENT_LEASE_PATH.name + ".tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(tmp, flags, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(peer_leases, handle, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, WG_AGENT_LEASE_PATH)
            os.chmod(WG_AGENT_LEASE_PATH, 0o600)
        finally:
            if tmp.exists():
                tmp.unlink()

    async def sweep_peer_leases() -> None:
        # Only use a DEDICATED managed wg0 interface. Peers not present in the
        # authorized lease file are removed on startup or expiry.
        async with lease_lock:
            current = set(wg("show", WG_INTERFACE, "peers").split())
            ts = int(time.time())
            for pub in current:
                lease = peer_leases.get(pub)
                if not lease or lease["expires_at"] <= ts:
                    wg("set", WG_INTERFACE, "peer", pub, "remove")
                    peer_leases.pop(pub, None)
            for pub, lease in list(peer_leases.items()):
                if lease["expires_at"] <= ts:
                    peer_leases.pop(pub, None)
            save_peer_leases()

    async def peer_lease_worker() -> None:
        while True:
            try:
                await sweep_peer_leases()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("Peer expiry sweep failed")
            await asyncio.sleep(15)

    @app.post("/agent/peer", dependencies=[Depends(require_agent)])
    async def agent_peer(change: PeerChange):
        if not validate_wg_key(change.public_key): bad(422, "Invalid public key")
        try:
            ip = ipaddress.ip_address(change.ip)
            network = ipaddress.ip_network(WG_SERVER_CIDR, strict=False)
            if (ip.version != 4 or network.version != 4 or ip not in network
                    or ip in (network.network_address, network.broadcast_address,
                              network.network_address + 1)):
                raise ValueError
        except ValueError:
            bad(422, "Invalid internal peer IP")
        async with lease_lock:
            if change.allow:
                ts = int(time.time())
                expires = min(change.expires_at or ts + WG_PEER_LEASE_SECONDS,
                              ts + WG_PEER_LEASE_SECONDS)
                if expires <= ts:
                    bad(409, "Access already expired")
                wg("set", WG_INTERFACE, "peer", change.public_key, "allowed-ips", str(ip) + "/32")
                peer_leases[change.public_key] = {"ip": str(ip), "expires_at": expires}
                try:
                    save_peer_leases()
                except Exception:
                    # Never keep an active peer whose expiry cannot be persisted.
                    wg("set", WG_INTERFACE, "peer", change.public_key, "remove")
                    peer_leases.pop(change.public_key, None)
                    raise
            else:
                wg("set", WG_INTERFACE, "peer", change.public_key, "remove")
                peer_leases.pop(change.public_key, None)
                save_peer_leases()
        return {"ok": True}

    @app.get("/agent/stats", dependencies=[Depends(require_agent)])
    async def agent_stats():
        rows = wg("show", WG_INTERFACE, "dump").splitlines()
        peers = []
        for line in rows[1:]:
            columns = line.split("\t")
            if len(columns) >= 8:
                peers.append({"public_key": columns[0], "handshake": int(columns[4]),
                              "rx": int(columns[5]), "tx": int(columns[6])})
        mem = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith(("MemTotal:", "MemAvailable:")):
                        k, val = line.split(":", 1)
                        mem[k] = int(val.strip().split()[0]) * 1024
        except OSError: pass
        disk = os.statvfs("/")
        cpu_percent = None
        network_rx = network_tx = None
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.15)
            counters = psutil.net_io_counters()
            network_rx, network_tx = counters.bytes_recv, counters.bytes_sent
        except (ImportError, OSError):
            pass
        return {"agent_version": "4", "peers": peers, "load_average": os.getloadavg()[0],
                "cpu_percent": cpu_percent, "memory": mem,
                "network_rx": network_rx, "network_tx": network_tx,
                "disk_free": disk.f_bavail * disk.f_frsize}

    @app.get("/health")
    async def agent_health():
        wg("show", WG_INTERFACE, "public-key")
        return {"status": "ok", "interface": WG_INTERFACE}

    @asynccontextmanager
    async def lifespan_agent(a: FastAPI):
        peer_leases.update(read_peer_leases())
        # On rollout unknown existing peers are revoked once; BotHost renews
        # authorized devices during its periodic reconciliation.
        await sweep_peer_leases()
        task = asyncio.create_task(peer_lease_worker())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    app.router.lifespan_context = lifespan_agent

# Telegram Web App UI is intentionally embedded here to honor the one-file request.
# All data comes from the authenticated API; no fake subscriptions or statistics.
STILL_WEB_HTML = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#100D11">
<title>Still VPN — VPN для Android, iPhone и компьютера | WireGuard</title>
<meta name="description" content="Still VPN — VPN на WireGuard с сервером в Нидерландах. Подключение через Telegram, тарифы и личный кабинет для Android, iPhone, Windows и macOS.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="__STILL_CANONICAL__">
<meta property="og:type" content="website"><meta property="og:site_name" content="Still VPN">
<meta property="og:title" content="Still VPN — защищённое VPN-подключение на WireGuard">
<meta property="og:description" content="VPN через Telegram и личный кабинет. Нидерланды, Android, iPhone и компьютер.">
<meta property="og:url" content="__STILL_CANONICAL__">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Still VPN","url":"__STILL_CANONICAL__","inLanguage":"ru"}</script>
<meta name="still-release" content="10.0.0">
<style>
:root{--bg:#100D11;--panel:#191217;--red:#681A29;--red2:#42131F;--violet:#76558D;--ink:#F3EEF0;--muted:#A99DA4;--line:rgba(243,238,240,.12);--green:#96c8af}
*{box-sizing:border-box}html{scroll-behavior:smooth}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink)}
body{font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;letter-spacing:-.012em}button,input,select{font:inherit}button{cursor:pointer}button:disabled{opacity:.45;cursor:not-allowed}a{color:inherit;text-decoration:none}a:hover{color:#ded0e6}
::selection{background:#76558D;color:#fff}:focus-visible{outline:2px solid #a77cbf;outline-offset:3px}
header{height:81px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;max-width:1160px;margin:auto;padding:0 32px;gap:20px}
.logotype{display:flex;align-items:center;gap:13px;font-weight:750;font-size:19px;letter-spacing:.19em;white-space:nowrap}.iconmark{height:28px;width:28px;display:inline-block;border-radius:8px 8px 3px 8px;background:#681A29;transform:rotate(-28deg);position:relative;overflow:hidden}.iconmark:after{content:"";position:absolute;background:#100D11;width:19px;height:23px;top:-7px;left:14px;border-radius:50%}
.micro{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.17em;font-weight:650}
.topnav{display:flex;align-items:center;gap:30px;font-size:13px;color:var(--muted)}.topnav a:hover{color:white}.pill-link{border:1px solid var(--line);padding:10px 15px;border-radius:9px;color:var(--ink);font-size:12px;white-space:nowrap}
.shell{max-width:1150px;margin:0 auto;padding:62px 32px 120px}.kicker{font-size:11px;letter-spacing:.19em;text-transform:uppercase;color:#ae90bd;font-weight:720;margin:0 0 15px}
h1{font-size:clamp(36px,5.7vw,70px);line-height:1.04;letter-spacing:-.059em;font-weight:640;margin:0 0 20px;max-width:860px}h2{font-size:clamp(26px,3.2vw,38px);line-height:1.15;letter-spacing:-.045em;margin:0 0 12px;font-weight:630}h3{font-size:17px;letter-spacing:-.02em;margin:0 0 8px;font-weight:660}p{margin:0 0 14px}.muted{color:var(--muted)}.lead{font-size:clamp(15px,1.65vw,19px);line-height:1.6;color:#c2b6bd;max-width:580px}
.status-dot{width:7px;height:7px;display:inline-block;border-radius:50%;background:#a9cab5;margin-right:9px;box-shadow:0 0 0 3px #a9cab522}.eyebrow{display:inline-flex;align-items:center;padding:7px 12px;border:1px solid var(--line);color:#c2b6bd;border-radius:100px;font-size:12px;gap:7px}
.cta{border:1px solid #873449;background:#681A29;border-radius:10px;padding:12px 19px;color:#fff;font-weight:660;font-size:14px;display:inline-flex;justify-content:center;align-items:center;gap:8px;min-height:46px}.cta:hover{background:#7b2536;color:white}.cta.outline{background:transparent;border:1px solid #56404a;color:var(--ink)}.cta.outline:hover{background:#251b23}.cta.tiny{font-size:12px;padding:9px 13px;min-height:36px}.cta.danger{background:transparent;border-color:#8a3a4d;color:#f2afb8}.cta.plain{background:transparent;border-color:transparent;color:#baa0ca;padding-left:0}.buttons{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
.intro{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:50px;align-items:center;min-height:440px;border-bottom:1px solid var(--line);padding-bottom:60px}.intro-art{height:295px;border-radius:18px;background:#171116;display:grid;place-items:center;position:relative;overflow:hidden;border:1px solid var(--line)}.intro-art:before{content:"";position:absolute;width:230px;height:230px;border:1px solid #5d3040;border-radius:50%;transform:translate(12px,8px)}.intro-art:after{content:"";position:absolute;width:150px;height:150px;border:1px solid #533044;border-radius:50%;transform:translate(12px,8px)}.intro-art .symbol{width:88px;height:88px;background:#681A29;border-radius:25px 25px 7px 25px;transform:rotate(-30deg);position:relative;overflow:hidden;z-index:1}.intro-art .symbol:after{content:"";position:absolute;background:#171116;width:65px;height:72px;top:-22px;left:48px;border-radius:50%}.intro-art .sidenote{position:absolute;left:22px;bottom:20px;letter-spacing:.13em;font-size:10px;color:#a99da4}
.intro-list{display:grid;grid-template-columns:repeat(3,1fr);gap:27px;padding:26px 0 0}.intro-list div{padding-right:15px}.intro-list strong{font-size:13px;display:block;margin-bottom:5px;font-weight:660}.intro-list p{font-size:12px;color:var(--muted)}
.auth-shell{max-width:510px;margin:auto;border-top:1px solid #694052;padding:32px 0 0}.auth-head{margin-bottom:25px}.auth-tabs{display:flex;gap:24px;border-bottom:1px solid var(--line);margin:0 0 25px}.auth-tabs button{background:none;border:0;color:var(--muted);padding:0 0 13px;border-bottom:2px solid transparent;font-weight:590;font-size:14px}.auth-tabs button.active{border-bottom-color:#a15d74;color:#fff}
.field{display:block;margin:15px 0}.field span{display:block;color:#c8bbc4;font-size:12px;margin-bottom:6px}.field input,.field select{width:100%;background:#1b151a;border:1px solid #43343e;color:var(--ink);padding:12px 13px;min-height:47px;border-radius:9px;outline:none}.field input:focus,.field select:focus{border-color:#916d9b}.field input::placeholder{color:#7c717b}input[type=checkbox]{accent-color:#86536d}.small{font-size:12px;line-height:1.55}.hint{color:var(--muted);font-size:12px}.notice{background:#241921;border:1px solid #503348;color:#dbbccc;border-radius:11px;padding:13px 15px;margin:16px 0;font-size:13px;line-height:1.5}.notice.bad{border-color:#86324a;background:#2d1720;color:#f6bccb}.notice.good{border-color:#426453;background:#17241d;color:#b8e1c7}
.hidden{display:none!important}.subnav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:42px;padding-bottom:20px;border-bottom:1px solid var(--line)}.subnav button{font-size:13px;color:var(--muted);background:transparent;border:1px solid transparent;border-radius:9px;padding:10px 16px}.subnav button.active{background:#21181f;border-color:#44303b;color:#fff}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:48px}.side{border-top:1px solid var(--line);padding-top:21px}.side .note{padding:0 0 20px;margin:0 0 21px;border-bottom:1px solid var(--line)}.side b{font-size:13px;display:block;margin-bottom:7px}.side p{font-size:12px;color:var(--muted)}
.overview{background:#1a1318;border:1px solid #442733;border-radius:16px;padding:27px 28px;margin:28px 0 22px;position:relative;overflow:hidden}.overview::after{content:"";position:absolute;right:-80px;top:-110px;width:290px;height:260px;border:1px solid #663142;border-radius:50%;opacity:.5;pointer-events:none}.overview .eyebrow{border-color:#4d3040}.big-info{font-size:clamp(24px,3.7vw,43px);letter-spacing:-.05em;font-weight:690;margin:10px 0 2px}.listrow{border-bottom:1px solid var(--line);padding:18px 0;display:flex;justify-content:space-between;align-items:center;gap:15px;font-size:14px}.listrow:last-child{border-bottom:0}.listrow strong{text-align:right;max-width:66%;overflow-wrap:anywhere;font-weight:600}.section{margin:34px 0}.splithead{display:flex;gap:12px;align-items:center;justify-content:space-between}.planline{padding:25px 0;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:16px;justify-content:space-between}.planline strong{font-size:18px;letter-spacing:-.035em}.planline .price{font-size:24px;letter-spacing:-.03em;font-weight:670;white-space:nowrap}.planline .price small{font-size:12px;font-weight:400;color:var(--muted)}.line{height:1px;background:var(--line);margin:20px 0}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.center{display:flex;align-items:center;gap:9px}.indicator{font-size:12px;color:#c9a7c2;border:1px solid #4d334a;border-radius:100px;padding:5px 9px}.codebox{border:1px solid #41313b;background:#0c090c;border-radius:11px;padding:16px;white-space:pre-wrap;word-break:break-all;font:12px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;max-height:330px;overflow:auto;color:#e1dce0}.progress{height:4px;border-radius:20px;background:#3f2c37;overflow:hidden;margin:13px 0 0}.progress i{height:100%;background:#9a6075;display:block;border-radius:20px}
.device{padding:22px 0;border-bottom:1px solid var(--line)}.device:first-child{border-top:1px solid var(--line)}.devicehead{display:flex;justify-content:space-between;gap:12px}.device .buttons{margin-top:12px}.chip{color:#c3b6bd;font-size:11px;border:1px solid var(--line);border-radius:18px;padding:4px 9px;height:fit-content;white-space:nowrap}.config-output{margin:20px 0;padding:24px;border:1px solid #614050;background:#1a131a;border-radius:12px}.panel{border:1px solid var(--line);background:#191217;padding:23px;border-radius:13px;margin:20px 0}.empty{font-size:13px;color:var(--muted);padding:26px 0;border-bottom:1px solid var(--line)}
#toast{position:fixed;top:24px;right:24px;background:#321e2b;border:1px solid #624055;color:white;padding:13px 17px;border-radius:10px;font-size:13px;z-index:999;display:none;max-width:calc(100% - 40px)}
footer{border-top:1px solid var(--line);margin-top:80px;padding:29px 0;display:flex;justify-content:space-between;gap:20px;color:var(--muted);font-size:12px;flex-wrap:wrap}
@media(max-width:820px){.intro{grid-template-columns:1fr;gap:24px;min-height:0}.intro-art{height:180px;max-width:100%}.intro-art:before{width:170px;height:170px}.intro-art:after{width:100px;height:100px}.intro-art .symbol{width:65px;height:65px}.layout{grid-template-columns:1fr}.side{display:none}.intro-list{gap:16px}.shell{padding:39px 22px 110px}header{height:72px;padding:0 22px}.topnav{gap:13px}.topnav .hide-mobile{display:none}}
@media(max-width:520px){.micro.desktop{display:none}.logotype{font-size:17px}.pill-link{padding:8px 10px;font-size:11px}.intro-list{grid-template-columns:1fr;gap:3px}.intro-list div{padding:9px 0;border-bottom:1px solid var(--line)}.intro-art{height:145px}.intro{padding-bottom:35px}.shell{padding-top:30px}.subnav{display:grid;grid-template-columns:repeat(4,1fr);gap:0}.subnav button{font-size:11px;padding:10px 3px}.overview{padding:22px 18px}.grid2{grid-template-columns:1fr}.planline{align-items:flex-start}.listrow strong{font-size:13px}.buttons .cta{width:100%}h1{font-size:36px}}
@media(prefers-reduced-motion:no-preference){.cta,.subnav button{transition:background .14s,border-color .14s}}

/* STILL / EDITION 10 — asymmetric editorial layout, measured type, data-first member pages. */
:root{--trim:#a96a7e}
body{font-feature-settings:"tnum" 1}
header{max-width:1260px}.shell{max-width:1210px;padding-top:48px}
.logotype{letter-spacing:.24em;font-weight:720}.topnav{gap:23px}
h1{font-weight:570;letter-spacing:-.065em;line-height:1.03}
.intro{grid-template-columns:minmax(0,1fr) 360px;gap:8vw;min-height:540px;align-items:start;padding-top:40px;padding-bottom:58px}
.intro-copy{padding:28px 0 6px}.intro h1{max-width:790px;font-size:clamp(47px,6.4vw,84px);margin:24px 0 25px}
.intro h1 em{font-style:normal;color:#b77c91}
.intro .lead{max-width:525px;font-size:16px;line-height:1.85}
.intro-footnote{margin-top:31px;font-size:11px;letter-spacing:.07em;color:var(--muted)}
.intro-art{height:auto;min-height:412px;display:block;overflow:hidden;border:1px solid #422f3c;border-radius:4px;background:#161116;padding:27px 25px}
.intro-art::before,.intro-art::after{display:none!important}
.workflow-title{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #4b3642;padding-bottom:22px;gap:6px}
.workflow-tag{color:#927f8c;font:11px ui-monospace,monospace;white-space:nowrap}
.workflow{margin:30px 0;padding:0;list-style:none;counter-reset:none}
.workflow li{display:grid;grid-template-columns:37px 1fr;align-items:start;gap:17px;padding:18px 0 20px;border-bottom:1px solid #32272f}
.workflow li:last-child{border-bottom:0}
.workflow strong{display:block;font-size:16px;font-weight:580;line-height:1.5}.workflow small{color:var(--muted);font-size:12px;display:block;margin-top:3px}
.step-no{font:12px ui-monospace,monospace;color:#a37388;padding-top:4px}
.workflow-bottom{display:block;border-top:1px solid #4b3642;padding-top:18px;margin-top:7px;color:#95818d;font-size:10px;letter-spacing:.15em}
.intro-list{border-bottom:1px solid var(--line);grid-template-columns:repeat(3,1fr);gap:12px;padding:21px 0}
.intro-list div{padding:10px 22px 7px 0;border-right:1px solid var(--line)}.intro-list div:last-child{border-right:0}
.intro-list strong{font-size:12px;letter-spacing:.01em}.intro-list p{font-size:12px;line-height:1.5}
.auth-shell{margin-top:90px}
.subnav{gap:4px}.subnav button{border-radius:5px;padding:10px 14px}
.overview{border:0;border-left:2px solid #774056;border-radius:0;padding:23px 22px;background:#191217}
.overview::after{display:none!important}
.big-info{font-size:clamp(30px,3.9vw,52px);font-weight:590}
.planline{padding:27px 0}.planline strong{font-weight:600}
.panel{background:#141015;border-radius:9px}
.cta{border-radius:7px;font-weight:600}.pill-link{border-radius:6px}
.listrow strong{font-variant-numeric:tabular-nums}
.site-subtitle{border-top:1px solid var(--line);padding-top:17px;font-size:12px;color:var(--muted)}
.config-output{border-radius:7px;background:#171217}
.export-row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:15px}
.export-copy{border-top:1px solid var(--line);margin-top:17px;padding-top:15px;color:var(--muted);font-size:12px;line-height:1.65}
@media(max-width:900px){.intro{grid-template-columns:1fr 320px;gap:34px;min-height:0}.intro h1{font-size:clamp(43px,6vw,67px)}}
@media(max-width:780px){.intro{grid-template-columns:1fr;gap:25px;padding-top:4px}.intro-copy{padding-top:9px}.intro-art{min-height:unset;padding:23px}.workflow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}.workflow li{display:block;padding:10px 0;border:0}.workflow strong{font-size:13px}.workflow small{font-size:11px}.step-no{display:block;margin-bottom:9px}.intro-list{grid-template-columns:1fr}.intro-list div{border-right:0;border-bottom:1px solid var(--line);padding:10px 0}.intro-list div:last-child{border:0}}
@media(max-width:520px){.shell{padding-top:24px}.intro h1{font-size:clamp(39px,11.8vw,56px)}.intro .lead{font-size:14px;line-height:1.7}.workflow{grid-template-columns:1fr}.workflow li{display:grid;grid-template-columns:29px 1fr;border-bottom:1px solid #382b35}.intro-art{padding:17px}.intro-list{gap:0}.intro-footnote{font-size:10px}.auth-shell{margin-top:52px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}

/* STILL / EDITION 10: high-contrast editorial cover, diagrammatic connection board. */
:root{--bg:#121217;--panel:#1c171e;--red:#792c43;--ink:#f4f0e8;--muted:#aa9caa;--line:rgba(242,233,231,.17)}
body{background:var(--bg)}header{height:77px}a.subtle-link{color:#ce9bb0;text-decoration:underline;text-underline-offset:4px}
.intro{align-items:stretch;grid-template-columns:minmax(0,1.12fr) minmax(270px,.78fr);min-height:570px;gap:0;padding:0;border:1px solid #4e3941;background:#eae3d7;color:#18171a;overflow:hidden;border-radius:0}
.intro-copy{padding:53px 5vw 42px 44px}.intro .kicker{color:#69283e}.intro h1{color:#1b1a1d;font-size:clamp(45px,5.6vw,82px);margin:29px 0}.intro h1 em{color:#7c2a46}.intro .lead{color:#5a5359;font-size:16px;line-height:1.73;max-width:520px}
.intro .cta{background:#75293f;border-color:#75293f;color:white}.intro .cta.outline{background:transparent;color:#2b242a;border-color:#766771}.intro .cta.outline:hover{background:#ded3c5;color:#2b242a}
.hero-small-meta{display:flex;gap:14px;flex-wrap:wrap;margin-top:42px;padding-top:18px;border-top:1px solid #cbbdb3;font-size:10px;letter-spacing:.07em;color:#6b5c64}.hero-small-meta span:not(:last-child){border-right:1px solid #b9aeb0;padding-right:14px}
.intro-art{border:0;border-left:1px solid #4f3743;border-radius:0;padding:33px 30px 26px;min-height:0;background:#1a1720;color:#f7eee9;display:flex;flex-direction:column;justify-content:space-between}
.intro-art .micro{color:#d2afb9}.route-visual{margin:57px 0 40px}.route-start{font:11px ui-monospace,monospace;letter-spacing:.13em;color:#d4b6c3}.route-line{display:block;height:130px;margin:23px 0 20px 21px;border-left:1px solid #986879;position:relative}.route-line:before,.route-line:after{content:"";position:absolute;width:8px;height:8px;border:2px solid #e6cbb7;border-radius:50%;left:-5px;top:-2px;background:#1a1720}.route-line:after{top:auto;bottom:-2px;background:#b56d7d}.route-line i{position:absolute;left:-3px;top:48%;width:5px;height:5px;background:#efdbbe;border-radius:50%}.route-end{font-size:72px;line-height:.92;letter-spacing:-.07em;font-weight:630;color:#f4eee3;display:block}.route-end small{display:block;font-size:11px;letter-spacing:.16em;font-weight:500;margin-top:15px;color:#b9a7b2}
.route-data{border-top:1px solid #4a3945;margin-top:15px}.route-data div{border-bottom:1px solid #4a3945;padding:15px 0;display:flex;gap:14px;justify-content:space-between;align-items:center}.route-data span{font-size:10px;letter-spacing:.12em;color:#9e8a9b}.route-data strong{font-size:12px;text-align:right;font-weight:570}.route-footer{padding-top:22px;display:flex;align-items:center;justify-content:space-between;font-size:11px;color:#ab99a4}.route-footer b{color:#e2a6b8;letter-spacing:.1em}
.intro-list{padding-top:33px;padding-bottom:28px}.intro-list strong{font-size:14px}.intro-list p{font-size:13px;line-height:1.65}.community-strip{margin:34px 0 72px;padding:19px 0;border-top:1px solid #65515b;border-bottom:1px solid #65515b;display:flex;gap:20px;align-items:center;flex-wrap:wrap}.community-strip span{display:flex;flex:1;min-width:190px;flex-direction:column;gap:6px}.community-strip b{font-size:12px;letter-spacing:.1em}.community-strip small{color:#aa9caa;font-size:12px}.community-strip a,.community-strip button{color:#f0cfdb;border:0;border-bottom:1px solid #8a586e;background:transparent;padding:7px 2px;font-size:13px;text-decoration:none;white-space:nowrap}
@media(max-width:900px){.intro{grid-template-columns:minmax(0,1fr) minmax(240px,.7fr)}.intro-copy{padding:43px 25px}.intro-art{min-height:450px;padding:24px}.route-visual{margin:28px 0}.route-line{height:80px}}
@media(max-width:740px){.intro{display:block}.intro h1{font-size:clamp(43px,10vw,70px)}.intro-art{display:block;min-height:auto}.route-visual{display:grid;grid-template-columns:1fr 40px 1fr;align-items:center;gap:15px;margin:24px 0}.route-start{font-size:10px}.route-line{height:1px;border:0;border-top:1px solid #986879;margin:0;position:relative}.route-line:before,.route-line:after{display:none}.route-end{font-size:41px}.route-end small{font-size:9px}.route-data{margin-top:18px}.route-data div{padding:10px 0}.intro-copy{padding:35px 21px}.hero-small-meta{margin-top:26px}}
@media(max-width:520px){.topnav{gap:8px}.topnav a{font-size:12px}.intro-copy{padding:28px 21px}.intro h1{font-size:clamp(40px,10.6vw,53px)}.intro .lead{font-size:14px}.intro .buttons .cta{width:100%}.hero-small-meta{gap:8px;font-size:9px}.hero-small-meta span:not(:last-child){padding-right:8px}.route-visual{grid-template-columns:1fr 28px 1fr}.route-end{font-size:42px}.community-strip{align-items:flex-start}.community-strip span{min-width:100%;flex:auto}}

.seo-landing{border-top:1px solid var(--line);padding-top:36px;padding-bottom:40px}.seo-landing h2{max-width:830px}.seo-landing p{max-width:800px;color:var(--muted);font-size:14px}.seo-landing a{text-decoration:underline;text-underline-offset:4px;color:#d9b7cb}
</style></head>
<body>
<header><a class="logotype" href="/web" aria-label="Still VPN — главная"><i class="iconmark" aria-hidden="true"></i>STILL <span style="font-weight:400;letter-spacing:.13em;color:#d7c6ce">VPN</span></a><span class="micro desktop">EUROPE / PRIVATE NETWORK</span><nav class="topnav"><a href="https://t.me/StillVPN_official" target="_blank" rel="noopener noreferrer">Канал ↗</a><a href="/web/terms" class="hide-mobile">Условия</a><a href="#" id="bot-link" class="pill-link hidden" target="_blank" rel="noopener noreferrer">Telegram ↗</a></nav></header>
<div id="toast" role="status" aria-live="polite"></div>
<main class="shell"><div id="guest">
<section class="intro"><div class="intro-copy"><p class="kicker">STILL / VPN WITH INTENTION — 10</p><h1>Тише снаружи.<br><em>Свободнее внутри.</em></h1><p class="lead">Интернет для твоих привычных дел. Смотри, общайся, работай — VPN на WireGuard без сложных настроек и скрытых лимитов.</p><div class="buttons"><button class="cta" id="intro-create">Начать со Still VPN <span aria-hidden="true">↗</span></button><button class="cta outline" id="intro-login">Войти в кабинет</button></div><div class="hero-small-meta"><span>01 / WireGuard</span><span>02 / Нидерланды</span><span>03 / Android · iOS · PC</span></div></div><div class="intro-art"><div class="workflow-title"><span class="micro">ВАШ МАРШРУТ</span><span class="workflow-tag">STILL / CONNECTION</span></div><div class="route-visual"><span class="route-start">УСТРОЙСТВО</span><span class="route-line"><i></i></span><span class="route-end">NL <small>НИДЕРЛАНДЫ</small></span></div><div class="route-data"><div><span>ПРОТОКОЛ</span><strong>WireGuard®</strong></div><div><span>УЗЕЛ</span><strong>Europe / NL</strong></div><div><span>НАСТРОЙКА</span><strong>Свой .conf для каждого устройства</strong></div></div><div class="route-footer"><span>Подключение на твоих условиях.</span><b>→ STILL</b></div></div></section>
<div class="intro-list"><div><strong>01 / Приватное подключение</strong><p>Уникальный WireGuard-профиль для каждого устройства. Приватный ключ отправляется только по вашему запросу в личный Telegram-чат.</p></div><div><strong>02 / Всё под контролем</strong><p>Срок подписки, трафик и список подключений всегда в кабинете.</p></div><div><strong>03 / Свой путь</strong><p>Вход через Telegram или отдельно на сайте. <a href="https://t.me/StillVPN_official" target="_blank" rel="noopener noreferrer" class="subtle-link">Следить за обновлениями ↗</a></p></div></div><div class="community-strip"><span><b>НЕ ТОЛЬКО VPN</b><small>Новости, обновления и советы — в нашем Telegram-канале.</small></span><a href="https://t.me/StillVPN_official" target="_blank" rel="noopener noreferrer">Читать канал ↗</a><button id="share-site" type="button">Поделиться Still VPN ↗</button></div>
<section class="auth-shell" id="authorization" style="margin-top:80px"><p class="kicker">ВАШ КАБИНЕТ</p><h2 id="auth-title">Вход в Still VPN</h2><div class="auth-tabs"><button data-auth="login" class="active">Вход</button><button data-auth="register">Регистрация</button><button data-auth="recover">Восстановление</button></div><form id="auth-form"><label class="field"><span>Логин</span><input id="login" name="username" minlength="3" maxlength="32" autocomplete="username" required placeholder="например, still_user"></label><label class="field hidden" id="email-field"><span>Email для подтверждения (необязательно)</span><input id="email" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com"></label><label class="field" id="password-field"><span id="password-label">Пароль</span><input id="password" type="password" minlength="12" maxlength="128" autocomplete="current-password" required placeholder="Не менее 12 символов"></label><label class="field hidden" id="recovery-field"><span>Одноразовый код восстановления</span><input id="recovery" type="text" autocomplete="off" maxlength="120" placeholder="STILL-..."></label><label class="center small hidden" id="agree-field" style="margin:17px 0"><input type="checkbox" id="agree"> <span>Принимаю <a href="/web/terms" style="text-decoration:underline">условия тестирования</a></span></label><div class="buttons"><button class="cta" id="auth-submit" type="submit">Войти в аккаунт</button></div></form><p class="hint" id="auth-hint" style="margin-top:15px">Доступ к кабинету не требует Telegram.</p><div id="auth-error" aria-live="polite"></div></section>
<section class="seo-landing" aria-label="Информация о Still VPN"><h2>VPN на WireGuard для телефона и компьютера</h2><p>Still VPN помогает настроить защищённое соединение на Android, iPhone, Windows и macOS. Управляйте подпиской, пробным доступом и устройствами в Telegram Mini App или через личный кабинет сайта. Основной VPN-сервер расположен в Нидерландах.</p><p>После создания устройства скачайте файл WireGuard (.conf) или запросите его в личном чате Telegram. Для включения VPN импортируйте файл в приложение WireGuard. Лимиты трафика, срок и количество устройств зависят от выбранного тарифа.</p><a href="https://www.wireguard.com/install/" target="_blank" rel="noopener noreferrer">Установить WireGuard ↗</a> · <a href="https://t.me/StillVPN_official" target="_blank" rel="noopener noreferrer">Канал Still VPN ↗</a></section>
</div>
<div id="member" class="hidden"><div class="subnav" id="member-nav"><button data-page="home" class="active">Обзор</button><button data-page="plans">Подписка</button><button data-page="devices">Устройства</button><button data-page="profile">Профиль</button></div><div class="layout"><section id="content" aria-live="polite"></section><aside class="side"><div class="note"><p class="kicker">STILL VPN</p><b>Кабинет без Telegram</b><p>Устройства и подписки обслуживаются тем же VPN-сервером, что и в Mini App.</p></div><div class="note"><b>Безопасность</b><p>Приватный ключ устройства генерируется в браузере. Сохраните конфигурацию сразу после создания.</p></div><div class="note"><b>Поддержка</b><p>Если Telegram недоступен, обратитесь по альтернативному контакту, указанному в условиях сервиса.</p></div></aside></div></div>

<footer><span>© Still VPN · EDITION 10 · BUILT FOR EVERYDAY CONNECTION</span><span><a href="https://t.me/StillVPN_official" target="_blank" rel="noopener noreferrer">Наш канал</a> · <a href="/web/terms">Условия и данные</a> · <span id="footer-bot"></span></span></footer>
</main>
<script>
(()=>{'use strict';
const $=q=>document.querySelector(q), $$=q=>Array.from(document.querySelectorAll(q));
let me=null,config=null,page='home',authMode='login',csrf='',devices=[],plans=[],lastConfig=null;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>v?new Date(v).toLocaleDateString('ru-RU',{day:'numeric',month:'long',year:'numeric'}):'—';
const bytes=v=>v===null||v===undefined?'Без лимита':(v/1073741824).toFixed(2)+' ГБ';
function toast(t,bad=false){const el=$('#toast');el.textContent=t;el.style.background=bad?'#681A29':'#321e2b';el.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.style.display='none',4600)}
async function api(path,options={}){const method=options.method||'GET';const r=await fetch('/web/api/'+path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...(method==='GET'?{}:{'X-CSRF-Token':csrf}),...(options.headers||{})}});let data;try{data=await r.json()}catch{throw Error('Сервер вернул непонятный ответ')};if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'Ошибка '+r.status);return data}
async function guestApi(path,body){const r=await fetch('/web/api/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let d;try{d=await r.json()}catch{throw Error('Не удалось прочитать ответ сервера')};if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Ошибка '+r.status);return d}
function showAuth(mode='login'){authMode=mode;$('#authorization').scrollIntoView({behavior:'smooth'});$$('[data-auth]').forEach(b=>b.classList.toggle('active',b.dataset.auth===mode));$('#auth-title').textContent=({login:'Вход в Still VPN',register:'Создать аккаунт',recover:'Восстановление доступа'})[mode];$('#email-field').classList.toggle('hidden',mode!=='register');$('#recovery-field').classList.toggle('hidden',mode!=='recover');$('#agree-field').classList.toggle('hidden',mode!=='register');$('#password-label').textContent=mode==='login'?'Пароль':mode==='recover'?'Новый пароль':'Придумайте пароль';$('#password').minLength=mode==='login'?1:12;$('#password').autocomplete=mode==='login'?'current-password':'new-password';$('#auth-submit').textContent=({login:'Войти в аккаунт',register:'Зарегистрироваться',recover:'Восстановить пароль'})[mode];$('#auth-error').innerHTML='';$('#auth-hint').textContent=mode==='register'?'Используйте уникальный пароль от 12 символов. Email нужен для подтверждения пробного доступа.':'Никаких обязательных входов через Telegram.'}
$$('[data-auth]').forEach(b=>b.onclick=()=>showAuth(b.dataset.auth));$('#intro-create').onclick=()=>showAuth('register');$('#intro-login').onclick=()=>showAuth('login');
$('#share-site').onclick=async()=>{const url=location.origin+'/web';try{if(navigator.share){await navigator.share({title:'Still VPN',text:'VPN для повседневного интернета',url});return}await navigator.clipboard.writeText(url);toast('Ссылка на Still VPN скопирована')}catch(e){if(e?.name!=='AbortError')toast('Ссылка: '+url)}};
function showMemberRecovery(code){
const modal=document.createElement('div');modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.85);display:grid;place-items:center;z-index:1000;padding:22px';
modal.innerHTML='<div style="width:min(100%,510px);padding:28px;background:#191217;border:1px solid #694052;border-radius:16px"><p class="kicker">БЕЗОПАСНОСТЬ</p><h2>Сохраните код восстановления</h2><p class="small muted">Код показывается только сейчас. Без него восстановить доступ при потере пароля невозможно.</p><div class="codebox" id="new-recovery-code"></div><div class="buttons"><button class="cta outline" id="recovery-copy">Скопировать</button><button class="cta" id="recovery-close">Я сохранил код</button></div></div>';
document.body.appendChild(modal);modal.querySelector('#new-recovery-code').textContent=code;modal.querySelector('#recovery-copy').onclick=()=>navigator.clipboard.writeText(code).then(()=>toast('Скопировано'),()=>toast('Ошибка буфера обмена',true));modal.querySelector('#recovery-close').onclick=()=>modal.remove();
}
function showRecovery(code){$('#auth-error').innerHTML=`<div class="notice good"><strong>Сохраните код восстановления.</strong><br>Он показывается один раз и нужен, если вы забудете пароль. Храните его вне сайта и не отправляйте никому.</div><div id="recovery-secret" class="codebox"></div><button type="button" id="recover-copy" class="cta outline tiny">Скопировать код</button>`;$('#recovery-secret').textContent=code;$('#recover-copy').onclick=()=>navigator.clipboard.writeText(code).then(()=>toast('Код скопирован'),()=>toast('Не удалось скопировать',true))}
$('#auth-form').onsubmit=async e=>{e.preventDefault();const btn=$('#auth-submit');btn.disabled=true;$('#auth-error').innerHTML='';try{const login=$('#login').value.trim().toLowerCase(),password=$('#password').value;let d;
if(authMode==='register'){d=await guestApi('register',{login,password,email:$('#email').value.trim()||null,agreed:$('#agree').checked});csrf=d.csrf;await loadMe(true);showMemberRecovery(d.recovery_code);return}
if(authMode==='login'){d=await guestApi('login',{login,password});csrf=d.csrf;await loadMe(true);return}
d=await guestApi('password/recover',{login,recovery_code:$('#recovery').value.trim(),new_password:password});showRecovery(d.recovery_code);toast('Пароль заменён. Войдите с новым паролем.');return;
}catch(err){$('#auth-error').innerHTML=`<div class="notice bad">${esc(err.message)}</div>`}finally{btn.disabled=false}};
async function loadMe(activate=false){try{me=await api('me');csrf=me.csrf;$('#guest').classList.add('hidden');$('#member').classList.remove('hidden');if(activate)page='home';render();}catch(e){if(e.message.includes('Войдите')||e.message.includes('Сессия')){me=null;$('#member').classList.add('hidden');$('#guest').classList.remove('hidden')}else toast(e.message,true)}}
$$('[data-page]').forEach(b=>b.onclick=()=>nav(b.dataset.page));function nav(p){page=p;$$('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===p));render();window.scrollTo({top:0,behavior:'smooth'})}
function subhead(k,title,desc=''){return `<p class="kicker">${esc(k)}</p><h1 style="font-size:clamp(30px,4.5vw,53px)">${esc(title)}</h1><p class="lead">${esc(desc)}</p>`}
function render(){if(!me)return;const c=$('#content');if(page==='home')home(c);else if(page==='plans')plansPage(c);else if(page==='devices')devicesPage(c);else profilePage(c)}
function home(c){const s=me.subscription;
const pct=(s&&s.limit!==null&&s.limit>0)?Math.min(100,Math.max(0,s.used/s.limit*100)):null;
const network=(me.service&&me.service.responsive_nodes>0)?'Сервер отвечает':'Статус уточняется';
c.innerHTML=subhead('ОБЗОР / STILL VPN',`На связи, ${me.username}.`,'Ваша сеть, устройства и срок доступа — без лишних меню.')+
`<div class="overview"><div class="splithead"><span class="eyebrow"><i class="status-dot"></i>${s?'Доступ активен':'Нет активного доступа'}</span><span class="micro">АККАУНТ / ${me.id>0?'TG':'WEB'}</span></div><div class="big-info">${s?esc(s.name):'Управляйте подключением'}</div><p class="small muted">${s?'Доступ до '+date(s.end):'Выберите подписку, чтобы добавить WireGuard-устройство.'}</p>${pct!==null?`<div class="progress" role="progressbar" aria-label="Использовано трафика" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(pct)}"><i style="width:${pct}%"></i></div>`:''}</div>
<div class="listrow"><span class="muted">Израсходовано за период</span><strong>${s?bytes(s.used)+' / '+bytes(s.limit):'—'}</strong></div><div class="listrow"><span class="muted">Устройства</span><strong>${me.device_count} / ${s?s.devices:'—'}</strong></div><div class="listrow"><span class="muted">VPN-инфраструктура</span><strong>${network}</strong></div><div class="buttons"><button class="cta" id="go-connect">${s?'Перейти к устройствам':'Посмотреть тарифы'} <span aria-hidden="true">↗</span></button>${!s&&!me.trial_used&&me.can_trial?'<button class="cta outline" id="trial">Активировать пробный доступ</button>':''}</div>`;
$('#go-connect').onclick=()=>nav(s?'devices':'plans');if($('#trial'))$('#trial').onclick=async()=>{if(!confirm('Активировать единственный пробный период сейчас?'))return;try{await api('trial',{method:'POST',body:'{}'});toast('Пробный период активирован');await loadMe()}catch(e){toast(e.message,true)}}
}
async function plansPage(c){c.innerHTML=subhead('ПОДПИСКА','Ваши возможности.','Тарифы и лимиты поступают из базы Still VPN.')+`<div class="notice">Оплата на отдельном сайте пока не подключена. Telegram Stars доступны только через Telegram после включения платежей. Для входа без Telegram можно использовать уже активную подписку или подарочный / промокод.</div><div id="plans-load"><p class="muted">Загрузка тарифов…</p></div><div class="section"><h3>Активировать код</h3><p class="muted small">Одноразовый подарок или промокод на дни доступа.</p><form id="redeem-form"><label class="field"><span>Ваш код</span><input id="redeem-code" maxlength="80" required placeholder="Введите код"></label><button class="cta" type="submit">Активировать</button></form></div>`;
try{plans=await api('plans');if(page!=='plans')return;$('#plans-load').innerHTML=plans.length?plans.map(p=>`<div class="planline"><div><strong>${esc(p.title)}</strong><p class="muted small">${p.days} дней · ${p.devices} устройств · ${bytes(p.traffic_bytes)}</p></div><span class="price">${p.stars} <small>Stars</small></span></div>`).join(''):'<div class="empty">Тарифы пока не опубликованы.</div>'}catch(e){toast(e.message,true)}$('#redeem-form').onsubmit=async ev=>{ev.preventDefault();try{await api('redeem',{method:'POST',body:JSON.stringify({code:$('#redeem-code').value.trim()})});toast('Код активирован');await loadMe();nav('home')}catch(e){toast(e.message,true)}}}
async function devicesPage(c){c.innerHTML=subhead('WIREGUARD','Ваши устройства.','Каждое подключение использует собственную пару ключей.')+(!me.subscription?'<div class="notice bad">Для подключения нужна активная подписка или пробный доступ.</div>':'')+`<div class="panel"><h3>Новое устройство</h3><p class="muted small">Ключ создаётся в браузере. Наш сервер получает только публичный ключ.</p><form id="device-create"><div class="grid2"><label class="field"><span>Название</span><input id="device-name" required maxlength="60" placeholder="Мой телефон" value="Мой телефон"></label><label class="field"><span>Платформа</span><select id="device-platform"><option value="android">Android</option><option value="ios">iOS</option><option value="windows">Windows</option><option value="macos">macOS</option><option value="linux">Linux</option></select></label></div><button class="cta" ${!me.subscription?'disabled':''} id="create-button" type="submit">Создать конфигурацию</button></form></div><div id="new-config"></div><div class="section"><div class="splithead"><h3>Добавленные устройства</h3><button class="cta plain tiny" id="reload-devices">Обновить ↻</button></div><div id="device-list"><p class="muted small">Загрузка…</p></div></div>`;
$('#device-create').onsubmit=createDevice;$('#reload-devices').onclick=loadDevices;loadDevices()}
async function loadDevices(){try{devices=await api('devices');if(page!=='devices')return;const box=$('#device-list');box.innerHTML=devices.length?devices.map(d=>`<div class="device"><div class="devicehead"><div><h3>${esc(d.name)}</h3><p class="muted small">${esc(d.platform)} · добавлено ${date(d.created_at)}<br>${d.last_handshake?'Последний handshake: '+date(d.last_handshake):'Нет данных о подключении'}</p></div><span class="chip">${!d.enabled?'Отозван':d.provisioned?'Выдан':'Ожидает'}</span></div>${d.enabled?`<div class="buttons"><button class="cta outline tiny" data-rename="${esc(d.id)}">Переименовать</button><button class="cta danger tiny" data-revoke="${esc(d.id)}">Отозвать</button></div>`:''}</div>`).join(''):'<div class="empty">Подключений пока нет.</div>';
$$('[data-rename]').forEach(b=>b.onclick=async()=>{const d=devices.find(x=>x.id===b.dataset.rename),name=prompt('Новое имя',d.name);if(!name)return;try{await api('devices/'+d.id,{method:'PATCH',body:JSON.stringify({name:name.trim()})});toast('Переименовано');await loadDevices()}catch(e){toast(e.message,true)}});
$$('[data-revoke]').forEach(b=>b.onclick=async()=>{if(!confirm('Отозвать доступ устройства? Старая конфигурация перестанет работать.'))return;try{await api('devices/'+b.dataset.revoke,{method:'DELETE',body:'{}'});toast('Отзыв доступа запрошен');await loadDevices();await loadMe()}catch(e){toast(e.message,true)}})}catch(e){toast(e.message,true)}}
function b64(a){return btoa(String.fromCharCode(...new Uint8Array(a)))}
async function keypair(){if(!isSecureContext||!crypto.subtle)throw Error('Для создания ключей требуется HTTPS и современный браузер');try{const kp=await crypto.subtle.generateKey({name:'X25519'},true,['deriveBits']);const pub=b64(await crypto.subtle.exportKey('raw',kp.publicKey)),der=new Uint8Array(await crypto.subtle.exportKey('pkcs8',kp.privateKey));if(der.length<32)throw Error('Invalid X25519 private key');return {pub,priv:b64(der.slice(-32))}}catch{throw Error('Этот браузер не поддерживает X25519. Используйте современный Chrome, Firefox или Safari.')}}
function saveBlobConfig(conf,filename){
 const blob=new Blob([conf],{type:'application/octet-stream'});const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),120000);
}
async function saveConfigLocally(conf,filename){
 if(typeof File==='undefined'){saveBlobConfig(conf,filename);toast('Если загрузка не появилась, используйте «Копировать».',true);return;}
 const file=new File([conf],filename,{type:'text/plain'});
 if(window.showSaveFilePicker){try{const handle=await window.showSaveFilePicker({suggestedName:filename,types:[{description:'WireGuard',accept:{'text/plain':['.conf']}}]});const out=await handle.createWritable();await out.write(file);await out.close();toast('Конфигурация сохранена');return}catch(e){if(e.name==='AbortError')return}}
 if(navigator.share&&(!navigator.canShare||navigator.canShare({files:[file]}))){try{await navigator.share({files:[file],title:'Still VPN WireGuard'});toast('Выберите локальное сохранение файла');return}catch(e){if(e.name==='AbortError')return}}
 saveBlobConfig(conf,filename);toast('Проверьте загрузки. Если файла нет, скопируйте текст в .conf вручную.',true);
}
async function createDevice(e){e.preventDefault();const button=$('#create-button');button.disabled=true;button.textContent='Создаём ключ…';try{const name=$('#device-name').value.trim(),platform=$('#device-platform').value;const kp=await keypair();const r=await api('devices',{method:'POST',body:JSON.stringify({name,platform,public_key:kp.pub})});const configText=`[Interface]\nPrivateKey = ${kp.priv}\nAddress = ${r.address}\nDNS = ${r.dns}\nMTU = 1280\n\n[Peer]\nPublicKey = ${r.server_key}\nEndpoint = ${r.endpoint}\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 25\n`;
lastConfig=configText;const box=$('#new-config');box.innerHTML=`<div class="config-output"><h3>Конфигурация создана</h3><div class="notice ${r.status==='ready'?'good':'bad'}">${r.status==='ready'?'Peer подтверждён VPN-сервером.':'VPN-сервер пока не подтвердил выдачу. Проверьте состояние устройства позже.'}</div><p class="small muted">Ключ создан локально. Если отправите .conf в Telegram, он однократно пройдёт через сервер по HTTPS и останется в вашем личном чате. Другие способы сохраняют файл локально.</p><div class="codebox" id="conf-display"></div><div class="export-row"><button class="cta tiny" id="conf-telegram">✉ Отправить .conf в личный чат</button><button class="cta outline tiny" id="conf-save">Сохранить локально</button><button class="cta outline tiny" id="conf-copy">Копировать</button><button class="cta plain tiny" id="conf-download">Обычная загрузка</button></div><p class="export-copy">Отправка в личный чат требует привязанного Telegram-аккаунта; ключ проходит через API и Telegram без сохранения в нашей базе. Приоритет приватности — локальное сохранение.</p></div>`;$('#conf-display').textContent=configText;
const configFilename='still-vpn-'+r.id.slice(0,8)+'.conf';
$('#conf-telegram').onclick=async()=>{const b=$('#conf-telegram');if(!confirm('Отправить ваш приватный ключ в Telegram? Файл останется в личном чате.'))return;b.disabled=true;b.textContent='Отправляем…';try{await api('devices/'+r.id+'/send-conf',{method:'POST',body:JSON.stringify({private_key:kp.priv})});toast('Файл отправлен в личный чат с ботом');b.textContent='✓ Отправлено в Telegram'}catch(e){toast(e.message,true);b.disabled=false;b.textContent='✉ Отправить .conf в личный чат'}};
$('#conf-save').onclick=()=>saveConfigLocally(configText,configFilename);
$('#conf-download').onclick=()=>saveBlobConfig(configText,configFilename);
$('#conf-copy').onclick=()=>navigator.clipboard.writeText(configText).then(()=>toast('Конфигурация скопирована'),()=>toast('Не удалось скопировать',true));await loadDevices();me.device_count+=1;box.scrollIntoView({behavior:'smooth'});
}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Создать конфигурацию'}}
function profilePage(c){c.innerHTML=subhead('АККАУНТ','Ваш профиль.','Простые настройки и понятный контроль доступа.')+`<div class="listrow"><span class="muted">Логин</span><strong>${esc(me.username)}</strong></div><div class="listrow"><span class="muted">Дата регистрации</span><strong>${date(me.created_at)}</strong></div><div class="listrow"><span class="muted">Email</span><strong>${esc(me.email||'Не указан')}</strong></div><div class="listrow"><span class="muted">Подтверждение email</span><strong>${me.email_verified?'Подтверждён':'Нет'}</strong></div><div class="listrow"><span class="muted">Telegram</span><strong>${me.id>0?'Связан':'Не привязан'}</strong></div><section class="section" id="email-options"></section><section class="section"><h3>Поддержка Still VPN</h3><p class="muted small">Обращения доступны здесь, даже если Telegram недоступен. Не отправляйте приватные ключи или пароли.</p><form id="ticket-form"><label class="field"><span>Опишите проблему</span><textarea id="ticket-text" maxlength="3500" minlength="5" required placeholder="Что не работает?" style="width:100%;min-height:95px;background:#1b151a;border:1px solid #43343e;border-radius:9px;color:#F3EEF0;padding:12px;font:inherit"></textarea></label><button class="cta tiny">Создать обращение</button></form><div id="my-tickets" class="section">Загрузка обращений…</div></section><section class="section"><h3>Привязка Telegram</h3><p class="muted small">Если Telegram доступен, отправьте боту /linkweb и вставьте одноразовый код. Привязка доступна только для нового веб-аккаунта без использованных подписок и VPN-профилей.</p><form id="link-form"><label class="field"><span>Код привязки</span><input id="link-code" placeholder="STILL-..." maxlength="80" required></label><button type="submit" class="cta outline tiny">Привязать Telegram</button></form></section><section class="section"><h3>Сменить пароль</h3><p class="muted small">После смены пароля все сессии будут завершены. Сохраните новый код восстановления.</p><form id="change-form"><label class="field"><span>Текущий пароль</span><input id="old-pass" type="password" required></label><label class="field"><span>Новый пароль (от 12 символов)</span><input id="new-pass" type="password" minlength="12" required></label><button class="cta outline tiny">Сменить пароль</button></form></section><div class="line"></div><button class="cta danger tiny" id="logout">Выйти из аккаунта</button>`;
if(!me.email){$('#email-options').innerHTML=`<h3>Добавить email</h3><p class="muted small">Для подтверждения пробного доступа можно привязать email. Потребуется текущий пароль.</p><form id="email-add-form"><label class="field"><span>Email</span><input id="email-new" type="email" required></label><label class="field"><span>Текущий пароль</span><input id="email-pass" type="password" required></label><button class="cta tiny">Добавить email</button></form>`;$('#email-add-form').onsubmit=async e=>{e.preventDefault();try{await api('email/update',{method:'POST',body:JSON.stringify({email:$('#email-new').value,password:$('#email-pass').value})});toast('Email добавлен. Подтвердите его.');await loadMe()}catch(e){toast(e.message,true)}}}
if(me.email&&!me.email_verified){$('#email-options').innerHTML=`<h3>Подтвердить email</h3><p class="muted small">Для бесплатного пробного доступа на сайте потребуется подтверждение почты, если эта функция включена администратором.</p><div class="buttons"><button class="cta outline tiny" id="email-send">Отправить код</button></div><form id="email-form"><label class="field"><span>Шестизначный код из письма</span><input id="email-code" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code"></label><button class="cta tiny">Подтвердить</button></form>`;$('#email-send').onclick=async()=>{try{await api('email/send',{method:'POST',body:'{}'});toast('Письмо отправлено')}catch(e){toast(e.message,true)}};$('#email-form').onsubmit=async e=>{e.preventDefault();try{await api('email/verify',{method:'POST',body:JSON.stringify({code:$('#email-code').value.trim()})});toast('Email подтверждён');await loadMe()}catch(e){toast(e.message,true)}}}
$('#ticket-form').onsubmit=async e=>{e.preventDefault();try{await api('tickets',{method:'POST',body:JSON.stringify({text:$('#ticket-text').value.trim()})});$('#ticket-text').value='';toast('Обращение создано');await loadWebTickets()}catch(e){toast(e.message,true)}};
loadWebTickets();
$('#logout').onclick=async()=>{try{await api('logout',{method:'POST',body:'{}'});me=null;csrf='';lastConfig=null;$('#member').classList.add('hidden');$('#guest').classList.remove('hidden');showAuth('login')}catch(e){toast(e.message,true)}};
$('#change-form').onsubmit=async e=>{e.preventDefault();if(!confirm('Сменить пароль и завершить все сессии?'))return;try{const d=await api('password/change',{method:'POST',body:JSON.stringify({old_password:$('#old-pass').value,new_password:$('#new-pass').value})});me=null;csrf='';$('#member').classList.add('hidden');$('#guest').classList.remove('hidden');showAuth('login');showRecovery(d.recovery_code);toast('Пароль обновлён, сохраните новый код')}catch(e){toast(e.message,true)}};
$('#link-form').onsubmit=async e=>{e.preventDefault();try{await api('link-telegram',{method:'POST',body:JSON.stringify({code:$('#link-code').value.trim()})});toast('Telegram привязан');await loadMe()}catch(e){toast(e.message,true)}}}
async function loadWebTickets(){if(page!=='profile')return;const box=$('#my-tickets');if(!box)return;try{const rows=await api('tickets');box.innerHTML=rows.length?rows.map(t=>`<div class="listrow"><span>Обращение #${t.id} <small class="muted">${esc(t.status)}</small></span><button class="cta outline tiny" data-webticket="${t.id}">Открыть</button></div>`).join(''):'<p class="small muted">Обращений пока нет.</p>';
$$('[data-webticket]').forEach(b=>b.onclick=()=>openWebTicket(Number(b.dataset.webticket)));}catch(e){box.textContent=e.message}}
async function openWebTicket(id){const box=$('#my-tickets');try{const t=await api('tickets/'+id);box.innerHTML=`<button class="cta plain tiny" id="ticket-back">← К обращениям</button><h3>Обращение #${t.id} (${esc(t.status)})</h3>`+t.messages.map(m=>`<div class="panel"><span class="small muted">${m.sender==='admin'?'Поддержка':'Вы'} · ${date(m.date)}</span><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(m.text)}</p></div>`).join('')+(t.status!=='closed'?`<form id="ticket-reply"><label class="field"><span>Ваш ответ</span><textarea id="reply-text" maxlength="3500" required style="width:100%;min-height:80px;background:#1b151a;color:#fff;padding:12px;border:1px solid #43343e;border-radius:9px"></textarea></label><button class="cta tiny">Отправить</button></form>`:'');$('#ticket-back').onclick=loadWebTickets;
if($('#ticket-reply'))$('#ticket-reply').onsubmit=async ev=>{ev.preventDefault();try{await api('tickets/'+id+'/reply',{method:'POST',body:JSON.stringify({text:$('#reply-text').value.trim()})});await openWebTicket(id)}catch(e){toast(e.message,true)}};
}catch(e){toast(e.message,true)}}
async function init(){try{config=await api('config');if(config.bot_url){const b=$('#bot-link');b.href=config.bot_url;b.classList.remove('hidden');$('#footer-bot').innerHTML=`<a target="_blank" rel="noopener noreferrer" href="${esc(config.bot_url)}">Открыть Telegram-бота ↗</a>`}if(!config.registration_enabled){$$('[data-auth="register"]').forEach(x=>x.disabled=true);$('#intro-create').disabled=true}await loadMe()}catch(e){toast(e.message,true)}}
init();
})();
</script></body></html>"""

MINI_APP_HTML = r"""<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>STILL VPN / EDITION 11</title><meta name="still-release" content="11.0.0"><meta name="robots" content="noindex,nofollow">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<style>
:root{color-scheme:dark;--bg:#100D11;--soft:#191217;--red:#681A29;--deep:#42131F;--violet:#76558D;--ink:#F3EEF0;--muted:#A99DA4;--hair:rgba(243,238,240,.095)}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink)}
body{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;letter-spacing:-.015em}
button,input,select{font:inherit}button{cursor:pointer;touch-action:manipulation}button:disabled{opacity:.42;cursor:default}
#app{max-width:620px;margin:0 auto;min-height:100dvh;padding:calc(env(safe-area-inset-top) + 26px) 22px calc(env(safe-area-inset-bottom) + 106px)}
.top{display:flex;align-items:center;justify-content:space-between;margin-bottom:43px}
.wordmark{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:800;letter-spacing:.20em}
.mark{width:24px;height:24px;border-radius:7px 7px 3px 7px;background:var(--red);transform:rotate(-24deg);position:relative}
.mark:after{content:"";position:absolute;width:16px;height:18px;background:var(--bg);top:-5px;left:11px;border-radius:50%}
.kicker{font-size:11px;font-weight:700;letter-spacing:.17em;color:var(--violet);text-transform:uppercase;margin:0 0 12px}
h1{font-size:clamp(30px,8vw,43px);letter-spacing:-.052em;line-height:1.06;margin:0 0 12px;font-weight:700}
h2{font-size:21px;letter-spacing:-.04em;margin:0 0 17px}h3{font-size:15px;margin:0 0 8px}
p{line-height:1.56}.muted{color:var(--muted)}.small{font-size:12px}.para{margin:0 0 23px;line-height:1.52;font-size:14px}
.hero{margin:37px 0 18px;padding:28px 23px;border:1px solid rgba(189,129,146,.16);background:radial-gradient(circle at 100% 0%,rgba(104,26,41,.25),transparent 43%),var(--soft);border-radius:18px;overflow:hidden}
.hero .big{font-size:30px;font-weight:700;letter-spacing:-.047em;margin:9px 0 3px}.subline{font-size:13px;color:var(--muted)}
.row{display:flex;justify-content:space-between;align-items:center;gap:12px}.statrow{border-bottom:1px solid var(--hair);padding:17px 0;display:flex;justify-content:space-between;gap:13px;font-size:14px}
.statrow b{font-size:14px;text-align:right}.statrow:last-child{border-bottom:0}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;background:var(--violet);margin-right:7px}
.button{display:block;width:100%;padding:15px 18px;border:1px solid #8a3348;background:var(--red);border-radius:12px;color:#fff;font-weight:700;text-align:center;font-size:14px;transition:transform .15s,background .15s}
.button:active{transform:scale(.985)}.button.secondary{background:transparent;border:1px solid var(--hair);color:var(--ink)}
.button.ghost{background:transparent;color:var(--muted);border:1px solid var(--hair)}.button.compact{padding:10px 13px;width:auto;font-size:12px;border-radius:9px}
.section{margin:27px 0 0}.line{height:1px;background:var(--hair);margin:18px 0}
.panel{border:1px solid var(--hair);background:var(--soft);border-radius:16px;padding:20px;margin:12px 0}
.plan{padding:20px 0;border-bottom:1px solid var(--hair)}.plan:last-child{border-bottom:0}
.plan .price{font-size:27px;font-weight:700;letter-spacing:-.045em}.plan .price small{font-size:13px;color:var(--muted);font-weight:400}
label{display:block;margin:14px 0 7px;color:var(--muted);font-size:12px}input,select{width:100%;padding:14px 13px;color:var(--ink);border:1px solid #49343d;background:#1c171c;border-radius:10px;outline:0;font-size:14px;min-height:46px}
input:focus,select:focus{border-color:var(--violet)}.device{border-bottom:1px solid var(--hair);padding:17px 0}.device:last-child{border:0}
.pill{font-size:11px;background:rgba(118,85,141,.14);border:1px solid rgba(118,85,141,.25);border-radius:99px;color:#bfa3cf;padding:6px 9px;white-space:nowrap}
.tabs{position:fixed;bottom:0;left:0;right:0;z-index:5;background:rgba(16,13,17,.97);border-top:1px solid var(--hair);backdrop-filter:blur(18px);padding:10px max(15px,env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) max(15px,env(safe-area-inset-left));display:flex;justify-content:space-around}
.tabs button{background:none;border:0;color:#867e85;display:flex;flex-direction:column;gap:7px;align-items:center;font-size:10px;min-width:67px;padding:4px 1px;font-weight:600}
.tabs button.active{color:var(--ink)}.tabs svg{width:21px;height:21px;stroke:currentColor;fill:none;stroke-width:1.6;stroke-linejoin:round;stroke-linecap:round}
.notice{padding:13px 15px;background:rgba(118,85,141,.13);border:1px solid rgba(118,85,141,.23);border-radius:10px;color:#ddc9e8;font-size:13px;line-height:1.5;margin:15px 0}
.error{background:rgba(104,26,41,.2);border-color:rgba(160,57,83,.5);color:#ffd1d8}
#toast{position:fixed;top:17px;left:50%;transform:translateX(-50%);max-width:calc(100vw - 32px);background:#31252f;color:#fff;padding:13px 18px;border-radius:12px;z-index:20;box-shadow:0 10px 30px #0008;font-size:13px;display:none}
.code{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid var(--hair);background:#09070a;color:#e8dde5;border-radius:12px;padding:16px;font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px;line-height:1.7;margin:13px 0}
#qr{display:flex;justify-content:center;background:white;padding:15px;border-radius:12px;width:fit-content;max-width:100%;margin:14px auto}#qr img{max-width:100%}
.link{color:#c3a1d5;text-decoration:none}a:focus,button:focus-visible{outline:2px solid var(--violet);outline-offset:2px}
/* Admin-only surfaces: compact, data-first, no decorative cards. */
.admin-head{display:flex;align-items:flex-start;justify-content:space-between;gap:15px;margin:0 0 18px}
.admin-head h1{font-size:29px;margin-bottom:4px}
.admin-nav{display:flex;overflow-x:auto;gap:8px;margin:14px -22px 20px;padding:0 22px 9px;scrollbar-width:none}
.admin-nav::-webkit-scrollbar{display:none}
.admin-nav button{flex:0 0 auto;border:1px solid var(--hair);background:transparent;color:var(--muted);border-radius:9px;padding:10px 12px;font-size:12px}
.admin-nav button.active{border-color:#794052;background:rgba(104,26,41,.19);color:var(--ink)}
.admin-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 17px;margin:8px 0 22px;border-top:1px solid var(--hair)}
.admin-metric{padding:15px 0;border-bottom:1px solid var(--hair)}
.admin-metric strong{display:block;font-size:24px;font-variant-numeric:tabular-nums;letter-spacing:-.04em;margin-top:5px}
.admin-table{margin-top:12px;border-top:1px solid var(--hair)}
.admin-item{padding:13px 0;border-bottom:1px solid var(--hair);display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.admin-item b{font-weight:600;font-size:14px}.admin-item .small{line-height:1.5}
.admin-actions{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.admin-actions button{width:auto}
.admin-form{padding:16px 0;border-top:1px solid var(--hair);margin-top:14px}
.admin-form .row{align-items:flex-end}.admin-form .row>div{min-width:0;flex:1}
.admin-form input,.admin-form select,.admin-form textarea{font-size:14px}
.admin-form textarea{width:100%;min-height:88px;background:#1c171c;color:var(--ink);border:1px solid #49343d;border-radius:10px;padding:12px;resize:vertical}
.admin-empty{color:var(--muted);font-size:13px;padding:18px 0;line-height:1.5}
.admin-filter{display:flex;gap:8px}.admin-filter input{flex:1;min-width:0}.admin-filter button{flex:0 0 auto}
.admin-status{font-size:11px;border:1px solid var(--hair);border-radius:20px;padding:5px 9px;color:var(--muted);white-space:nowrap}
.admin-status.ok{color:#b7dbc6;border-color:rgba(112,188,143,.28)}
.admin-breadcrumb{background:none;border:0;color:#c3a1d5;padding:0;font-size:12px;margin:0 0 14px}
.admin-feed{padding:0;list-style:none}.admin-feed li{padding:10px 0;border-bottom:1px solid var(--hair);font-size:13px;line-height:1.5}
.admin-trial-test{padding:19px 0;margin:14px 0;border-top:1px solid #61384b;border-bottom:1px solid var(--hair)}
.admin-trial-test h3{margin:6px 0 5px;font-size:16px}
@media(max-width:370px){.tabs button{min-width:52px;font-size:9px}.admin-form .row{flex-direction:column;align-items:stretch}}

@media(min-width:700px){.tabs{max-width:620px;margin:0 auto;border-left:1px solid var(--hair);border-right:1px solid var(--hair)}#app{padding-left:32px;padding-right:32px}}

/* STILL / SIGNAL: editorial hierarchy, quiet linework instead of decorative cards. */
:root{--signal:#b67b91}
body{font-feature-settings:"tnum" 1}
.top{padding-bottom:17px;border-bottom:1px solid var(--hair);margin-bottom:30px}
.wordmark{font-weight:760;letter-spacing:.23em;font-size:19px}
.top>.muted{font-size:9px;text-transform:uppercase;letter-spacing:.16em}
.hero{margin:24px 0 10px;padding:24px 0 22px;border:0;border-radius:0;background:transparent;border-top:2px solid #673043;border-bottom:1px solid var(--hair)}
.hero .big{font-size:clamp(29px,8.4vw,46px);line-height:1.06;letter-spacing:-.058em;font-weight:640;margin:19px 0 9px}
.hero .pill{background:transparent;border:1px solid #51404e;color:#d4c4d0}
.hero .dot{background:#94b9a6}
.statrow{padding:20px 0;align-items:flex-start;line-height:1.4}
.statrow .muted{font-size:13px}.statrow b{font-variant-numeric:tabular-nums;font-weight:580;max-width:65%}
.button{border-radius:9px;font-weight:620;min-height:48px;background:#681A29}
.button:focus-visible{outline:2px solid #b89ac6;outline-offset:3px}
.panel{border:1px solid var(--hair);background:#151116;border-radius:11px}
.plan{border-left:2px solid transparent;padding:22px 10px 22px 0}.plan:hover{border-left-color:#681A29;padding-left:10px}
.section{margin-top:32px}
.kicker{color:#b294c5;letter-spacing:.18em}
.usage-head{display:flex;justify-content:space-between;gap:10px;align-items:baseline;margin:24px 0 4px;font-size:13px;color:var(--muted)}
.usage-head strong{color:var(--ink);font-variant-numeric:tabular-nums;font-weight:620}
.usage-track{height:5px;width:100%;background:#342630;overflow:hidden;border-radius:5px}
.usage-track span{height:100%;display:block;background:#915268;border-radius:5px}
.status-rail{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--hair);padding:15px 0}
.status-rail span{font-size:12px;color:var(--muted)}.status-rail b{font-size:13px;font-weight:610}
.export-primary{border-top:1px solid var(--hair);margin-top:18px;padding-top:14px}
.export-info{font-size:12px;color:var(--muted);line-height:1.65}
.export-actions{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:9px;margin:13px 0}
.export-actions button{min-width:0;white-space:normal}
#config-text{max-height:132px;overflow:auto;color:#c6b7c2}
@media(max-width:370px){.export-actions{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

/* STILL / 08: cream signal cover, oxblood edge, no stock imagery or fake metrics. */
:root{--bg:#0f1115;--soft:#181b20;--red:#78334a;--deep:#492631;--violet:#cba0ad;--ink:#f0eae3;--muted:#aaa6ac;--hair:rgba(240,234,227,.15);--signal:#d6a19b}
body{background:var(--bg)}#app{padding-top:calc(env(safe-area-inset-top) + 19px)}
.top{border-bottom:1px solid #514049;padding-bottom:19px;margin-bottom:27px}.wordmark{letter-spacing:.18em}.mark{background:#b56c7e}.mark:after{background:var(--bg)}
.kicker{color:#d6a0ab;letter-spacing:.2em}h1{font-weight:590;letter-spacing:-.065em}.button{background:#8d4257;border-color:#9a4f64;color:white}.button.secondary{background:transparent;border-color:#55434d}.button.ghost{color:#dbc3c8}
.hero{padding:25px 23px 24px;border:0;background:#ede6da;color:#19171b;border-radius:3px;margin-top:17px;position:relative}
.hero:before{content:"";position:absolute;top:0;left:0;width:53px;height:4px;background:#8e3b54}.hero .small{color:#635b62}.hero .pill{border-color:#c3a8ad;color:#7c364d;background:transparent}.hero .dot{background:#873e56}.hero .big{color:#201b20;font-weight:650;font-size:clamp(31px,8vw,47px);line-height:1.08;margin:22px 0 9px}.hero .subline{color:#5b5358;font-size:13px}.hero-mark{display:flex;align-items:center;justify-content:space-between;gap:10px;border-bottom:1px solid #d4c8bd;padding-bottom:18px}.hero-mark small{font-size:10px;letter-spacing:.17em;color:#6c5862}.hero-number{font-size:12px;letter-spacing:.12em;color:#895269}.hero .hero-foot{display:flex;justify-content:space-between;align-items:center;border-top:1px solid #d4c8bd;margin-top:25px;padding-top:15px;font-size:11px;color:#6f666c}
.quick-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:13px 0 26px}.quick-row button{padding:16px 10px;text-align:left;min-height:94px;border:1px solid #49404a;border-radius:4px;background:#1c1b21;color:#efe5e2}.quick-row button span{display:block;font-size:11px;color:#ba929b;letter-spacing:.1em;margin-bottom:17px}.quick-row button strong{font-size:15px;letter-spacing:-.03em;font-weight:590}
.signal-card{border:1px solid #4a3c43;background:#17171c;margin:28px 0 16px;padding:20px 18px;border-radius:4px}.signal-card h2{font-size:25px;margin:5px 0 7px;font-weight:590}.signal-head{display:flex;gap:10px;align-items:center;justify-content:space-between}.signal-head .kicker{margin:0}.signal-country{font-size:14px;color:#e1d3d3}.signal-data{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;margin-top:14px}.signal-data>div{border-top:1px solid #40373d;padding:14px 0}.signal-data span{display:block;font-size:10px;color:#a79da1;letter-spacing:.1em;text-transform:uppercase}.signal-data strong{font-size:14px;font-weight:560;display:block;margin-top:7px}.signal-live{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:#b3d6bc}.signal-live:before{content:"";display:block;width:6px;height:6px;border-radius:50%;background:#87b59c}.signal-live.wait{color:#d2b59e}.signal-live.wait:before{background:#d4ae7d}
.community-box{margin:31px 0 20px;border-top:1px solid #55414b;border-bottom:1px solid #55414b;padding:21px 0}.community-box h2{margin:7px 0;font-weight:600}.community-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:19px}.community-actions button{border:1px solid #674354;background:#3c2631;color:#f5e2e8;padding:14px 10px;border-radius:5px;font-size:13px;font-weight:580}.community-actions button:nth-child(2){background:transparent;border-color:#4e4249;color:#e9dfe1}.community-actions button:nth-child(3){grid-column:span 2;background:#e7ded3;color:#272127;border-color:#e7ded3}
.edition-footer{margin-top:29px;padding:19px 0 4px;border-top:1px solid var(--hair);font:10px ui-monospace,monospace;letter-spacing:.1em;color:#8c858c;display:flex;justify-content:space-between;gap:14px}.edition-footer a{color:#cfa8b8;text-decoration:none}
.usage-track{height:5px;background:#322a30;overflow:hidden;border-radius:0}.usage-track span{display:block;background:#bd7388;height:100%}.usage-head{color:#c0b0b4}.status-rail{padding:15px 0;border-bottom:1px solid var(--hair);display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:14px}.status-rail b{font-size:13px;font-weight:560;text-align:right}
.panel{border-radius:6px;background:#1a191e}.tabs{background:rgba(15,17,21,.96)}
@media(max-width:380px){.community-actions{grid-template-columns:1fr}.community-actions button:nth-child(3){grid-column:span 1}.hero{padding:21px 17px}.signal-data{gap:0 9px}}

.vpn-control{background:linear-gradient(135deg,#241921,#151016);border:1px solid #63405b;border-radius:18px;padding:23px;margin:19px 0 27px;box-shadow:0 16px 40px #0002}
.vpn-control-head{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.vpn-control-head .kicker{margin:0}.vpn-control-main{display:flex;align-items:center;gap:16px;margin:22px 0}.vpn-control-main h2{font-size:21px;margin:0 0 7px}.vpn-control-main p{margin:0}
.vpn-power{width:76px;height:76px;flex:none;border-radius:22px;background:linear-gradient(145deg,#8e526e,#312134);border:1px solid #b37591;display:flex;align-items:center;justify-content:center;font-size:42px;color:#f5dde8;box-shadow:0 9px 27px #0004}
.vpn-how{margin-top:17px;padding-top:15px;border-top:1px solid #705064;color:var(--ink);line-height:1.6}.vpn-how p{font-size:13px;margin:0 0 12px}.vpn-how a{color:#eab9d2;text-decoration:underline}
.vpn-status-fresh{color:#c1e3ca!important;border-color:#56806b!important}.vpn-status-idle{color:#d4b8cc!important}
@media(max-width:390px){.vpn-control{padding:16px}.vpn-power{width:56px;height:56px;font-size:33px}.vpn-control-main h2{font-size:18px}}
/* STILL 11 / Support desk. No flashy gradients; readable, tactile information design. */
.tabs{justify-content:space-between;gap:2px;padding-left:9px;padding-right:9px}
.tabs button{min-width:0;flex:1 1 0;font-size:9px;white-space:nowrap;letter-spacing:-.015em}
.tabs svg{width:20px;height:20px}
.ticket-top{margin:8px 0 24px;display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.ticket-top h1{font-size:clamp(29px,8vw,43px);margin:8px 0}
.ticket-card{border:1px solid #463942;background:#1b1a20;padding:19px 17px;margin:11px 0;border-radius:8px;text-align:left;display:block;width:100%;color:var(--ink);font:inherit;cursor:pointer}
.ticket-card:focus-visible,.ticket-pill:focus-visible{outline:2px solid #d4a2b3;outline-offset:2px}
.ticket-topline{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}
.ticket-title{font-size:17px;font-weight:650;letter-spacing:-.03em;line-height:1.3;overflow-wrap:anywhere}
.ticket-meta{font-size:11px;color:#ada3ab;line-height:1.7;margin-top:6px}
.ticket-priority{display:inline-flex;align-items:center;gap:7px;color:#e7dfde;font-size:11px;white-space:nowrap}
.ticket-dot{width:9px;height:9px;display:inline-block;border-radius:50%;background:#81bf99;box-shadow:0 0 0 3px #81bf9917;flex:none}
.ticket-dot.medium{background:#e2b46c;box-shadow:0 0 0 3px #e2b46c21}
.ticket-dot.critical{background:#e67a83;box-shadow:0 0 0 3px #e67a8320}
.ticket-state{font-size:10px;letter-spacing:.035em;text-transform:uppercase;color:#d9c4c7;border:1px solid #634d55;border-radius:3px;padding:5px 7px;white-space:nowrap}
.ticket-state.answered{border-color:#74887b;color:#bed9c5}.ticket-state.closed{color:#98929c;border-color:#423e43}
.ticket-controls{display:flex;gap:8px;flex-wrap:wrap;margin:17px 0}
.ticket-controls button{flex:1;min-width:90px}
.ticket-form{background:#1d1b22;border:1px solid #514049;border-radius:9px;padding:19px 17px;margin:18px 0}
.ticket-form label,.ticket-form>label{display:block;font-size:12px;color:#d5ccd1;margin:15px 0 7px}
.ticket-form input,.ticket-form textarea,.ticket-form select{width:100%;font:inherit;color:#f3ecec;background:#131319;border:1px solid #54454d;border-radius:5px;padding:12px;box-sizing:border-box;outline-offset:2px}
.ticket-form textarea{min-height:130px;resize:vertical;line-height:1.5}
.ticket-form input:focus,.ticket-form textarea:focus{border-color:#c78ea3}
.ticket-priority-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin:12px 0}
.ticket-priority-grid label{min-width:0;margin:0;border:1px solid #52434b;border-radius:5px;padding:11px 6px;display:flex;flex-direction:column;align-items:flex-start;gap:10px;font-size:11px;cursor:pointer;line-height:1.3}
.ticket-priority-grid label:has(input:checked){background:#392b34;border-color:#bd8498}
.ticket-priority-grid input{position:absolute;opacity:0;width:1px;height:1px;padding:0}
.ticket-priority-grid input:focus-visible+span{outline:2px solid #f2d6e0}
.ticket-priority-grid label span{display:flex;align-items:center;gap:7px}
.ticket-chat{border-left:1px solid #4a3b45;padding:9px 0 11px 18px;margin:18px 0;min-height:80px}
.ticket-bubble{padding:13px 15px;border:1px solid #443941;background:#1c1a20;border-radius:7px;margin:0 0 12px;overflow-wrap:anywhere}
.ticket-bubble.staff{background:#292029;border-color:#735467}
.ticket-bubble .byline{font-size:11px;color:#b2a5ac;display:flex;justify-content:space-between;gap:9px;margin-bottom:8px}
.ticket-bubble p{margin:0;white-space:pre-wrap;line-height:1.6;font-size:14px}
.ticket-intro{font-size:13px;color:var(--muted);line-height:1.6;border-top:1px solid #4d3d46;padding-top:14px}
.ticket-filter{display:flex;gap:7px;overflow-x:auto;padding:4px 0 12px;margin:10px 0}
.ticket-filter button{flex:none;background:transparent;border:1px solid #55434c;border-radius:22px;color:#d5c9cd;padding:9px 14px;font:inherit;font-size:12px}
.ticket-filter button.active{background:#e8ded7;color:#261d23;border-color:#e8ded7}
.ticket-admin-filter{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0}
.ticket-admin-filter select,.ticket-admin-filter input{flex:1;min-width:100px;max-width:100%;background:#1d1a20;border:1px solid #53424c;border-radius:5px;color:#e8dfe3;padding:11px;font:inherit;font-size:12px}
.ticket-admin-note{padding:12px 14px;border-left:3px solid #ac748b;background:#261e26;font-size:12px;color:#d9c5cd;line-height:1.55}
@media(max-width:370px){.ticket-priority-grid{grid-template-columns:1fr}.ticket-priority-grid label{flex-direction:row;align-items:center}.ticket-priority-grid label span{gap:8px}}
</style></head>
<body><div id="toast" role="status" aria-live="polite"></div>
<div id="app"><div class="top"><div class="wordmark"><i class="mark"></i>STILL</div><span class="muted small">VPN / EDITION 11</span></div><main id="main"><p class="muted">Подключаем Still VPN…</p></main></div>
<nav class="tabs" id="tabs" aria-label="Разделы"></nav>
<script>
(()=>{
'use strict';
const tg=window.Telegram?.WebApp;tg?.ready();tg?.expand();
const $=s=>document.querySelector(s), main=$('#main'), tabs=$('#tabs');
let page='home', me=null, plans=[], devices=[], payments=[], gifts=[], currentConfig=null;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const day=x=>new Date(x).toLocaleDateString('ru-RU',{day:'2-digit',month:'long',year:'numeric'});
const gb=x=>x===null||x===undefined?'Без лимита':(x/(1024**3)).toFixed(x?2:0)+' ГБ';
function toast(text,err=false){const el=$('#toast');el.textContent=text;el.style.background=err?'#681A29':'#31252f';el.style.display='block';clearTimeout(toast._t);toast._t=setTimeout(()=>el.style.display='none',3900)}
async function api(path,opts={}){
 if(!tg?.initData)throw new Error('Откройте Mini App через Telegram-бота');
 const r=await fetch('/api/'+path,{...opts,headers:{'Content-Type':'application/json','X-Telegram-Init-Data':tg.initData,...opts.headers}});
 let out;try{out=await r.json()}catch{throw new Error('Ответ сервера не прочитан')}
 if(!r.ok){const d=out.detail;throw new Error(typeof d==='string'?d:'Ошибка запроса '+r.status)}return out;
}
function nav(to){page=to;currentConfig=null;drawTabs();render();window.scrollTo(0,0)}
const icons={tickets:'<path d="M4 4h16v13H8l-4 3z"/><path d="M8 9h8M8 13h5"/>',admin:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 10v10"/>',home:'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',plans:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/>',connect:'<circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-5"/>',account:'<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3-6 8-6s8 2 8 6"/>'};
function drawTabs(){const items=[['home','Главная'],['plans','Тарифы'],['connect','VPN'],['tickets','Тикеты'],['account','Профиль']];if(me?.admin_role)items.push(['admin','Админ']);tabs.innerHTML=items.map(([id,label])=>`<button data-nav="${id}" class="${page===id?'active':''}"><svg viewBox="0 0 24 24">${icons[id]}</svg>${label}</button>`).join('');tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>nav(b.dataset.nav))}
const section=(label,title,desc='')=>`<p class="kicker">${label}</p><h1>${title}</h1>${desc?`<p class="para muted">${desc}</p>`:''}`;
function activeText(){if(!me.subscription)return 'Нет активной подписки';const ms=new Date(me.subscription.end)-Date.now();return ms>0?Math.ceil(ms/86400000)+' дн. осталось':'Срок действия истёк'}
function render(){if(!me){main.innerHTML='<p class="muted">Подключение к Still VPN…</p>';return}
 if(page==='home')home(); else if(page==='plans')planPage(); else if(page==='connect')connectPage(); else if(page==='tickets')ticketsPage(); else if(page==='admin')adminPage(); else accountPage()}
function openOutside(url){if(!url)return;try{if(tg?.openLink){tg.openLink(url);return}}catch(e){}window.open(url,'_blank','noopener,noreferrer')}
function shareTelegram(url){if(!url)return;const href='https://t.me/share/url?url='+encodeURIComponent(url)+'&text='+encodeURIComponent('Still VPN — VPN для повседневного интернета.');try{if(tg?.openTelegramLink){tg.openTelegramLink(href);return}}catch(e){}window.open(href,'_blank','noopener,noreferrer')}
async function miniServers(){try{const list=await api('servers/public');const box=$('#server-signal');if(page!=='home'||!box)return;
if(!list.length){box.innerHTML='<p class="small muted">Нет доступных локаций. Проверяем работу сети.</p>';return}
box.innerHTML=list.map(n=>`<div class="signal-data"><div><span>Регион</span><strong>${esc(n.country)}</strong></div><div><span>Провайдер</span><strong>${esc(n.provider)}</strong></div><div><span>Протокол</span><strong>${esc(n.protocol)}</strong></div><div><span>Состояние</span><strong class="signal-live ${n.status==='online'?'':'wait'}">${n.status==='online'?'Узел доступен':'Проверяем'}</strong></div></div>`).join('');
}catch(e){const box=$('#server-signal');if(box&&page==='home')box.innerHTML='<p class="small muted">Не удалось получить актуальное состояние. Обновите страницу.</p>'}}
async function miniReferrals(){try{const r=await api('referrals');const box=$('#ref-count');if(box&&page==='home')box.textContent=`${r.registered} приглашено · ${r.paid} купили`;const btn=$('#invite-share');if(btn&&r.link){btn.onclick=()=>shareTelegram(r.link)}}catch(e){}}
function home(){const s=me.subscription;
main.innerHTML=section('STILL / ЛИЧНЫЙ КАБИНЕТ',`На связи, ${esc(me.first_name||'друг')}.`,'Твой интернет. Твои устройства. Твой ритм.')+
`<div class="hero"><div class="hero-mark"><small>ВАШЕ ПОДКЛЮЧЕНИЕ</small><span class="pill"><i class="dot"></i>${s?'Доступ активен':'Нет доступа'}</span></div>
<div class="big">${s?esc(s.name):'Начнём с подключения.'}</div><div class="subline">${s?`До ${day(s.end)} · ${activeText()}`:'Настройте пробный период или выберите подходящий тариф.'}</div><div class="hero-foot"><span>STILL / VPN</span><span class="hero-number">№ 10 — PRIVATE NETWORK</span></div></div>
<div class="quick-row"><button id="quick-connect"><span>01 / УСТРОЙСТВА</span><strong>Подключить ↗</strong></button><button id="quick-plans"><span>02 / ПОДПИСКА</span><strong>Выбрать тариф ↗</strong></button></div>
<div class="usage-head"><span>Трафик за период</span><strong>${s?gb(s.used)+' / '+gb(s.limit):'—'}</strong></div>
${s&&s.limit!==null&&s.limit>0?`<div class="usage-track" aria-label="Использовано трафика"><span style="width:${Math.min(100,Math.max(0,s.used/s.limit*100)).toFixed(1)}%"></span></div>`:''}
<div class="status-rail"><span>Устройства</span><b>${me.device_count} / ${s?s.devices:'—'}</b></div>
<div class="status-rail"><span>Работающие узлы</span><b>${me.service?.responsive_nodes||0} из ${me.service?.enabled_nodes||0}</b></div>
${!s&&!me.trial_used?'<div class="section"><button class="button" id="trial">Активировать бесплатный пробный период</button><p class="small muted">Один раз на аккаунт. Длительность и объём — по настройкам сервиса.</p></div>':''}
<div class="signal-card"><div class="signal-head"><p class="kicker">03 / СЕТЬ STILL</p><span class="signal-country">🇳🇱 NL</span></div><h2>Где находится сервер?</h2><p class="small muted">Наш основной узел находится в Нидерландах. Состояние сети обновляется по данным агента — без выдуманных показателей скорости.</p><div id="server-signal"><p class="small muted">Получаем информацию…</p></div></div>
<div class="community-box"><p class="kicker">04 / ДАЛЬШЕ ВМЕСТЕ</p><h2>Передай хорошую связь.</h2><p class="small muted">Поделись Still VPN с друзьями, следи за обновлениями и открывай сайт напрямую. Подписка на канал — по желанию.</p><div class="community-actions"><button id="invite-share">↗ Поделиться VPN</button><button id="channel-open">◈ Наш канал</button><button id="site-open">🌐 Перейти на сайт Still VPN ↗</button></div><p id="ref-count" class="small muted">Статистика приглашений загружается…</p></div>
<div class="edition-footer"><span>STILL VPN / RELEASE 10</span><a href="https://t.me/StillVPN_official" id="channel-link">CHANNEL ↗</a></div>`;
$('#quick-connect').onclick=()=>nav('connect');$('#quick-plans').onclick=()=>nav('plans');
$('#channel-open').onclick=()=>openOutside(me.channel_url||'https://t.me/StillVPN_official');
$('#site-open').onclick=()=>openOutside(me.site_url||location.origin+'/web');
$('#invite-share').onclick=()=>shareTelegram('https://t.me/StillVPNapp_bot');
$('#channel-link').onclick=e=>{e.preventDefault();openOutside(me.channel_url||'https://t.me/StillVPN_official')};
if($('#trial'))$('#trial').onclick=async()=>{try{await api('trial',{method:'POST'});toast('Пробный доступ активирован');await reload();nav('home')}catch(e){toast(e.message,true)}};
miniServers();miniReferrals();
}
function planPage(){main.innerHTML=section('Подписка','Выберите свой ритм.','Никаких скрытых параметров: цену и ограничения задаёт администратор.')+
'<div class="section"><label>Скидочный промокод (если есть)</label><input id="discount-code" maxlength="80" placeholder="Необязательно"></div><div id="plan-list"></div><div class="section"><h2>История платежей</h2><div id="history"><p class="muted small">Загрузка…</p></div></div>';
const box=$('#plan-list');if(!plans.length)box.innerHTML='<div class="notice">Тарифы пока не опубликованы администратором.</div>';
else box.innerHTML=plans.map(p=>`<div class="plan"><div class="row"><div><h2 style="margin:0 0 7px">${esc(p.title)}</h2><span class="small muted">${p.days} дней · ${p.devices} устр. · ${gb(p.traffic_bytes)}</span></div><span class="price">${p.stars} <small>⭐</small></span></div><div class="row" style="margin-top:16px"><button class="button compact" data-buy="${p.id}">Купить</button><button class="button secondary compact" data-gift="${p.id}">В подарок</button></div></div>`).join('');
box.querySelectorAll('[data-buy],[data-gift]').forEach(b=>b.onclick=()=>buy(Number(b.dataset.buy||b.dataset.gift),Boolean(b.dataset.gift)));
loadPayments();}
async function buy(planId,isGift){if(!me.payments_enabled){toast('Оплата пока не подключена. Обратитесь к администратору.',true);return}
 try{const promoCode=($('#discount-code')?.value||'').trim();const inv=await api('invoice',{method:'POST',body:JSON.stringify({plan_id:planId,kind:isGift?'gift':'subscription',promo_code:promoCode||null})});
 if(!tg.openInvoice)throw new Error('Оплата доступна только в Telegram');
 tg.openInvoice(inv.url, status=>{if(status==='paid')toast('Telegram принял '+inv.amount+' Stars. Ожидаем серверного подтверждения.');setTimeout(()=>reload(),1500)});
 }catch(e){toast(e.message,true)}}
async function loadPayments(){try{payments=await api('payments');if(page!=='plans')return;
$('#history').innerHTML=payments.length?payments.map(p=>`<div class="statrow" style="align-items:flex-start"><span><b>${esc(p.plan)}</b><br><span class="small muted">${day(p.date)} · ${p.kind==='gift'?'Подарок':'Подписка'}<br>ID ${esc(p.id)}</span></span><span><b>${p.amount} ⭐</b><br><span class="small muted">${esc(p.status)}</span></span></div>`).join(''):'<p class="muted small">Пока нет платежей.</p>';
}catch(e){toast(e.message,true)}}
function connectPage(){const e=me.subscription;
main.innerHTML=section('VPN','Ваши устройства.','Создайте профиль один раз, затем включайте и выключайте туннель через настройки телефона или WireGuard.')+
`<div class="vpn-control" id="vpn-control"><div class="vpn-control-head"><span class="kicker">STILL / СТАТУС ПОДКЛЮЧЕНИЯ</span><span id="vpn-activity" class="pill">Проверяем устройства…</span></div><div class="vpn-control-main"><div class="vpn-power" aria-hidden="true">⏻</div><div><h2>VPN под вашим контролем</h2><p class="small muted">Mini App показывает данные сервера, но не может включать системный VPN без приложения.</p></div></div><button id="vpn-how-toggle" class="button secondary compact">Как включать / выключать быстро ↗</button><div id="vpn-how" class="vpn-how" hidden><p><b>Android:</b> откройте WireGuard и активируйте профиль. Для быстрого доступа добавьте VPN в быстрые настройки или используйте совместимый виджет.</p><p><b>iPhone:</b> откройте настройки iOS → VPN или приложение WireGuard и включите конфигурацию.</p><p class="small muted">Это управление в системе устройства. Кнопка в Mini App не имитирует включение VPN.</p><a href="https://www.wireguard.com/install/" target="_blank" rel="noopener noreferrer">Установить WireGuard ↗</a></div></div>`+
(!e?'<div class="notice error">Для создания конфигурации активируйте тариф или пробный период.</div>':'')+
`<div class="panel"><h3>Новое подключение</h3><label>Название устройства</label><input id="dev-name" maxlength="60" placeholder="Мой iPhone" autocomplete="off"><label>Платформа</label><select id="dev-platform"><option value="android">Android</option><option value="ios">iOS</option><option value="windows">Windows</option><option value="macos">macOS</option><option value="linux">Linux</option></select><div style="height:18px"></div><button id="create-device" class="button" ${!e?'disabled':''}>Создать конфигурацию</button></div>`+
`<div id="new-config"></div><div class="section"><h2>Добавленные устройства</h2><div id="device-list"></div></div>`;
$('#create-device').onclick=createDevice;$('#vpn-how-toggle').onclick=()=>{$('#vpn-how').hidden=!$('#vpn-how').hidden};loadDevices();}
async function loadDevices(){try{devices=await api('devices');if(page!=='connect')return;
const indicator=$('#vpn-activity');if(indicator){const active=devices.filter(d=>d.enabled&&d.provisioned);const recent=active.some(d=>d.last_handshake&&Date.now()-new Date(d.last_handshake).getTime()<180000);indicator.textContent=recent?'Связь с сервером недавно':active.length?'Профиль готов':'Нет активного профиля';indicator.className='pill '+(recent?'vpn-status-fresh':'vpn-status-idle')}
const box=$('#device-list');box.innerHTML=devices.length?devices.map(d=>`<div class="device"><div class="row"><div><h3>${esc(d.name)}</h3><span class="small muted">${esc(d.platform)} · ${day(d.created_at)}<br>${d.last_handshake?'Последняя активность '+day(d.last_handshake):'Нет данных о подключении'}</span></div><span class="pill">${!d.enabled?'Отозван':d.provisioned?'Выдан':'Ожидает'}</span></div><div class="row" style="justify-content:flex-start;margin-top:13px">${d.enabled?`<button class="button ghost compact" data-rename="${d.id}">Переименовать</button><button class="button ghost compact" data-delete="${d.id}">Отозвать</button>`:''}</div></div>`).join(''):'<p class="muted small">Устройства пока не добавлены.</p>';
box.querySelectorAll('[data-rename]').forEach(b=>b.onclick=async()=>{const d=devices.find(x=>x.id===b.dataset.rename),name=prompt('Новое название',d.name);if(!name)return;try{await api('devices/'+d.id,{method:'PATCH',body:JSON.stringify({name})});loadDevices()}catch(e){toast(e.message,true)}});
box.querySelectorAll('[data-delete]').forEach(b=>b.onclick=async()=>{if(!confirm('Отозвать VPN-доступ для этого устройства?'))return;try{await api('devices/'+b.dataset.delete,{method:'DELETE'});toast('Отзыв отправлен');loadDevices();await reload()}catch(e){toast(e.message,true)}});
}catch(e){toast(e.message,true)}}
function b64(buffer){return btoa(String.fromCharCode(...new Uint8Array(buffer)))}
async function wgKeyPair(){
 if(!window.isSecureContext||!crypto.subtle)throw new Error('Требуется HTTPS и современный Telegram WebView');
 try{
 const keys=await crypto.subtle.generateKey({name:'X25519'},true,['deriveBits']);
 const publicKey=b64(await crypto.subtle.exportKey('raw',keys.publicKey));
 const der=new Uint8Array(await crypto.subtle.exportKey('pkcs8',keys.privateKey));
 if(der.length<32)throw new Error('Неверный формат ключа');
 const privateKey=b64(der.slice(-32));
 return {publicKey,privateKey};
 }catch(e){throw new Error('WebView не поддерживает генерацию X25519. Обновите Telegram и ОС. Сервер не генерирует приватные ключи.');}
}
function wireguardBlobDownload(conf,filename){
 const blob=new Blob([conf],{type:'application/octet-stream'});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download=filename;
 document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),120000);
}
async function saveWireguardConf(conf,filename){
 if(typeof File==='undefined'){wireguardBlobDownload(conf,filename);toast('Если загрузка не появилась, используйте «Копировать».',true);return;}
 // Preserve user gesture: launch the native chooser before awaiting other async work.
 const file=new File([conf],filename,{type:'text/plain'});
 if(window.showSaveFilePicker){
   try{const handle=await window.showSaveFilePicker({suggestedName:filename,types:[{description:'WireGuard',accept:{'text/plain':['.conf']}}]});
       const writable=await handle.createWritable();await writable.write(file);await writable.close();
       toast('Файл сохранён на устройство');return;
   }catch(e){if(e.name==='AbortError')return;}
 }
 if(typeof navigator.share==='function'&&(!navigator.canShare||navigator.canShare({files:[file]}))){
   try{await navigator.share({files:[file],title:'WireGuard — Still VPN'});
       toast('Сохраните файл локально через системное меню');return;
   }catch(e){if(e.name==='AbortError')return;}
 }
 wireguardBlobDownload(conf,filename);
 toast('Если файл не появился в загрузках Telegram, нажмите «Копировать» и сохраните .conf локально.',true);
}
async function createDevice(){const btn=$('#create-device');btn.disabled=true;btn.textContent='Создание ключа…';
 try{const name=$('#dev-name').value.trim(),platform=$('#dev-platform').value;if(!name)throw new Error('Введите название устройства');
 const keys=await wgKeyPair();const response=await api('devices',{method:'POST',body:JSON.stringify({name,platform,public_key:keys.publicKey})});
 const conf=`[Interface]\nPrivateKey = ${keys.privateKey}\nAddress = ${response.address}\nDNS = ${response.dns}\nMTU = 1280\n\n[Peer]\nPublicKey = ${response.server_key}\nAllowedIPs = 0.0.0.0/0\nEndpoint = ${response.endpoint}\nPersistentKeepalive = 25\n`;
 currentConfig={name,conf,deviceId:response.id,privateKey:keys.privateKey};
 const root=$('#new-config');root.innerHTML=`<div class="panel"><h2>Конфигурация готова</h2><div class="notice ${response.status==='ready'?'':'error'}">${response.status==='ready'?'VPN-профиль добавлен на сервер.':'Сервер пока не подтвердил создание. Конфигурация сохранится только если вы её скачаете; проверьте статус позже.'}</div><p class="small muted">Ключ создан локально. При нажатии «Получить в Telegram» он однократно передаётся защищённому API и в ваш личный чат; сервер не сохраняет его в базе. При потере конфигурации удалите устройство и создайте новое.</p><div id="qr"></div><div class="code" id="config-text"></div><div class="export-primary"><button id="send-conf-telegram" class="button">✉ Получить .conf в личный чат Telegram</button><p class="export-info">По вашему нажатию ключ отправляется боту по HTTPS, затем приходит личным документом в Telegram. Хранение файла в Telegram зависит от настроек и политики мессенджера.</p><div class="export-actions"><button id="share-conf" class="button secondary compact">Сохранить локально</button><button id="copy-conf" class="button secondary compact">Копировать текст</button></div><button id="download" class="button ghost compact">Обычная загрузка .conf</button></div><p class="export-info">Храните профиль как пароль. Не отправляйте файл посторонним. Для максимальной приватности выбирайте локальное сохранение.</p><p class="small muted" id="install-help"></p></div>`;
 $('#config-text').textContent=conf;
 const tips={android:'Android: установите WireGuard из Google Play или F-Droid, добавьте туннель из файла или QR-кода.',ios:'iPhone/iPad: установите WireGuard из App Store, откройте приложение и выберите «Создать туннель» → из файла или QR-кода.',windows:'Windows: установите официальный WireGuard с wireguard.com/install, затем «Import tunnel(s) from file».',macos:'macOS: установите WireGuard, выберите «Import tunnel(s) from file».',linux:'Linux: установите wireguard-tools, сохраните файл как /etc/wireguard/wg-still.conf (права 600) и запустите sudo wg-quick up wg-still.'};
 $('#install-help').textContent=(tips[platform]||'')+' Для всех платформ: скачайте конфигурацию, импортируйте её и активируйте туннель. Не пересылайте приватный ключ.';
 if(window.QRCode){try{new QRCode($('#qr'),{text:conf,width:205,height:205,correctLevel:QRCode.CorrectLevel.L})}catch{$('#qr').textContent='QR слишком большой. Скачайте файл.'}}else $('#qr').textContent='QR не загрузился. Скачайте файл.';
 const confFilename='still-'+name.replace(/[^a-z0-9-_]/gi,'-')+'.conf';
 $('#send-conf-telegram').onclick=async()=>{const b=$('#send-conf-telegram');if(!confirm('Отправить конфигурацию с приватным ключом в ваш личный Telegram-чат? Сервер не будет хранить ключ, но файл останется в Telegram.'))return;b.disabled=true;b.textContent='Отправляем в чат…';try{await api('devices/'+response.id+'/send-conf',{method:'POST',body:JSON.stringify({private_key:keys.privateKey})});toast('Файл отправлен в личный чат с ботом. Закройте Mini App, чтобы найти его.');b.textContent='✓ Файл отправлен в Telegram'}catch(e){toast(e.message,true);b.disabled=false;b.textContent='✉ Получить .conf в личный чат Telegram'}};
 $('#download').onclick=()=>wireguardBlobDownload(conf,confFilename);
 $('#share-conf').onclick=()=>saveWireguardConf(conf,confFilename);
 $('#copy-conf').onclick=async()=>{try{await navigator.clipboard.writeText(conf);toast('Конфигурация скопирована')}catch{toast('Буфер обмена недоступен',true)}};
 toast('Устройство создано');await loadDevices();await reload();root.scrollIntoView({behavior:'smooth'});
 }catch(e){toast(e.message,true)}finally{btn.disabled=false;btn.textContent='Создать конфигурацию'}}
let selectedTicket=null, ticketListFilter='active';
const priorities={normal:'Обычный',medium:'Средний',critical:'Критический'};
const statusTitles={open:'Ожидает ответа',answered:'Ответ поддержки',closed:'Закрыт'};
const ticketPriority=(p)=>`<span class="ticket-priority"><i class="ticket-dot ${p==='critical'?'critical':p==='medium'?'medium':''}"></i>${esc(priorities[p]||priorities.normal)}</span>`;
const ticketStatus=(s)=>`<span class="ticket-state ${s==='closed'?'closed':s==='answered'?'answered':''}">${esc(statusTitles[s]||s)}</span>`;
function ticketsPage(){main.innerHTML=section('STILL / ЦЕНТР ПОДДЕРЖКИ','Мы на связи.','Заявки и переписка с командой — в одном месте, без сообщений в чате бота.')+
`<div class="ticket-controls"><button class="button" id="ticket-new">Создать обращение</button><button class="button secondary" id="ticket-refresh">Обновить</button></div><div id="tickets-content"><p class="muted small">Загружаем обращения…</p></div><p class="ticket-intro">Ответы сотрудников появятся здесь. Если у вас есть Telegram, уведомление о новом ответе придёт в личный чат. Не отправляйте пароли, VPN-конфигурации и приватные ключи.</p>`;
$('#ticket-new').onclick=showTicketForm;$('#ticket-refresh').onclick=()=>{selectedTicket=null;loadTickets()};
if(selectedTicket)openTicket(selectedTicket);else loadTickets()}
function showTicketForm(){selectedTicket=null;const box=$('#tickets-content');if(!box)return;
box.innerHTML=`<div class="ticket-form"><p class="kicker">НОВОЕ ОБРАЩЕНИЕ</p><h2>Расскажите, что случилось</h2><form id="ticket-create-form"><label for="ticket-title">Тема обращения</label><input id="ticket-title" maxlength="140" minlength="4" required autocomplete="off" placeholder="Например: Не подключается WireGuard"><label for="ticket-body">Описание проблемы</label><textarea id="ticket-body" maxlength="3500" minlength="10" required placeholder="Что произошло, на каком устройстве, что уже пробовали?"></textarea><label>Важность</label><div class="ticket-priority-grid">${['normal','medium','critical'].map((p,i)=>`<label><input type="radio" name="ticket-priority" value="${p}" ${i===0?'checked':''}><span>${ticketPriority(p)}</span></label>`).join('')}</div><p class="small muted">Критический — полная недоступность сервиса; средний — мешает работе; обычный — вопрос или предложение.</p><div class="ticket-controls"><button class="button" type="submit" id="ticket-submit">Отправить обращение</button><button class="button secondary" type="button" id="ticket-cancel">Отмена</button></div></form></div>`;
$('#ticket-cancel').onclick=()=>loadTickets();$('#ticket-create-form').onsubmit=async(e)=>{e.preventDefault();const b=$('#ticket-submit');b.disabled=true;
try{const data={title:$('#ticket-title').value.trim(),description:$('#ticket-body').value.trim(),priority:document.querySelector('input[name="ticket-priority"]:checked').value};const r=await api('tickets',{method:'POST',body:JSON.stringify(data)});toast('Обращение создано');selectedTicket=r.id;await openTicket(r.id)}catch(err){toast(err.message,true)}finally{b.disabled=false}}}
async function loadTickets(){const box=$('#tickets-content');if(!box||page!=='tickets')return;selectedTicket=null;
try{const all=await api('tickets');const filtered=all.filter(t=>ticketListFilter==='all'||(ticketListFilter==='active'?t.status!=='closed':t.status==='closed'));
box.innerHTML=`<div class="ticket-filter">${[['active','Активные'],['closed','Закрытые'],['all','Все']].map(([v,l])=>`<button data-filter="${v}" class="${ticketListFilter===v?'active':''}">${l}</button>`).join('')}</div><div class="ticket-rows">${filtered.length?filtered.map(t=>`<button class="ticket-card" data-ticket="${t.id}"><div class="ticket-topline">${ticketPriority(t.priority)}${ticketStatus(t.status)}</div><div class="ticket-title">${esc(t.title)}</div><div class="ticket-meta">Обращение #${t.id} · Обновлено ${day(t.updated_at||t.created_at)}</div></button>`).join(''):'<div class="ticket-form"><h2>Пока пусто</h2><p class="small muted">Здесь появятся ваши обращения. Создайте первое, если нужна помощь.</p></div>'}</div>`;
box.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{ticketListFilter=b.dataset.filter;loadTickets()});box.querySelectorAll('[data-ticket]').forEach(b=>b.onclick=()=>openTicket(Number(b.dataset.ticket)));
}catch(err){box.innerHTML=`<div class="notice error">${esc(err.message)}</div>`}}
async function openTicket(id){selectedTicket=id;const box=$('#tickets-content');if(!box)return;box.innerHTML='<p class="small muted">Открываем обращение…</p>';
try{const t=await api('tickets/'+id);if(page!=='tickets'||selectedTicket!==id)return;
box.innerHTML=`<button class="button ghost compact" id="ticket-back">← Все обращения</button><div class="ticket-form"><div class="ticket-topline">${ticketPriority(t.priority)}${ticketStatus(t.status)}</div><h2>${esc(t.title)}</h2><p class="small muted">#${t.id} · Создано ${day(t.created_at)}</p></div><div class="ticket-chat">${t.messages.map(m=>`<div class="ticket-bubble ${m.sender==='admin'||m.sender==='staff'?'staff':''}"><div class="byline"><b>${m.sender==='admin'||m.sender==='staff'?'Поддержка Still VPN':'Вы'}</b><span>${day(m.date)}</span></div><p>${esc(m.text)}</p></div>`).join('')}</div>${t.status!=='closed'?`<form id="ticket-reply-form" class="ticket-form"><label for="ticket-reply-text">Дополнить обращение</label><textarea id="ticket-reply-text" maxlength="3500" minlength="2" required placeholder="Напишите ответ…"></textarea><button class="button" id="ticket-send">Отправить сообщение</button></form><button class="button ghost compact" id="ticket-close">Закрыть обращение</button>`:`<div class="ticket-form"><p>Обращение закрыто.</p><button class="button secondary" id="ticket-reopen">Открыть повторно</button></div>`}`;
$('#ticket-back').onclick=()=>loadTickets();if($('#ticket-reply-form'))$('#ticket-reply-form').onsubmit=async ev=>{ev.preventDefault();const b=$('#ticket-send');b.disabled=true;try{await api('tickets/'+id+'/reply',{method:'POST',body:JSON.stringify({text:$('#ticket-reply-text').value.trim()})});toast('Сообщение отправлено');await openTicket(id)}catch(err){toast(err.message,true)}finally{b.disabled=false}};
if($('#ticket-close'))$('#ticket-close').onclick=async()=>{if(!confirm('Закрыть обращение?'))return;try{await api('tickets/'+id+'/close',{method:'POST'});toast('Обращение закрыто');await openTicket(id)}catch(err){toast(err.message,true)}};
if($('#ticket-reopen'))$('#ticket-reopen').onclick=async()=>{try{await api('tickets/'+id+'/reopen',{method:'POST'});toast('Обращение открыто повторно');await openTicket(id)}catch(err){toast(err.message,true)}};
}catch(err){box.innerHTML=`<div class="notice error">${esc(err.message)}</div><button class="button secondary" id="ticket-list-return">Назад</button>`;$('#ticket-list-return').onclick=loadTickets}}
function accountPage(){main.innerHTML=section('Ваш профиль','Приватность прежде всего.','Мы храним только данные, необходимые для подписки и доступа.')+
`<div class="statrow"><span class="muted">Telegram ID</span><b>${me.id}</b></div>
<div class="statrow"><span class="muted">Имя пользователя</span><b>${esc(me.username?'@'+me.username:'—')}</b></div>
<div class="statrow"><span class="muted">Дата регистрации</span><b>${day(me.created_at)}</b></div>
<div class="statrow"><span class="muted">Подписка</span><b>${esc(me.subscription?.name||'Не активна')}</b></div>
<div class="statrow"><span class="muted">Статус аккаунта</span><b>${esc(me.account_status)}</b></div>
<div class="section"><h2>Подарки и промокоды</h2><p class="muted small">Созданные подарки доступны после подтверждённой оплаты. Коды активируются один раз.</p><label>Код подарка / промокод</label><input id="redeem" placeholder="STILL-… или SH-…"><div style="height:12px"></div><button class="button" id="redeem-btn">Активировать код</button><div id="gift-list"></div></div>
${me.admin_role?'<div class="section"><button id="open-admin" class="button secondary">Открыть админ-панель</button></div>':''}<div class="section"><h2>Помощь и документы</h2><p class="muted small">Создайте тикет, укажите тему и важность. История ответов доступна в Mini App.</p><button class="button secondary" id="support-btn">Открыть центр поддержки</button></div>`;
$('#redeem-btn').onclick=async()=>{const code=$('#redeem').value.trim();try{const r=await api('redeem',{method:'POST',body:JSON.stringify({code})});toast(`Активировано: +${r.days} дней`);$('#redeem').value='';await reload();accountPage()}catch(e){toast(e.message,true)}};
$('#support-btn').onclick=()=>nav('tickets');if($('#open-admin'))$('#open-admin').onclick=()=>nav('admin');
loadGifts();}
async function loadGifts(){try{gifts=await api('gifts');if(page!=='account')return;
$('#gift-list').innerHTML=gifts.map(g=>`<div class="panel"><h3>${esc(g.name)}</h3><p class="small muted">Действует до ${day(g.expires_at)} · ${g.used?'Активирован':g.invalid?'Аннулирован':'Ожидает'}</p>${g.code?`<div class="code">${esc(g.code)}</div><button class="button secondary compact" data-code="${esc(g.id)}">Скопировать код</button>`:''}</div>`).join('');
$('#gift-list').querySelectorAll('[data-code]').forEach(b=>b.onclick=async()=>{const g=gifts.find(x=>x.id===b.dataset.code);if(g?.code){await navigator.clipboard.writeText(g.code);toast('Код скопирован')}});
}catch(e){toast(e.message,true)}}
async function reload(){me=await api('me');if(page==='home')render()}
async function boot(){drawTabs();try{[me,plans]=await Promise.all([api('me'),api('plans')]);const query=new URLSearchParams(location.search);const start=query.get('tab')||query.get('tgWebAppStartParam')||tg?.initDataUnsafe?.start_param||'';if(['home','plans','connect','account','tickets'].includes(start)||(start==='admin'&&me.admin_role))page=start;drawTabs();render()}catch(e){main.innerHTML=`<div class="notice error">${esc(e.message)}</div><button id="retry" class="button secondary">Повторить</button>`;$('#retry').onclick=boot}}
// Only users with an authenticated admin role see this entrance. Every request
// is also authorized by role on the FastAPI side; UI checks are cosmetic.
let adminSection='overview', adminSelectedUser=null, adminSelectedTicket=null, adminPlanEdit=null;
const adminSections=[['overview','Сводка','access'],['users','Пользователи','users'],
 ['plans','Тарифы','plans'],['promos','Промокоды','plans'],['servers','Серверы','servers'],['payments','Платежи','finance'],
 ['support','Поддержка','support'],['settings','Настройки','settings'],
 ['staff','Роли','staff'],['audit','Журнал','audit']];
const adminPerms={owner:['access','stats','users','plans','servers','finance','support','settings','staff','audit'],
 administrator:['access','stats','users','plans','servers','finance','support','settings','audit'],
 support:['access','users','support'],finance:['access','stats','finance'],viewer:['access','stats']};
function acan(perm){return (adminPerms[me?.admin_role]||[]).includes(perm)}
function stateTag(s,ok){return `<span class="admin-status ${ok?'ok':''}">${esc(s)}</span>`}
function adminReason(){const r=prompt('Причина изменения (не менее 5 символов, для журнала действий):');if(!r)return null;if(r.trim().length<5){toast('Причина должна содержать минимум 5 символов',true);return null}return r.trim()}
function adminPage(){if(!me?.admin_role){nav('account');return}
 const available=adminSections.filter(x=>acan(x[2]));if(!available.some(x=>x[0]===adminSection))adminSection=available[0][0];
 main.innerHTML=`<div class="admin-head"><div><p class="kicker">Управление Still VPN</p><h1>Админ-панель</h1><p class="small muted">Роль: ${esc(me.admin_role)} · данные из системы</p></div><button id="admin-refresh" class="button secondary compact">Обновить</button></div>`+
 `<div class="admin-nav">${available.map(x=>`<button type="button" class="${x[0]===adminSection?'active':''}" data-admin-tab="${x[0]}">${x[1]}</button>`).join('')}</div><div id="admin-content" aria-live="polite"></div>`;
 document.querySelectorAll('[data-admin-tab]').forEach(b=>b.onclick=()=>{adminSection=b.dataset.adminTab;adminSelectedUser=null;adminSelectedTicket=null;adminPlanEdit=null;adminPage()});
 $('#admin-refresh').onclick=()=>adminLoad();adminLoad();}
async function adminLoad(){const box=$('#admin-content');if(!box)return;box.innerHTML='<p class="admin-empty">Загрузка данных…</p>';
 try{if(adminSection==='overview')await adminOverview(box);
 else if(adminSection==='users')await adminUsers(box);
 else if(adminSection==='plans')await adminPlans(box);
 else if(adminSection==='promos')await adminPromos(box);
 else if(adminSection==='servers')await adminServers(box);
 else if(adminSection==='payments')await adminPayments(box);
 else if(adminSection==='support')await adminTickets(box);
 else if(adminSection==='settings')await adminSettings(box);
 else if(adminSection==='staff')await adminStaff(box);
 else if(adminSection==='audit')await adminAudit(box);
 }catch(e){if($('#admin-content')===box)box.innerHTML=`<div class="notice error">${esc(e.message)}</div><button id="admin-again" class="button secondary">Повторить</button>`,$('#admin-again').onclick=adminLoad}}
function adminList(items,fn){return items.length?`<div class="admin-table">${items.map(fn).join('')}</div>`:'<p class="admin-empty">Пока нет записей.</p>'}
function mval(label,n){return `<div class="admin-metric"><span class="small muted">${label}</span><strong>${esc(n??0)}</strong></div>`}
async function adminOverview(box){const d=await api('admin/summary');const x=d.stats||{}, f=d.finance||{};
 let html='';if(d.stats)html+=`<div class="admin-metrics">${mval('Пользователи',x.users)}${mval('Новые за сутки',x.new_users)}${mval('Активные подписки',x.subscriptions)}${mval('Пробные периоды',x.trials)}${mval('Устройства',x.devices)}${mval('Серверы онлайн',`${x.healthy_servers}/${x.servers}`)}${mval('Истёкшие подписки',x.expired_subs)}${mval('Открытые обращения',x.tickets)}</div>`;
 if(d.finance)html+=`<div class="section"><h2>Платежи</h2><div class="statrow"><span class="muted">Подтверждено</span><b>${f.payments}</b></div><div class="statrow"><span class="muted">Получено Stars (без возвратов)</span><b>${f.stars} ⭐</b></div><div class="statrow"><span class="muted">Возвраты</span><b>${f.refunds}</b></div></div>`;
 if(d.support)html+=`<h2>Обращения</h2>${mval('Открыто',d.support.open_tickets)}`;
 if(d.events?.length)html+=`<div class="section"><h2>Последние действия</h2>${adminList(d.events,x=>`<div class="admin-item"><div><b>${esc(x.action)}</b><div class="small muted">${esc(x.target)} · ${esc(x.admin_id)}</div></div><span class="small muted">${day(x.date)}</span></div>`)}</div>`;
 box.innerHTML=html||'<p class="admin-empty">Нет доступных показателей для вашей роли.</p>';}
async function adminUsers(box, query=''){if(adminSelectedUser){await adminUserDetail(box,adminSelectedUser);return}
 const data=await api('admin/users?q='+encodeURIComponent(query));box.innerHTML=`<h2>Пользователи</h2><p class="small muted">Поиск по Telegram ID или @username.</p><div class="admin-filter"><input id="admin-search" placeholder="ID или username" maxlength="80" value="${esc(query)}"><button id="admin-search-btn" class="button compact">Найти</button></div>`+
 adminList(data,u=>`<div class="admin-item"><div><b>${esc(u.first_name||u.username||u.id)}</b><div class="small muted">${esc(u.username?'@'+u.username:'Без username')} · ID ${u.id}<br>Регистрация ${day(u.created_at)}</div></div><button class="button secondary compact" data-user="${u.id}">Открыть</button></div>`);
 $('#admin-search-btn').onclick=()=>adminUsers(box,$('#admin-search').value);$('#admin-search').onkeydown=e=>{if(e.key==='Enter')adminUsers(box,e.target.value)};
 box.querySelectorAll('[data-user]').forEach(b=>b.onclick=()=>{adminSelectedUser=Number(b.dataset.user);adminLoad()});}
async function adminUserDetail(box,uid){const u=await api('admin/users/'+uid);box.innerHTML=`<button id="admin-back" class="admin-breadcrumb">← К пользователям</button><h2>${esc(u.first_name||u.username||u.id)}</h2>
 <div class="statrow"><span class="muted">Telegram ID</span><b>${u.id}</b></div><div class="statrow"><span class="muted">Username</span><b>${esc(u.username?'@'+u.username:'—')}</b></div><div class="statrow"><span class="muted">Статус</span>${stateTag(u.blocked?'Заблокирован':'Активен',!u.blocked)}</div><div class="statrow"><span class="muted">Пробный доступ</span><b>${u.trial?day(u.trial.ends_at)+' · '+new Date(u.trial.ends_at).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'}):'Не использован'}</b></div>`+
 (['owner','administrator'].includes(me.admin_role)?`<div class="admin-actions"><button class="button secondary compact" id="admin-block">${u.blocked?'Разблокировать':'Заблокировать'}</button><button class="button secondary compact" id="admin-grant">Выдать подписку</button><button class="button ghost compact" id="admin-revoke-all">Отозвать все устройства</button></div>`:'')+
 (me.admin_role==='owner'&&u.trial&&new Date(u.trial.ends_at)>new Date()?`<section class="admin-trial-test"><span class="kicker">ТЕСТ ДОСТУПА</span><h3>Сократить пробный период</h3><p class="small muted">Только для выбранного пользователя. Записывается в Audit Log. Это не отменяет платную подписку.</p><div class="admin-actions"><button class="button secondary compact" id="admin-trial-five">До 5 минут</button><button class="button ghost compact" id="admin-trial-end">Завершить сейчас</button></div></section>`:'')+
 `<div class="section"><h2>Подписки</h2>${adminList(u.subscriptions,s=>`<div class="admin-item"><div><b>${esc(s.name)}</b><div class="small muted">${day(s.starts_at)} — ${day(s.ends_at)} · ${esc(s.source)}</div></div>${stateTag(s.revoked?'Отозвана':'Выдана',!s.revoked)}</div>`)}</div>`+
 `<div class="section"><h2>Устройства</h2>${adminList(u.devices,d=>`<div class="admin-item"><div><b>${esc(d.name)}</b><div class="small muted">${esc(d.ip)} · ${d.last_handshake?day(d.last_handshake):'Нет handshake'}</div></div>${['owner','administrator'].includes(me.admin_role)&&d.enabled?`<button class="button ghost compact" data-revoke="${esc(d.id)}">Отозвать</button>`:stateTag(d.enabled?'Активно':'Отозвано',d.enabled)}</div>`)}</div>`;
 $('#admin-back').onclick=()=>{adminSelectedUser=null;adminLoad()};
 if($('#admin-block'))$('#admin-block').onclick=async()=>{const r=adminReason();if(!r)return;try{await api('admin/users/'+uid+'/block',{method:'POST',body:JSON.stringify({reason:r,blocked:!u.blocked})});toast('Статус изменён');adminLoad()}catch(e){toast(e.message,true)}};
 for(const [id,minutes] of [['admin-trial-five',5],['admin-trial-end',0]]){
  const b=$('#'+id);if(!b)continue;
  b.onclick=async()=>{
    const question=minutes===0?'Завершить пробный период пользователя прямо сейчас?':'Сократить пробный период пользователя до 5 минут?';
    if(!confirm(question))return;
    const reason=adminReason();if(!reason)return;
    try{const out=await api('admin/users/'+uid+'/trial/shorten',{method:'POST',body:JSON.stringify({remaining_minutes:minutes,reason})});
        toast(minutes===0?'Пробный период завершён, отзыв Peer запрошен':'Пробный период сокращён до 5 минут');
        adminLoad();
    }catch(e){toast(e.message,true)}
  };
 }
 if($('#admin-grant'))$('#admin-grant').onclick=async()=>{const days=Number(prompt('На сколько дней?','30'));if(!Number.isInteger(days)||days<1||days>365)return;const devices=Number(prompt('Количество устройств (1–20)','2'));if(!Number.isInteger(devices)||devices<1||devices>20)return;const traffic_gb=Number(prompt('Лимит в ГБ (0 = безлимит)','0'));if(!Number.isInteger(traffic_gb)||traffic_gb<0||traffic_gb>10000)return;const reason=adminReason();if(!reason)return;try{await api('admin/users/'+uid+'/grant',{method:'POST',body:JSON.stringify({days,devices,traffic_gb,reason})});toast('Подписка выдана');adminLoad()}catch(e){toast(e.message,true)}};
 if($('#admin-revoke-all'))$('#admin-revoke-all').onclick=async()=>{if(!confirm('Отозвать VPN-доступ всех устройств пользователя?'))return;const reason=adminReason();if(!reason)return;try{await api('admin/users/'+uid+'/revoke',{method:'POST',body:JSON.stringify({reason})});toast('Отзыв отправлен');adminLoad()}catch(e){toast(e.message,true)}};
 box.querySelectorAll('[data-revoke]').forEach(b=>b.onclick=async()=>{const reason=adminReason();if(!reason)return;try{await api('admin/devices/'+b.dataset.revoke+'/revoke',{method:'POST',body:JSON.stringify({reason})});toast('Peer отозван');adminLoad()}catch(e){toast(e.message,true)}});}
async function adminPlans(box){const data=await api('admin/plans');box.innerHTML=`<h2>Тарифы</h2><p class="small muted">Изменения влияют только на будущие покупки. Уже выданные подписки сохраняют свои условия.</p>`+
 adminList(data,p=>`<div class="admin-item"><div><b>${esc(p.title)}</b><div class="small muted">${p.days} дн. · ${p.stars} ⭐ · ${p.devices} устр. · ${p.traffic_gb||'∞'} ГБ</div></div><div>${stateTag(p.enabled?'Включён':'Скрыт',p.enabled)}${['owner','administrator'].includes(me.admin_role)?`<button class="button secondary compact" data-plan="${p.id}" style="margin-top:7px">Изменить</button>`:''}</div></div>`)+
 (['owner','administrator'].includes(me.admin_role)?`<div class="admin-form"><h3 id="admin-plan-form-title">Новый тариф</h3><label>Название</label><input id="ap-title" maxlength="120" placeholder="Например, 30 дней"><div class="row"><div><label>Дни</label><input type="number" id="ap-days" min="1" max="3650" value="30"></div><div><label>Stars</label><input type="number" id="ap-stars" min="1" value="100"></div></div><div class="row"><div><label>Устройства</label><input type="number" id="ap-devices" min="1" max="20" value="2"></div><div><label>Трафик, ГБ (0 = ∞)</label><input type="number" id="ap-gb" min="0" value="0"></div></div><label><input type="checkbox" id="ap-enabled" checked style="width:auto;min-height:0"> Показывать в Mini App</label><button id="admin-plan-save" class="button">Сохранить тариф</button></div>`:'');
 box.querySelectorAll('[data-plan]').forEach(b=>b.onclick=()=>{const p=data.find(x=>x.id===Number(b.dataset.plan));adminPlanEdit=p.id;$('#admin-plan-form-title').textContent='Редактировать тариф #'+p.id;$('#ap-title').value=p.title;$('#ap-days').value=p.days;$('#ap-stars').value=p.stars;$('#ap-devices').value=p.devices;$('#ap-gb').value=p.traffic_gb;$('#ap-enabled').checked=p.enabled;$('#ap-title').scrollIntoView({behavior:'smooth'})});
 if($('#admin-plan-save'))$('#admin-plan-save').onclick=async()=>{const p={title:$('#ap-title').value.trim(),days:Number($('#ap-days').value),stars:Number($('#ap-stars').value),devices:Number($('#ap-devices').value),traffic_gb:Number($('#ap-gb').value),enabled:$('#ap-enabled').checked};try{await api('admin/plans'+(adminPlanEdit?'/'+adminPlanEdit:''),{method:adminPlanEdit?'PUT':'POST',body:JSON.stringify(p)});toast('Тариф сохранён');adminPlanEdit=null;plans=await api('plans');adminLoad()}catch(e){toast(e.message,true)}};}
async function adminPromos(box){const rows=await api('admin/promos');box.innerHTML=`<h2>Промокоды</h2><p class="small muted">Коды не сохраняются в открытом виде. Новый код будет показан один раз, затем его можно передать пользователю.</p>`+
 adminList(rows,p=>`<div class="admin-item"><div><b>#${p.id} · ${p.type==='discount'?'-'+p.value+'%':'+'+p.value+' дней'}</b><div class="small muted">Использовано ${p.uses}/${p.max_uses} · до ${day(p.expires_at)}</div></div><div>${stateTag(p.enabled?'Активен':'Выключен',p.enabled)}${['owner','administrator'].includes(me.admin_role)&&p.enabled?`<button class="button ghost compact" data-promo-off="${p.id}" style="margin-top:7px">Отключить</button>`:''}</div></div>`)+
 (['owner','administrator'].includes(me.admin_role)?`<div class="admin-form"><h3>Новый промокод</h3><label>Тип</label><select id="pr-kind"><option value="days">Бесплатные дни</option><option value="discount">Скидка на Stars</option></select><label>Количество дней или процентов</label><input id="pr-value" type="number" min="1" max="365" value="7"><div class="row"><div><label>Максимум активаций</label><input id="pr-uses" type="number" min="1" value="10"></div><div><label>Действует, часов</label><input id="pr-hours" type="number" min="1" value="168"></div></div><div style="height:15px"></div><button id="pr-create" class="button">Создать код</button><div id="pr-created"></div></div>`:'');
 box.querySelectorAll('[data-promo-off]').forEach(b=>b.onclick=async()=>{const reason=adminReason();if(!reason)return;try{await api('admin/promos/'+b.dataset.promoOff+'/disable',{method:'POST',body:JSON.stringify({reason})});toast('Промокод отключён');adminLoad()}catch(e){toast(e.message,true)}});
 if($('#pr-create'))$('#pr-create').onclick=async()=>{const d={kind:$('#pr-kind').value,days_or_percent:Number($('#pr-value').value),max_uses:Number($('#pr-uses').value),hours:Number($('#pr-hours').value)};try{const out=await api('admin/promos',{method:'POST',body:JSON.stringify(d)});$('#pr-created').innerHTML=`<div class="notice">Код создан. Сохраните сейчас — повторно получить его невозможно.</div><div class="code" id="pr-code"></div><button id="pr-copy" class="button secondary compact">Копировать</button>`;$('#pr-code').textContent=out.code;$('#pr-copy').onclick=()=>navigator.clipboard.writeText(out.code).then(()=>toast('Скопировано'),()=>toast('Нет доступа к буферу',true));}catch(e){toast(e.message,true)}};
}
async function adminServers(box){const rows=await api('admin/servers');box.innerHTML=`<h2>VPN-серверы</h2><p class="small muted">Состояние из последней реальной проверки агента. Выключение запрещает новые подключения, но не удаляет действующие.</p>`+
 adminList(rows,n=>`<div class="admin-item"><div><b>#${n.id} · ${esc(n.location)}</b><div class="small muted">${esc(n.endpoint)}<br>Peer: ${n.peer_count??'—'} · CPU: ${n.cpu===null?'—':n.cpu+'%'}<br>RAM: ${n.ram_used===null?'—':(n.ram_used/1048576).toFixed(0)+' MiB'} · Диск: ${n.disk_free===null?'—':(n.disk_free/1073741824).toFixed(1)+' GiB'}<br>${n.error?'Ошибка: '+esc(n.error):'Обновлено: '+(n.last_seen?day(n.last_seen):'нет данных')}</div></div><div>${stateTag(n.online?'Онлайн':'Нет связи',n.online)}${stateTag(n.enabled?'Для новых: да':'Для новых: нет',n.enabled)}${['owner','administrator'].includes(me.admin_role)?`<button class="button secondary compact" data-server="${n.id}" style="margin-top:8px">${n.enabled?'Выключить':'Включить'}</button>`:''}</div></div>`);
 box.querySelectorAll('[data-server]').forEach(b=>b.onclick=async()=>{const n=rows.find(x=>x.id===Number(b.dataset.server));const reason=adminReason();if(!reason)return;try{await api('admin/servers/'+n.id+'/state',{method:'POST',body:JSON.stringify({enabled:!n.enabled,reason})});toast('Состояние обновлено');adminLoad()}catch(e){toast(e.message,true)}});}
async function adminPayments(box){const rows=await api('admin/payments');box.innerHTML=`<h2>Платежи</h2><p class="small muted">Показаны реальные транзакции Telegram Stars. Возврат выполняется владельцем через команду /adm_refund в боте с обязательной причиной и проверкой Telegram.</p>`+
 adminList(rows,p=>`<div class="admin-item"><div><b>${esc(p.plan)}</b><div class="small muted">Telegram ${p.user_id} · ${day(p.date)}<br>ID: ${esc(p.id)}<br>Charge: ${esc(p.charge_id||'—')}</div></div><div style="text-align:right"><b>${p.amount} ⭐</b><div>${stateTag(p.status,p.status==='paid')}</div></div></div>`);}
let adminTicketFilter='active',adminTicketPriority='all',adminTicketSearch='';
async function adminTickets(box){if(adminSelectedTicket){await adminTicketDetail(box,adminSelectedTicket);return}
const rows=await api('admin/tickets');const priorityOrder={critical:0,medium:1,normal:2};
const filtered=rows.filter(t=>{
 const statusOk=adminTicketFilter==='all'||(adminTicketFilter==='active'?t.status!=='closed':t.status==='closed');
 const priorityOk=adminTicketPriority==='all'||t.priority===adminTicketPriority;
 const searchOk=!adminTicketSearch||`${t.id} ${t.user_name} ${t.username} ${t.title}`.toLowerCase().includes(adminTicketSearch.toLowerCase());
 return statusOk&&priorityOk&&searchOk;
}).sort((a,b)=>(a.status==='closed')-(b.status==='closed')||(priorityOrder[a.priority]??2)-(priorityOrder[b.priority]??2)||new Date(b.updated_at)-new Date(a.updated_at));
box.innerHTML=`<h2>Центр поддержки</h2><p class="small muted">Все обращения управляются здесь. Ответ может отправить любой администратор. События отмечаются в служебной группе.</p><div class="ticket-admin-filter"><select id="admin-ticket-status"><option value="active">Активные</option><option value="closed">Закрытые</option><option value="all">Все</option></select><select id="admin-ticket-priority"><option value="all">Любая важность</option><option value="critical">🔴 Критические</option><option value="medium">🟡 Средние</option><option value="normal">🟢 Обычные</option></select><input id="admin-ticket-search" placeholder="Тема, ID, пользователь" value="${esc(adminTicketSearch)}"></div><p class="small muted">Найдено: ${filtered.length}</p>`+
adminList(filtered,t=>`<div class="admin-item"><div style="min-width:0;flex:1"><div class="ticket-topline">${ticketPriority(t.priority)}${ticketStatus(t.status)}</div><b style="overflow-wrap:anywhere">#${t.id} · ${esc(t.title)}</b><div class="small muted">${esc(t.user_name)} ${t.username?'· @'+esc(t.username):''} · ID ${t.user_id}<br>Обновлён ${day(t.updated_at||t.created_at)}</div></div><button class="button secondary compact" data-ticket="${t.id}">Открыть</button></div>`);
$('#admin-ticket-status').value=adminTicketFilter;$('#admin-ticket-priority').value=adminTicketPriority;
$('#admin-ticket-status').onchange=e=>{adminTicketFilter=e.target.value;adminTickets(box)};
$('#admin-ticket-priority').onchange=e=>{adminTicketPriority=e.target.value;adminTickets(box)};
$('#admin-ticket-search').oninput=e=>{adminTicketSearch=e.target.value};$('#admin-ticket-search').onkeydown=e=>{if(e.key==='Enter')adminTickets(box)};
box.querySelectorAll('[data-ticket]').forEach(b=>b.onclick=()=>{adminSelectedTicket=Number(b.dataset.ticket);adminLoad()});}
async function adminTicketDetail(box,id){const t=await api('admin/tickets/'+id);box.innerHTML=`<button id="admin-ticket-back" class="admin-breadcrumb">← К обращениям</button><h2>${esc(t.title)}</h2><div class="ticket-topline">${ticketPriority(t.priority)}${ticketStatus(t.status)}</div><p class="small muted">Обращение #${t.id} · ${esc(t.user_name)} ${t.username?'· @'+esc(t.username):''} · ID ${t.user_id} · ${day(t.created_at)}</p><div class="ticket-admin-filter"><label class="small muted" for="admin-ticket-change-priority">Изменить важность</label><select id="admin-ticket-change-priority"><option value="normal">🟢 Обычный</option><option value="medium">🟡 Средний</option><option value="critical">🔴 Критический</option></select></div><div class="ticket-admin-note">Ответы сохраняются в Mini App. Пользователю придёт уведомление в личный чат, но переписка не отправляется в служебную группу.</div><div class="ticket-chat">${t.messages.map(m=>`<div class="ticket-bubble ${m.sender==='admin'||m.sender==='staff'?'staff':''}"><div class="byline"><b>${m.sender==='admin'||m.sender==='staff'?'Сотрудник'+(m.staff_id?' #'+m.staff_id:''):'Пользователь'}</b><span>${day(m.date)}</span></div><p>${esc(m.text)}</p></div>`).join('')}</div>`+
(t.status!=='closed'?`<form id="admin-ticket-reply" class="ticket-form"><label for="admin-ticket-text">Ваш ответ</label><textarea id="admin-ticket-text" minlength="2" maxlength="3500" required placeholder="Объясните решение или задайте уточняющий вопрос…"></textarea><button class="button" type="submit" id="admin-ticket-send">Отправить ответ</button></form><button class="button ghost compact" id="admin-ticket-close">Закрыть обращение</button>`:`<div class="ticket-form"><p>Тикет закрыт.</p><button class="button secondary" id="admin-ticket-reopen">Открыть повторно</button></div>`);
$('#admin-ticket-back').onclick=()=>{adminSelectedTicket=null;adminLoad()};$('#admin-ticket-change-priority').value=t.priority;
$('#admin-ticket-change-priority').onchange=async e=>{try{await api('admin/tickets/'+id+'/priority',{method:'POST',body:JSON.stringify({priority:e.target.value})});toast('Важность обновлена');await adminLoad()}catch(err){toast(err.message,true)}};
if($('#admin-ticket-reply'))$('#admin-ticket-reply').onsubmit=async e=>{e.preventDefault();const text=$('#admin-ticket-text').value.trim();if(text.length<2)return;const b=$('#admin-ticket-send');b.disabled=true;try{await api('admin/tickets/'+id+'/reply',{method:'POST',body:JSON.stringify({text})});toast('Ответ сохранён. Пользователь получит уведомление.');await adminLoad()}catch(err){toast(err.message,true);b.disabled=false}};
if($('#admin-ticket-close'))$('#admin-ticket-close').onclick=async()=>{const reason=adminReason();if(!reason)return;try{await api('admin/tickets/'+id+'/close',{method:'POST',body:JSON.stringify({reason})});toast('Обращение закрыто');await adminLoad()}catch(err){toast(err.message,true)}};
if($('#admin-ticket-reopen'))$('#admin-ticket-reopen').onclick=async()=>{try{await api('admin/tickets/'+id+'/reopen',{method:'POST'});toast('Обращение открыто');await adminLoad()}catch(err){toast(err.message,true)}};}
async function adminSettings(box){const d=await api('admin/trial-settings');box.innerHTML=`<h2>Пробный доступ</h2><p class="small muted">Настройки применяются только к новым активациям. Ранее выданный доступ не изменяется.</p><div class="admin-form"><label><input id="at-enabled" type="checkbox" ${d.enabled?'checked':''} style="width:auto;min-height:0"> Доступен новым пользователям</label><div class="row"><div><label>Часов</label><input type="number" id="at-hours" min="1" max="720" value="${d.hours}"></div><div><label>Устройства</label><input type="number" id="at-devices" min="1" max="20" value="${d.devices}"></div></div><label>Трафик, ГБ (0 = без лимита)</label><input type="number" id="at-gb" min="0" max="10000" value="${d.traffic_gb}"><div style="height:15px"></div><button id="at-save" class="button">Сохранить настройки</button></div>`;
 $('#at-save').onclick=async()=>{const d={enabled:$('#at-enabled').checked,hours:Number($('#at-hours').value),devices:Number($('#at-devices').value),traffic_gb:Number($('#at-gb').value)};try{await api('admin/trial-settings',{method:'PUT',body:JSON.stringify(d)});toast('Настройки сохранены');adminLoad()}catch(e){toast(e.message,true)}};}
async function adminStaff(box){const d=await api('admin/staff');box.innerHTML=`<h2>Доступ сотрудников</h2><p class="small muted">Owner назначается через OWNER_IDS на BotHost. Остальные роли имеют отдельные API-права.</p>`+
 adminList([...d.owners.map(id=>({id,role:'owner'})),...d.members],x=>`<div class="admin-item"><div><b>${x.id}</b><div class="small muted">${esc(x.role)}</div></div>${x.role!=='owner'?`<button class="button ghost compact" data-staff-remove="${x.id}">Снять роль</button>`:''}</div>`)+
 `<div class="admin-form"><h3>Назначить роль</h3><label>Telegram ID</label><input id="staff-id" inputmode="numeric" placeholder="123456789"><label>Роль</label><select id="staff-role"><option value="administrator">Administrator</option><option value="support">Support</option><option value="finance">Finance</option><option value="viewer">Viewer</option></select><div style="height:15px"></div><button id="staff-save" class="button">Назначить</button></div>`;
 $('#staff-save').onclick=async()=>{const id=$('#staff-id').value.trim();const reason=adminReason();if(!id||!reason)return;try{await api('admin/staff/'+encodeURIComponent(id),{method:'PUT',body:JSON.stringify({role:$('#staff-role').value,reason})});toast('Роль изменена');adminLoad()}catch(e){toast(e.message,true)}};
 box.querySelectorAll('[data-staff-remove]').forEach(b=>b.onclick=async()=>{const reason=adminReason();if(!reason)return;try{await api('admin/staff/'+b.dataset.staffRemove,{method:'DELETE',body:JSON.stringify({reason})});toast('Доступ отозван');adminLoad()}catch(e){toast(e.message,true)}});}
async function adminAudit(box){const rows=await api('admin/audit');box.innerHTML='<h2>Журнал действий</h2><p class="small muted">Дата, сотрудник, действие и результат. Записи формируются сервером.</p>'+
 adminList(rows,a=>`<div class="admin-item"><div><b>${esc(a.action)}</b><div class="small muted">${esc(a.details||'—')}<br>Цель: ${esc(a.target)} · Админ: ${a.admin}</div></div><div style="text-align:right">${stateTag(a.result,a.result==='ok')}<div class="small muted">${day(a.date)}</div></div></div>`);}

boot();
})();
</script></body></html>"""

if __name__ == "__main__":
    if sys.argv[1:2] == ["dbtest"]:
        if MODE != "app":
            raise SystemExit("dbtest доступен только в SHADE_MODE=app")
        raise SystemExit(0 if asyncio.run(database_selftest()) else 1)
    if sys.argv[1:2] == ["verify"]:
        if MODE != "app":
            raise SystemExit("verify доступен только в SHADE_MODE=app")
        raise SystemExit(0 if asyncio.run(verify_services()) else 1)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0" if MODE == "app" else os.getenv("AGENT_BIND", "127.0.0.1"),
                port=int(os.getenv("PORT", "8000" if MODE == "app" else "8080")),
                proxy_headers=False, workers=1)
