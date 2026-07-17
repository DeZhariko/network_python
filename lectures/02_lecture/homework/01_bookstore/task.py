"""CRUD API для книжного магазина."""

from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════
# МОДЕЛИ
# ═══════════════════════════════════════════════════════════

class Category(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    model_config = {"extra": "forbid"}


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str) -> str:
        if len(value) not in (10, 13):
            raise ValueError("ISBN must contain 10 or 13 digits")

        if not value.isdigit():
            raise ValueError("ISBN must contain only digits")

        return value


class Book(BookBase):
    id: int


class BookCreate(BookBase):
    model_config = {"extra": "forbid"}


# ═══════════════════════════════════════════════════════════
# ИСКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════════

class BookNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=404,
            detail="Book not found",
        )


class DuplicateIsbnException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            detail="Book with this ISBN already exists",
        )


# ═══════════════════════════════════════════════════════════
# ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Bookstore API")

BOOKS: list[dict] = []
CATEGORIES: list[dict] = []


@app.exception_handler(BookNotFoundException)
async def book_not_found_handler(
    request: Request,
    exc: BookNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Book not found",
            "code": "NOT_FOUND",
        },
    )


@app.exception_handler(DuplicateIsbnException)
async def duplicate_isbn_handler(
    request: Request,
    exc: DuplicateIsbnException,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Book with this ISBN already exists",
            "code": "DUPLICATE_ISBN",
        },
    )


def next_id(items: list[dict]) -> int:
    """Получить новый id без сдвига старых id после удаления."""
    return max((item["id"] for item in items), default=0) + 1


def find_book_index(book_id: int) -> int:
    """Найти индекс книги в хранилище."""
    for index, book in enumerate(BOOKS):
        if book["id"] == book_id:
            return index

    raise BookNotFoundException()


def validate_category(category_id: Optional[int]) -> None:
    """Проверить существование указанной категории."""
    if category_id is None:
        return

    if not any(category["id"] == category_id for category in CATEGORIES):
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )


# ═══════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════

@app.get("/categories")
def list_categories() -> list[dict]:
    return CATEGORIES


@app.post("/categories", status_code=201)
def create_category(category: CategoryCreate) -> dict:
    new_category = {
        "id": next_id(CATEGORIES),
        **category.model_dump(),
    }

    CATEGORIES.append(new_category)
    return new_category


# ═══════════════════════════════════════════════════════════
# CRUD КНИГ
# ═══════════════════════════════════════════════════════════

@app.get("/books")
def list_books(
    category_id: Optional[int] = None,
    year: Optional[int] = None,
) -> list[dict]:
    result = BOOKS

    if category_id is not None:
        result = [
            book
            for book in result
            if book["category_id"] == category_id
        ]

    if year is not None:
        result = [
            book
            for book in result
            if book["year"] == year
        ]

    return result


@app.get("/books/search")
def search_books(query: str) -> list[dict]:
    normalized_query = query.casefold()

    return [
        book
        for book in BOOKS
        if normalized_query in book["title"].casefold()
        or normalized_query in book["author"].casefold()
    ]


@app.get("/books/{book_id}")
def get_book(book_id: int) -> dict:
    index = find_book_index(book_id)
    return BOOKS[index]


@app.post("/books", status_code=201)
def create_book(book: BookCreate) -> dict:
    if any(existing["isbn"] == book.isbn for existing in BOOKS):
        raise DuplicateIsbnException()

    validate_category(book.category_id)

    new_book = {
        "id": next_id(BOOKS),
        **book.model_dump(),
    }

    BOOKS.append(new_book)
    return new_book


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate) -> dict:
    index = find_book_index(book_id)

    if any(
        existing["isbn"] == book.isbn
        and existing["id"] != book_id
        for existing in BOOKS
    ):
        raise DuplicateIsbnException()

    validate_category(book.category_id)

    updated_book = {
        "id": book_id,
        **book.model_dump(),
    }

    BOOKS[index] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int) -> Response:
    index = find_book_index(book_id)
    BOOKS.pop(index)

    return Response(status_code=204)