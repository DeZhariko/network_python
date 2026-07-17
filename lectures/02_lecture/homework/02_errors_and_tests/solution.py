"""Исправленное FastAPI-приложение."""

import asyncio
import threading

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel


app = FastAPI()

ITEMS: dict[int, dict] = {}
NEXT_ID = 1

COUNTER = 0

items_lock = threading.Lock()
counter_lock = threading.Lock()


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str = ""


@app.get("/items")
def list_items() -> dict:
    """Вернуть список всех элементов."""
    with items_lock:
        return {
            "items": list(ITEMS.values()),
        }


@app.get("/items/{item_id}")
def get_item(item_id: int) -> dict:
    """Вернуть элемент по идентификатору."""
    with items_lock:
        item = ITEMS.get(item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )

    return item


@app.post("/items", status_code=201)
def create_item(item: ItemCreate) -> dict:
    """Создать новый элемент."""
    global NEXT_ID

    with items_lock:
        item_id = NEXT_ID
        NEXT_ID += 1

        new_item = {
            "id": item_id,
            "name": item.name,
        }

        ITEMS[item_id] = new_item

    return new_item


@app.get("/items/{item_id}/counter")
def get_counter(item_id: int) -> dict:
    """Потокобезопасно увеличить общий счётчик."""
    global COUNTER

    with counter_lock:
        COUNTER += 1
        current_value = COUNTER

    return {
        "counter": current_value,
    }


@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    update: ItemUpdate,
) -> dict:
    """Изменить существующий элемент."""
    with items_lock:
        if item_id not in ITEMS:
            raise HTTPException(
                status_code=404,
                detail="Item not found",
            )

        updated_item = {
            "id": item_id,
            "name": update.name,
        }

        ITEMS[item_id] = updated_item

    return updated_item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> Response:
    """Удалить элемент."""
    with items_lock:
        if item_id not in ITEMS:
            raise HTTPException(
                status_code=404,
                detail="Item not found",
            )

        del ITEMS[item_id]

    return Response(status_code=204)


@app.get("/divide")
def divide(a: int, b: int) -> dict:
    """Разделить a на b."""
    if b == 0:
        raise HTTPException(
            status_code=400,
            detail="Division by zero",
        )

    return {
        "result": a / b,
    }


@app.get("/slow-sync")
async def slow_sync() -> dict:
    """Выполнить неблокирующее ожидание."""
    await asyncio.sleep(0.5)

    return {
        "status": "done",
    }