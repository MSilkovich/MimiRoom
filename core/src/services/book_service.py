from src.models.book import Book, BookStatus
from src.models.book_service import BookService
from src.models.service import Service
from src.repositories.book_repository import BookRepository
from src.repositories.book_service_repository import BookServiceRepository
from src.repositories.service_repository import ServiceRepository
from src.schemas import BookCreate, BookRead, BookUpdate
from .base import BaseService


class BookServiceService(BaseService[Book, BookCreate, BookUpdate]):
    model = Book

    async def create(self, data: BookCreate) -> Book:
        async with self.uow_factory() as uow:
            book_repo: BookRepository = uow.repository(Book)
            book_service_repo: BookServiceRepository = uow.repository(
                BookService)
            service_repo: ServiceRepository = uow.repository(Service)

            payload = data.model_dump(exclude={"services"})
            payload["status"] = BookStatus.PENDING

            book = await book_repo.create(payload)

            if data.services:
                service_ids = {s.service_id for s in data.services}
                services = await service_repo.get_many_by_ids(service_ids)
                service_map = {s.service_id: s for s in services}

                missing = service_ids - service_map.keys()
                if missing:
                    raise ValueError(f"Services not found: {missing}")

                items = []
                for item in data.services:
                    svc = service_map[item.service_id]
                    if svc.is_deleted:
                        raise ValueError(
                            f"Service {svc.service_id} is deleted")

                    items.append({
                        "book_id": book.book_id,
                        "service_id": svc.service_id,
                        "master_id": item.master_id,
                        "service_name": svc.title,
                        "price_at_booking": svc.price,
                    })

                await book_service_repo.create_many(items)

            await uow.commit()
            return book
