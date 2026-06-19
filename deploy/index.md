# Deploy

## Структура

| Файл/Папка | Назначение |
|------------|------------|
| `docker-compose.yaml` | Production стек |
| `docker-compose.local.yml` | Локальная инфраструктура для разработки |
| `Dockerfile` | Образ backend API |
| `nginx/` | Конфиги Nginx |
| `docker/` | Скрипты инициализации контейнеров |

## Переменные

Все секреты в `.env` файле (на основе `.env.example`).  
В `docker-compose.yaml` только ссылки: `${DB_PASSWORD}`.

## Команды

```bash
just infra-up        # поднять локальную инфраструктуру
just dev             # infra + миграции + api
just deploy-up       # production стек
just deploy-migrate  # применить миграции на production
just deploy-logs     # смотреть логи
```

## Что менять в новом проекте

| Место | Что менять |
|-------|------------|
| `nginx/internal.conf` | `server_name`, TLS сертификаты |
| `docker-compose.yaml` | PostgreSQL параметры (shared_buffers и т.д.) |
| `Dockerfile` | Имя образа, `CMD` workers |
| `.env.example` | Все `CHANGE` комментарии |
| `docker/init-db.sh` | Read-only пользователи, extensions |

## TLS / HTTPS

Раскомментировать ssl_* блок в `nginx/internal.conf`.  
Сертификаты монтировать через Docker volume или secrets.
