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

## Подключение в другой компании

Проект можно использовать как основу для Mattermost-бота, но перед внедрением нужно адаптировать внутренние адреса, токены и правила безопасности под инфраструктуру компании.

### Что нужно подготовить

- Mattermost/Time workspace с правами на создание bot account и slash-команд.
- Bot account с username `summarize` или другим именем, под которое будет изменен поиск упоминания в `src/time_messages_handler.py`.
- Personal access token или bot token с правами читать треды и создавать сообщения.
- Доступ сервиса к Mattermost API и websocket.
- LLM endpoint, которому разрешено передавать текст пользовательских тредов.
- Секреты для `TIME_BOT_TOKEN` и `GPT_TOKEN` в secret storage компании.
- Публичный или внутренний HTTPS URL сервиса, доступный Mattermost для slash-команды.

### Что нужно изменить в коде

В текущей версии часть адресов завязана на внутреннюю инфраструктуру:

- `src/config.py` - `TIME_DRIVER_CONFIG.url` сейчас указывает на `api-time.tinkoff.ru`.
- `src/time_requests.py` - URL получения треда сейчас собирается как `https://api-time.tinkoff.ru/api/v4/posts/{post_id}/thread`.
- `src/gpt.py` - LLM proxy сейчас задан как `https://llm-proxy.t-tech.team/chat/completions`.
- `pyproject.toml` - Poetry source указывает на внутренний package registry.
- `Dockerfile` - base image, builder image и `leader-election` берутся из внутреннего registry.
- `unic.yaml` - deployment-конфигурация рассчитана на текущую платформу.

Для переносимого внедрения лучше вынести Mattermost host и LLM URL в переменные окружения, а Dockerfile заменить на base image и registry, принятые в новой компании.

### Настройка Mattermost

1. Создайте bot account.
2. Выдайте боту токен и сохраните его как `TIME_BOT_TOKEN`.
3. Добавьте бота в публичные и закрытые каналы, где он должен читать треды. Для закрытых каналов без участия бота API вернет ошибку доступа.
4. Создайте slash-команду `/summarize`.
5. Укажите request URL:

```text
https://<summarizer-service-host>/summarize
```

6. Метод запроса: `POST`.
7. Response username можно указать `summarize`.
8. Для обработки упоминаний убедитесь, что websocket-подключение бота получает события `posted` из нужных каналов.

### Требования к сетевым доступам

Ingress:

- Mattermost должен иметь доступ к `POST /summarize`.
- Внутренние клиенты, если используются, должны иметь доступ к `POST /answer`.
- Monitoring должен иметь доступ к `GET /metrics`.

Egress:

- Сервис должен иметь доступ к Mattermost REST API.
- Сервис должен иметь доступ к Mattermost websocket.
- Сервис должен иметь доступ к LLM proxy.

### Права бота

Боту нужны права:

- читать сообщения и треды в каналах, где используется суммаризация;
- отправлять ответы в канал;
- подключаться к websocket API;
- читать attachments и fields в сообщениях, если они используются в обсуждениях.

Код не фильтрует сообщения по автору, поэтому в суммаризацию попадают и сообщения пользователей, и сообщения ботов, если Mattermost API возвращает их в треде.

### Безопасность и комплаенс

- Текст треда отправляется во внешний для Mattermost LLM endpoint. Перед внедрением проверьте, что это разрешено политиками компании.
- Не используйте публичный LLM endpoint для тредов с персональными данными, коммерческой тайной или инцидентами без согласованного контура обработки данных.
- Логи содержат техническую информацию о запросах и могут включать пользовательский prompt. При необходимости сократите логирование prompt'ов.
- Храните `TIME_BOT_TOKEN` и `GPT_TOKEN` только в secret storage, не в репозитории и не в plain-text deployment manifests.
- Добавьте rate limiting или квоты на стороне gateway/ingress, если бот будет доступен большому числу пользователей.

### Проверка после подключения

Минимальный smoke test в тестовом канале:

1. Добавить бота в канал.
2. Создать тред из нескольких сообщений.
3. Внутри треда отправить:

```text
@summarize выдели проблему и решение
```

4. Проверить, что бот ответил в тред.
5. Вызвать slash-команду внутри треда:

```text
/summarize выдели проблему и решение
```

6. Проверить метрики на `/metrics`.
7. Проверить ошибочный сценарий: вызвать бота в закрытом канале, куда он не добавлен, и убедиться, что возвращается понятное сообщение об ошибке доступа.

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
