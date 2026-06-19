# PostgreSQL Storage

## `Database` класс

Singleton-обёртка над SQLAlchemy `async_engine` + `async_sessionmaker`.  
Инициализируется в `Application._startup()`, передаётся в Dishka context.

## Паттерны работы с БД

Всегда используем SQLAlchemy query builder. `session.add()` — не используем.

### SELECT

```python
result = await self.session.execute(
    select(UserModel).where(UserModel.id == user_id)
)
user = result.scalar_one_or_none()
```

### SELECT список

```python
result = await self.session.execute(
    select(MyModel)
    .where(MyModel.status == "active")
    .order_by(MyModel.created_at.desc())
    .limit(100)
)
items = list(result.scalars())
```

### INSERT (возвращает созданный объект)

```python
result = await self.session.execute(
    insert(MyModel)
    .values(id=uuid.uuid4(), title=request.title, status="active")
    .returning(MyModel)
)
record = result.scalar_one()
await self.session.commit()
```

### UPDATE

```python
await self.session.execute(
    update(MyModel)
    .where(MyModel.id == record_id)
    .values(status="done", updated_at=func.now())
)
await self.session.commit()
```

### DELETE

```python
await self.session.execute(delete(MyModel).where(MyModel.id == record_id))
await self.session.commit()
```

## ORM модели

Все модели наследуют `Base` из `database.py`.  
Расположение: `backend/app/<domain>/db_models.py`.

## Миграции

- Движок: Alembic
- Команда: `just db-create-migration "описание"`
- Применить: `just db-migrate`
- При добавлении новых моделей — импортировать в `migrations/env.py`
