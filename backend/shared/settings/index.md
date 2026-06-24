# Settings / Configuration

## Механизм конфигурации

Конфигурация загружается из YAML файла через `pydantic-settings`. Секреты передаются через переменные окружения.

## YAML файлы

| Файл | Когда используется |
|------|--------------------|
| `config.yaml` | Локальная разработка (gitignore!) |
| `config.yaml.example` | Шаблон, коммитится в git |
| `config.test.yaml` | pytest |
| `config.prod.yaml` | Production |

## Env override

Следующие переменные окружения всегда переопределяют YAML:

- `DATABASE_URL` — полная строка подключения к PostgreSQL
- `KAFKA_BOOTSTRAP_SERVERS` — Kafka брокеры
- `CONFIG_PATH` — путь к YAML файлу конфигурации
- `JWT_SECRET` — секрет для подписи access token

## Добавление нового параметра

1. Добавить поле в соответствующую Pydantic-модель в `backend/shared/config.py`
2. Добавить в все `.yaml` файлы
3. Задокументировать в `config.yaml.example`

## Правила

- Никогда не хардкодить секреты в `.yaml` файлах
- Production секреты только через env vars или secrets manager
- Пароли/ключи в `.env` файле (gitignore!)
