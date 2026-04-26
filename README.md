# Task Manager

Backend для менеджера задач на `FastAPI` с многопользовательской моделью, разделением задач по источникам и Telegram-ботом.

## Что умеет проект

- хранить задачи по пользователям, а не в одном общем списке;
- привязывать одного пользователя к нескольким платформам;
- разделять задачи по источнику: `telegram`, `vk`, `web`, `manual`;
- выдавать `user_key`, по которому можно связать Telegram и VK с одним аккаунтом;
- работать через API и через Telegram-бота.

## Стек

- Python
- FastAPI
- SQLAlchemy
- SQLite
- pytest
- aiogram

## Структура проекта

```text
task_manager/
|-- app/
|   |-- bot.py
|   |-- bot_utils.py
|   |-- config.py
|   |-- crud.py
|   |-- database.py
|   |-- dependencies.py
|   |-- main.py
|   |-- models.py
|   |-- schemas.py
|   |-- __init__.py
|   `-- services/
|       |-- tasks.py
|       |-- users.py
|       `-- __init__.py
|-- tests/
|   |-- conftest.py
|   |-- test_bot.py
|   |-- test_tasks.py
|   `-- __init__.py
|-- .env.example
|-- pyproject.toml
|-- pytest.ini
|-- README.md
|-- requirements.txt
|-- tasks.db
|-- test_tasks.db
`-- uv.lock
```

## Модель данных

В проекте теперь три основные сущности:

- `users`:
  внутренний пользователь системы с уникальным `user_key`
- `user_identities`:
  связь пользователя с внешней платформой, например `telegram` или `vk`
- `tasks`:
  задача, принадлежащая конкретному пользователю и имеющая `source`

Пример:

- пользователь пришел в Telegram;
- для него создается запись в `users`;
- Telegram-аккаунт сохраняется в `user_identities`;
- бот показывает `user_key`;
- потом этот `user_key` можно использовать в VK, чтобы привязать второй вход к тому же пользователю.

## API

Запуск API:

```powershell
uvicorn app.main:app --reload
```

Документация:

```text
http://127.0.0.1:8000/docs
```

### Переменные окружения

- `TASK_MANAGER_DATABASE_URL`, по умолчанию: `sqlite:///./tasks.db`
- `TASK_MANAGER_CORS_ORIGINS`, по умолчанию: `*`
- `TELEGRAM_BOT_TOKEN`

### Пользователи

Создать или найти пользователя по внешней платформе:

```http
POST /users/identify
```

Пример тела:

```json
{
  "provider": "telegram",
  "external_id": "123456789",
  "name": "Alice"
}
```

Привязать новую платформу к уже существующему пользователю:

```http
POST /users/link
```

Пример тела:

```json
{
  "provider": "vk",
  "external_id": "987654321",
  "user_key": "TM-AB12CD34"
}
```

Получить текущего пользователя по ключу:

```http
GET /users/me
X-User-Key: TM-AB12CD34
```

### Задачи

Все операции с задачами теперь выполняются в контексте пользователя через заголовок:

```http
X-User-Key: TM-AB12CD34
```

Создание задачи:

```http
POST /tasks
```

Пример тела:

```json
{
  "title": "Сделать VK-клиент",
  "description": "Подготовить интерфейс для Mini App",
  "status": "new",
  "priority": 3,
  "source": "web"
}
```

Получение задач:

```http
GET /tasks
GET /tasks?source=telegram
```

Доступные источники:

- `telegram`
- `vk`
- `web`
- `manual`

## Telegram-бот

Установка зависимостей и настройка токена:

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
$env:TELEGRAM_BOT_TOKEN="your-token"
```

Запуск:

```powershell
python -m app.bot
```

Команды:

- `/start`
- `/help`
- `/tasks` показывает только Telegram-задачи
- `/tasks_all` показывает все задачи пользователя
- `/task <id>`
- `/add <title> | <description> | <priority>`
- `/done <id>`
- `/delete <id>`
- `/key` показывает `user_key` для привязки VK

Бот автоматически определяет пользователя по `telegram user id` и создает или находит его запись в системе.

## Тесты

```powershell
pytest -q
```

## Следующий шаг

Следующий логичный этап:

- вынести VK-клиент в отдельный Python- или frontend-проект;
- использовать `user_key` для привязки VK к уже существующему Telegram-пользователю;
- добавить полноценную авторизацию и, при необходимости, списки задач или проекты поверх `source`.
