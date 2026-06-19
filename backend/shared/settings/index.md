# Settings / Configuration

## Механизм конфигурации

Конфигурация загружается из YAML файла. Секреты передаются через переменные окружения.

## YAML файлы

| Файл | Когда используется |
|------|--------------------|
| `config.yaml` | Локальная разработка (gitignore!) |
| `config.yaml.example` | Шаблон, коммитится в git |
| `config.test.yaml` | pytest |
| `config.docker.yaml` | docker-compose (может содержать `${ENV_VAR}` подстановки) |
| `config.production.yaml` | Production (генерируется скриптом, gitignore!) |

## Env override

Следующие переменные окружения всегда переопределяют YAML:

- `DATABASE_URL` — полная строка подключения к PostgreSQL
- `KAFKA_BOOTSTRAP_SERVERS` — Kafka брокеры
- `CONFIG_PATH` — путь к YAML файлу конфигурации
- `ENV` — имя окружения (`local`, `test`, `docker`, `production`)

## Добавление нового параметра

1. Добавить поле в соответствующий dataclass в `config.py` (или создать новый)
2. Добавить в все `.yaml` файлы
3. Задокументировать в `config.yaml.example` с комментарием `# CHANGE:`

## Правила

- Никогда не хардкодить секреты в `.yaml` файлах
- Production секреты только через env vars или secrets manager
- Пароли/ключи в `.env` файле (gitignore!)
