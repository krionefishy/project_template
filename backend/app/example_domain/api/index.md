# API Routes слой

## Назначение

API роутер — тонкий HTTP-адаптер. Он:
- Принимает и валидирует входящие данные (через Pydantic)
- Делегирует выполнение UseCase
- Маппит результат в HTTP-ответ (`None` → 404, `result` → 200/201/202)
- Декларирует зависимости через `Depends` и `FromDishka`

## Правила

### Обязательный шаблон роута

```python
@router.post("/", response_model=EntityDTO, status_code=201)
async def create_entity(
    request: CreateEntityRequest,                          # тело запроса
    auth: Annotated[AuthContext, Depends(require_auth)],   # аутентификация
    usecase: FromDishka[CreateEntityUseCase],              # UseCase из Dishka
) -> EntityDTO:
    result = await usecase.execute(request, auth)
    if result is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    return result
```

### Коды ответов

| Ситуация | Код |
|----------|-----|
| Создание сущности | 201 |
| Постановка в очередь (Kafka) | 202 |
| Не найдено (None от UseCase) | 404 |
| Нет доступа (None от UseCase) | 403 |
| Ошибка авторизации | 401 (автоматически через `require_auth`) |

### Загрузка файлов

- Принимать через `UploadFile = File(...)`
- Читать байты: `payload = await file.read()`
- Передавать в UseCase — UseCase занимается валидацией и отправкой в Kafka
- Возвращать 202 (очередь), не 200 (не готово)

### Обязательные элементы роутера

```python
router = APIRouter(
    prefix="/entities",
    tags=["entities"],       # имя группы в Swagger
    route_class=DishkaRoute, # обязательно для работы FromDishka
)
```
