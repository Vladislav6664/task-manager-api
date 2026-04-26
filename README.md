# Task Manager

Проект на Python, разделенный на отдельные приложения:

- `apps/backend`:
  API, база данных, модели, бизнес-логика
- `apps/telegram_bot`:
  Telegram-клиент, который работает через backend API
- `apps/vk_client`:
  отдельный Python-клиент для сценария привязки и работы с задачами VK
- `apps/shared`:
  общий HTTP-клиент для Telegram и VK

Такое разделение нужно, чтобы не смешивать ответственность:

- backend хранит и проверяет данные;
- Telegram и VK только общаются с пользователем;
- оба клиента используют один и тот же API.

## Стек

- Python
- FastAPI
- SQLAlchemy
- SQLite
- pytest
- aiogram
- httpx

## Структура проекта

```text
task_manager/
|-- apps/
|   |-- backend/
|   |   |-- app/
|   |   |   |-- config.py
|   |   |   |-- crud.py
|   |   |   |-- database.py
|   |   |   |-- dependencies.py
|   |   |   |-- main.py
|   |   |   |-- models.py
|   |   |   |-- schemas.py
|   |   |   |-- __init__.py
|   |   |   `-- services/
|   |   |       |-- tasks.py
|   |   |       |-- users.py
|   |   |       `-- __init__.py
|   |   |-- tests/
|   |   `-- __init__.py
|   |-- shared/
|   |   |-- task_manager_client.py
|   |   `-- __init__.py
|   |-- telegram_bot/
|   |   |-- app/
|   |   |   |-- bot_utils.py
|   |   |   |-- config.py
|   |   |   |-- main.py
|   |   |   `-- __init__.py
|   |   `-- tests/
|   `-- vk_client/
|       |-- app/
|       |   |-- config.py
|       |   |-- main.py
|       |   `-- __init__.py
|       `-- __init__.py
|-- .env.example
|-- pyproject.toml
|-- pytest.ini
|-- README.md
|-- requirements.txt
`-- uv.lock
```

## Что хранит backend

В backend три основные сущности:

- `users`:
  внутренний пользователь системы
- `user_identities`:
  привязка пользователя к внешней платформе (`telegram`, `vk`, `web`)
- `tasks`:
  задача, принадлежащая конкретному пользователю и имеющая `source`

Это дает такую модель:

- один человек может иметь один общий аккаунт в системе;
- Telegram и VK могут быть привязаны к этому аккаунту;
- задачи можно разделять по `source`, чтобы Telegram-задачи и VK-задачи не смешивались по умолчанию.

## Как работает привязка Telegram и VK

### Шаг 1. Пользователь приходит в Telegram

Telegram-бот вызывает backend:

```http
POST /users/identify
```

с параметрами:

```json
{
  "provider": "telegram",
  "external_id": "telegram_user_id",
  "name": "Имя пользователя"
}
```

Backend:

- находит существующего пользователя, если он уже есть;
- или создает нового;
- возвращает `user_key`.

### Шаг 2. Пользователь получает свой `user_key`

В Telegram это можно посмотреть командой:

```text
/key
```

Пример:

```text
TM-AB12CD34
```

### Шаг 3. Пользователь приходит в VK

VK-клиент вызывает backend:

```http
POST /users/link
```

с параметрами:

```json
{
  "provider": "vk",
  "external_id": "vk_user_id",
  "user_key": "TM-AB12CD34"
}
```

После этого Telegram и VK будут связаны с одним внутренним пользователем.

## Запуск backend

Backend теперь запускается как отдельное приложение:

```powershell
uvicorn apps.backend.app.main:app --reload
```

Документация:

```text
http://127.0.0.1:8000/docs
```

## Переменные окружения

- `BACKEND_API_URL`, по умолчанию: `http://127.0.0.1:8000`
- `TASK_MANAGER_DATABASE_URL`, по умолчанию: `sqlite:///./tasks.db`
- `TASK_MANAGER_CORS_ORIGINS`, по умолчанию: `*`
- `TELEGRAM_BOT_TOKEN`
- `VK_EXTERNAL_ID`

## Запуск Telegram-бота

Бот больше не работает напрямую с базой.
Теперь он является отдельным клиентом и ходит в backend через HTTP.

Запуск:

```powershell
python -m apps.telegram_bot.app.main
```

Команды:

- `/start`
- `/help`
- `/tasks`
- `/tasks_all`
- `/task <id>`
- `/add <title> | <description> | <priority>`
- `/done <id>`
- `/delete <id>`
- `/key`

## Запуск VK Python client

Это пока не VK Mini App, а учебный и технический Python-клиент.
Он нужен, чтобы уже сейчас проверить сценарий привязки и работу VK-задач через backend.

### Найти или создать VK-пользователя

```powershell
python -m apps.vk_client.app.main identify --vk-id 10001 --name "Vlad"
```

### Привязать VK к существующему аккаунту из Telegram

```powershell
python -m apps.vk_client.app.main link --vk-id 10001 --user-key TM-AB12CD34
```

### Посмотреть задачи пользователя

```powershell
python -m apps.vk_client.app.main tasks --user-key TM-AB12CD34
```

Только VK-задачи:

```powershell
python -m apps.vk_client.app.main tasks --user-key TM-AB12CD34 --source vk
```

### Создать задачу из VK

```powershell
python -m apps.vk_client.app.main add --user-key TM-AB12CD34 --title "Сделать VK flow" --description "Проверить привязку" --priority 2
```

## Почему мы это написали именно так

### `apps/backend`

Это ядро системы.
Здесь лежат:

- модели данных;
- правила создания и обновления задач;
- привязка пользователей к платформам;
- HTTP API.

### `apps/shared/task_manager_client.py`

Это общий клиент для API.
Он нужен, чтобы Telegram и VK не писали HTTP-запросы каждый по-своему.

### `apps/telegram_bot`

Это отдельный интерфейс для Telegram.
Он не должен знать, как устроена база данных.
Он должен только:

- определить пользователя Telegram;
- попросить backend вернуть или создать его аккаунт;
- запросить задачи;
- отправить команды пользователя в backend.

### `apps/vk_client`

Это первый шаг к VK-сценарию.
Пока это Python CLI, а не Mini App.
Но логика уже правильная:

- VK имеет свой `external_id`;
- VK привязывается к существующему `user_key`;
- задачи создаются с `source="vk"`.

Позже на этом месте можно сделать полноценный VK Mini App frontend.

## Тесты

Запуск тестов:

```powershell
pytest -q
```

## Следующий логичный шаг

Дальше можно делать одно из двух:

1. Развивать `apps/vk_client` до полноценного VK Mini App backend flow.
2. Добавить сущности списков или проектов, чтобы внутри одного пользователя задачи разделялись не только по `source`, но и по бизнес-смыслу.
