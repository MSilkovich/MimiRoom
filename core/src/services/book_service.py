from ..models.book import Book
from ..schemas import BookCreate, BookUpdate
from .base_service import BaseService


class BookService(BaseService[Book, BookCreate, BookUpdate]):
    model = Book
