"""
Путь: /api/v{version}/chat
- POST   /message                         — отправить сообщение в LLM (синхронно через HTTP)

Роутер для прямого HTTP-доступа к LLM (без Redis).
Основной поток сообщений идёт через Redis Stream consumer.
"""

from fastapi import APIRouter, Depends

from src.logging import get_logger
from src.schemas.incoming import IncomingMessage
from src.schemas.outgoing import OutgoingMessage
from src.services.llm_service import LLMService

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=OutgoingMessage)
async def handle_message(body: IncomingMessage) -> OutgoingMessage:
    """Отправить сообщение в LLM и получить ответ синхронно.

    Поля IncomingMessage:
    - user_id, provider, channel, external_id — для идентификации
    - text — текст сообщения
    - message_id — для идемпотентности
    - metadata — произвольные данные от адаптера
    - enrichments — (опционально) данные, добавленные на предыдущем этапе

    Возвращает OutgoingMessage с ответом LLM.
    """
    logger.info(
        "REST chat message: user_id=%s provider=%s message_id=%s",
        body.user_id, body.provider, body.message_id,
    )
    result = await LLMService.process_message(body.model_dump(mode="json"))
    return result
