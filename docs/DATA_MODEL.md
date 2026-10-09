# Модель данных Code Battle

## Границы хранилищ

PostgreSQL является источником истины для пользователей, условий задач,
отправок и результатов проверки. MongoDB хранит версии закрытых тест-наборов.
Redis не является постоянным хранилищем: он используется очередью Celery,
rate limit и краткоживущими блокировками.

Связь PostgreSQL с MongoDB выполняется по UUID задачи и номеру ревизии
тест-набора. Между разными СУБД внешнего ключа нет, поэтому согласованность
контролирует прикладной сервис.

## `users`

Реализована в `app/models/user.py`.

| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | UUID, PK | Идентификатор пользователя |
| `email` | varchar(320) | Email для входа |
| `username` | varchar(32) | Публичное имя |
| `password_hash` | varchar(255) | Argon2-хеш, никогда не пароль |
| `role` | user/admin | Авторизация административных действий |
| `rating` | integer | Материализованный рейтинг |
| `is_active` | boolean | Возможность войти и отправлять решения |
| `is_verified` | boolean | Подтверждение email |
| `created_at` | timestamptz | Время регистрации |
| `updated_at` | timestamptz | Время последнего изменения |

Email и username уникальны без учёта регистра. Счётчики отправок и решённых
задач не находятся в `users`: сначала они вычисляются из submissions, а при
необходимости оптимизации будут вынесены в отдельную статистику.

## `problems`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | UUID, PK | Идентификатор задачи и связь с MongoDB |
| `slug` | varchar(100), unique | Стабильный URL задачи |
| `title` | varchar(200) | Название |
| `statement` | text | Условие в Markdown |
| `difficulty` | enum | easy/medium/hard |
| `time_limit_ms` | integer | Ограничение времени |
| `memory_limit_mb` | integer | Ограничение памяти |
| `is_published` | boolean | Видимость пользователям |
| `author_id` | UUID, FK users, nullable | Автор или администратор |
| `version` | integer | Версия публичного условия |
| timestamps | timestamptz | Создание и изменение |

Ограничения: положительные time/memory limits и version, уникальный slug.
Публичные примеры являются частью условия, закрытые входы и ожидаемые ответы
хранятся только в MongoDB.

## `submissions`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | UUID, PK | Идентификатор отправки и сообщения Celery |
| `user_id` | UUID, FK users | Автор решения |
| `problem_id` | UUID, FK problems | Решаемая задача |
| `language` | varchar(32) | Идентификатор языка и версии runner |
| `source_code` | text | Отправленный исходный код |
| `status` | enum | Текущее состояние проверки |
| `score` | integer | Итоговый балл |
| `problem_version` | integer | Снапшот версии условия |
| `test_set_revision` | integer | Ревизия тестов MongoDB |
| `started_at` | timestamptz, nullable | Начало judge |
| `finished_at` | timestamptz, nullable | Завершение judge |
| timestamps | timestamptz | Постановка в очередь и изменение |

Состояния: `queued -> running -> accepted | wrong_answer |
time_limit_exceeded | memory_limit_exceeded | runtime_error | system_error`.
Переходы проверяются сервисом. Индексы нужны для истории пользователя,
очереди по статусу и отправок по задаче.

## `submission_cases`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | UUID, PK | Идентификатор результата теста |
| `submission_id` | UUID, FK submissions | Родительская отправка |
| `ordinal` | integer | Позиция теста в ревизии |
| `verdict` | enum | Результат теста |
| `duration_ms` | integer, nullable | Время выполнения |
| `memory_kb` | integer, nullable | Использованная память |
| `message` | text, nullable | Безопасное диагностическое сообщение |
| timestamps | timestamptz | Создание и изменение |

Пара `(submission_id, ordinal)` уникальна. Таблица не хранит входные данные и
ожидаемые ответы закрытых тестов. Каскадное удаление допустимо только от
submission к её case-результатам.

## Связи

```text
users 1 ─── N problems       (author_id)
users 1 ─── N submissions    (user_id)
problems 1 ─── N submissions (problem_id)
submissions 1 ─── N submission_cases
problems 1 ─── N test-set revisions in MongoDB
```
