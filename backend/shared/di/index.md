# Dependency Injection (Dishka)

## Архитектура DI

Используем [Dishka](https://dishka.readthedocs.io/) — async DI фреймворк для Python.

## Скоупы

| Scope | Кто | Создаётся |
|-------|-----|-----------|
| `APP` | DB, Redis, Kafka, S3, PasswordService, RsaKeyProvider | Один раз при старте приложения |
| `REQUEST` | AsyncSession, все UseCase'ы, AuthContext | На каждый HTTP-запрос |

## Структура providers/

| Файл | Назначение |
|------|------------|
| `app.py` | `AppProvider` (инфраструктура) + `SessionProvider` (AsyncSession) |
| `auth.py` | `AuthProvider` (сервисы auth) + `AuthUsecaseProvider` |
| `<domain>.py` | `XxxProvider` — usecase'ы конкретного домена |
| `provider.py` | `ALL_PROVIDERS` — итоговый список для `make_async_container()` |

## Как добавить новый домен

1. Создать файл `shared/di/providers/<domain>.py`:

```python
from dishka import Provider, Scope, provide
from backend.app.my_domain.usecases.create_item_usecase import CreateItemUseCase

class MyDomainProvider(Provider):
    scope = Scope.REQUEST

    create_item = provide(CreateItemUseCase)
    # Или вручную, если нужны нестандартные зависимости:
    # @provide
    # def create_item(self, session, kafka) -> CreateItemUseCase:
    #     return CreateItemUseCase(session, kafka)
```

2. Добавить в `provider.py`:

```python
from backend.shared.di.providers.my_domain import MyDomainProvider

ALL_PROVIDERS = [
    ...
    MyDomainProvider(),
]
```

## Инъекция в роутах

```python
from dishka.integrations.fastapi import DishkaRoute, FromDishka

router = APIRouter(route_class=DishkaRoute)

@router.get("/")
async def handler(usecase: FromDishka[MyUseCase]) -> ...:
    ...
```
