# Domain: `example_domain`

> Это пример структуры домена. Переименуй папку в реальное имя домена (`users`, `reports`, `orders` и т.д.) и замени `example` → имя своего домена во всех файлах.

## Назначение

Каждый домен — это изолированный модуль, реализующий одну бизнес-сущность.  
Домены не зависят друг от друга напрямую — взаимодействие через общие типы или Kafka-события.

## Структура файлов

| Файл | Назначение |
|------|------------|
| `db_models.py` | SQLAlchemy ORM модели. Только хранение данных, никакой бизнес-логики |
| `schemas/domain.py` | Pydantic модели для **входящих** запросов (request body, query params) |
| `schemas/dto.py` | Pydantic модели для **исходящих** ответов (response_model в роутере) |
| `api/routes.py` | FastAPI роутер. Только HTTP-слой: валидация, вызов UseCase, маппинг None → 404 |
| `usecases/` | Бизнес-логика. Один файл = один UseCase |

## Правила именования

- Файлы UseCase: `<действие>_<сущность>_usecase.py` → `create_order_usecase.py`
- Классы UseCase: `CreateOrderUseCase`
- ORM модели: `OrderModel`
- Pydantic request: `CreateOrderRequest`, `UpdateOrderRequest`
- Pydantic response: `OrderDTO`, `OrderListDTO`

## Что добавить при создании нового домена

1. Создать папку `backend/app/<domain>/`
2. Создать все 5 файлов/папок (см. выше)
3. Добавить ORM модели в `backend/migrations/env.py`
4. Создать `shared/di/providers/<domain>.py` с `XxxProvider`
5. Зарегистрировать провайдер в `shared/di/providers/provider.py`
6. Добавить роутер в `app/api/router.py`
7. Добавить builders в `tests/builder.py`
8. Создать папку тестов `tests/<domain>/`
