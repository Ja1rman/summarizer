# Summarizer

Бот для Mattermost/Time, который собирает сообщения из треда и делает краткое резюме через LLM proxy.

## Возможности

- Суммаризация треда по slash-команде `/summarize`.
- Суммаризация треда по упоминанию `@summarize`.
- Дополнительный пользовательский prompt после команды или тега.
- Ответ на вопрос по содержимому треда через endpoint `/answer`.
- Метрики Prometheus на `/metrics`.
- Healthcheck на `/healthz`.

## Как работает

### Slash-команда

Endpoint `/summarize` принимает form-data от Mattermost:

- `text` - ссылка на тред и/или дополнительный prompt.
- `root_id` - id текущего треда, если команда вызвана внутри треда.
- `user_id` - пользователь для метрик.

Если первым словом в `text` передана ссылка, id треда берется из ссылки. Иначе используется `root_id`.

Примеры:

```text
/summarize
/summarize выдели проблему и решение
/summarize https://time.example/team/pl/postid выдели проблему и решение
```

### Упоминание бота

Сервис слушает websocket-события Mattermost `posted` и реагирует на сообщения с `@summarize`.

Примеры:

```text
@summarize
@summarize выдели проблему, опиши как ее решили
@summarize https://time.example/team/pl/postid выдели проблему и решение
```

Если упоминание отправлено внутри треда, используется `root_id`. Если упоминание отправлено в корневом сообщении, используется `post.id`.

## API

### `GET /healthz`

Проверка доступности сервиса.

Ответ:

```json
{"status": 200}
```

### `POST /summarize`

Создает резюме треда и возвращает ответ в формате Mattermost response.

Form-data:

- `text`
- `root_id`
- `user_id`

### `POST /answer`

Отвечает на вопрос по содержимому треда.

Form-data:

- `thread_id`
- `question`
- `user_id`

### `GET /metrics`

Prometheus-метрики сервиса.

## Конфигурация

Переменные окружения:

- `TIME_BOT_TOKEN` - токен бота Mattermost/Time.
- `GPT_TOKEN` - токен для LLM proxy.
- `SAGE_ENV` - окружение для логов, по умолчанию `test`.
- `SAGE_SYSTEM` - имя системы для логов, по умолчанию `summarizer`.
- `SAGE_SERVER` - сервер/дата-центр для логов, по умолчанию `m1`.
- `SAGE_GROUP` - группа для логов, по умолчанию `bot_workflow`.
- `POD_NAME` - имя инстанса, по умолчанию `unknown`.

## Локальный запуск

Требуется Python 3.13 и Poetry.

```bash
poetry install
TIME_BOT_TOKEN=... GPT_TOKEN=... poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

Без реальных токенов можно проверять только синтаксис и локальные unit-тесты/заглушки. Проверки с Mattermost или LLM proxy используют внешние endpoint'ы и требуют отдельного разрешения.

## Docker

Образ собирается из `Dockerfile`. В runtime используется `leader-election`, который запускает:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Основные файлы

- `main.py` - HTTP API Starlette.
- `src/time_messages_handler.py` - websocket-обработчик Mattermost и разбор `@summarize`.
- `src/time_requests.py` - получение и сборка сообщений треда.
- `src/general.py` - сценарии суммаризации и ответа на вопрос.
- `src/gpt.py` - запросы к LLM proxy.
- `src/time_client.py` - отправка ответа в Mattermost/Time.
- `src/stats_pusher.py` - Prometheus-метрики.
- `src/logger.py` - JSON-логи.
