from ..models.book import Book
from .sqlalchemy_repository import SqlAlchemyRepository


class BookRepository(SqlAlchemyRepository[Book]):
    def __init__(self, session):
        super().__init__(Book, session)
