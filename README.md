# 💘 Chirikat' Bot — Telegram бот для знакомств

## [![Start Bot](https://img.shields.io/badge/Telegram-Запустить%20бота-green?logo=telegram)](https://t.me/ChirikatBot)

---

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue?logo=docker)

---
## 📌 О проекте

**Chirikat Bot** — это Telegram-бот для знакомств, который позволяет пользователям:

- 📄 Создавать анкеты (имя, возраст, город, описание)
- 🖼 Добавлять фотографии
- ❤️ Лайкать других пользователей
- 💬 Получать взаимные совпадения (matches)

Бот построен на асинхронной архитектуре и легко масштабируется.

---

## ⚙️ Стек технологий

- **Python 3.11**
- **Aiogram 3** — Telegram Bot API
- **SQLAlchemy 2 (async)** — ORM
- **PostgreSQL** — база данных
- **Alembic** — миграции
- **Docker** — контейнеризация

---

## 🚀 Быстрый старт

### 1. Клонировать проект

```bash
git clone https://github.com/your-username/chirikat-bot.git
cd chirikat-bot
```
---

### 2. Создать .env
```.env
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=
BOT_TOKEN=
DB_CONTANER_NAME=
DB_RESTART_POLICY=
DB_PORT_INTERNAL=
DB_PORT_EXTERNAL=
```


### 3. Запуск через Docker
```bash
docker-compose up -d
```
---

### 4. Применить миграции
```bash
alembic upgrade head
```
---

### 5. Запустить бота
```bash
python main.py
```

---

## 👤 Авторы

- KarpX – разработчик: [![Telegram](https://img.shields.io/badge/Contact-KarpX-blue?logo=telegram)](https://t.me/KarpXer)

- vladusecho – создатель идеи: [![Telegram](https://img.shields.io/badge/Contact-vladusecho-blue?logo=telegram)](https://t.me/cklsyawxgi)

---

## ⭐️ Поддержка

Если проект оказался интересным — поставь ⭐️ на GitHub!


