# Code Battle

Учебная соревновательная платформа для решения алгоритмических задач. Проект
переписывает идеи из `dop3file/code_versus` на асинхронный FastAPI и современный
Python-стек.

## Архитектурное направление

- FastAPI обслуживает внешний HTTP API.
- PostgreSQL хранит пользователей, каталог задач, отправки и результаты;
  изменения схемы ведутся через Alembic.
- MongoDB хранит входные/ожидаемые данные закрытых тест-кейсов; изменения
  документов и индексов будут отдельными версируемыми миграциями.
- Redis используется как брокер Celery и позднее — только для оправданного кеша.
- Выполнение пользовательского кода будет вынесено из API в изолированный judge.

Подробная последовательность работы: [docs/ROADMAP.md](docs/ROADMAP.md).

## Локальный запуск

Требования: Docker с Compose и `uv`.

```bash
cp .env.example .env
uv sync
docker compose up --build
```

После старта:

- health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`
- MongoDB: `localhost:27017`
- Redis: `localhost:6380` (внутри Compose остаётся `redis:6379`)

Полезные команды:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
docker compose down
```

`uv.lock` коммитится в репозиторий. `.env` и данные контейнеров — нет.
