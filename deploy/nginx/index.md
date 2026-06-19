# Nginx Configuration

## Файлы

| Файл | Назначение |
|------|------------|
| `nginx.conf` | Глобальные настройки (worker_processes, gzip, client_max_body_size) |
| `internal.conf` | Virtual host — маршрутизация `/api/` → backend, `/` → frontend |

## Что обязательно менять

1. `server_name` в `internal.conf` — твой домен
2. `client_max_body_size` — должно совпадать с `MAX_FILE_SIZE` в usecase'ах
3. TLS сертификаты — раскомментировать ssl_* блок

## Добавить HTTPS (Let's Encrypt)

```nginx
listen 443 ssl http2;
ssl_certificate     /etc/nginx/certs/fullchain.pem;
ssl_certificate_key /etc/nginx/certs/privkey.pem;
ssl_protocols TLSv1.2 TLSv1.3;
```

Редирект HTTP → HTTPS:

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
```

## Добавить новый upstream сервис

```nginx
upstream my_service {
    server my_service:8001;
}

location /api/v2/ {
    proxy_pass http://my_service;
    ...
}
```
