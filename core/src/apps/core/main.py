import logging

from fastapi import FastAPI

from config.project_config import settings_app
from src.apps.core.routes import get_apps_router
from src.excpetions.hadlers import register_exception_handlers
from src.middleware.auth import AuthMiddleware
from src.middleware.error import ErrorMiddleware
from .lifespan import lifespan


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings_app.PROJECT_NAME,
        debug=False,
        version=settings_app.VERSION,
        lifespan=lifespan,
        description="""
## О приложении

API для информационной системы груминг-салона MiMiRoom:
запись питомцев на услуги, управление мастерами, складом расходников
и справочниками (породы, типы питомцев, единицы измерения).

Система построена вокруг **записей (bookings)**: клиент выбирает услугу,
мастера и время; услуга автоматически резервирует необходимые материалы
со склада согласно норме расхода.

Авторизация:
Access-токен передаётся в заголовке `Authorization: Bearer <token>`.
""",
        contact={
            "name": "Команда поддержки",
            "email": "gnom.48.spb@gmail.com",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {
                "name": "auth",
                "description": "Регистрация, вход, обновление и отзыв токенов. ",
            },
            {
                "name": "users",
                "description": "Профиль текущего пользователя и привязки к внешним провайдерам.",
            },
            {
                "name": "pets",
                "description": "Питомцы клиентов: создание, редактирование, привязка к владельцу и породе.",
            },
            {
                "name": "breeds",
                "description": "Справочник пород. Каждая порода относится к типу питомца.",
            },
            {
                "name": "pet-types",
                "description": "Справочник типов питомцев (собака, кошка, ...).",
            },
            {
                "name": "services",
                "description": "Услуги клиники: цена, длительность, порода и список расходников. "
                "При создании услуги можно сразу передать материалы со склада.",
            },
            {
                "name": "storage",
                "description": "Склад: материалы, единицы измерения и остатки.",
            },
            {
                "name": "measure-units",
                "description": "Справочник единиц измерения (мл, г, шт, ...).",
            },
            {
                "name": "books",
                "description": "Записи на услуги: питомец, мастер, дата/время, услуга, комментарий.",
            },
        ],
    )

    application.include_router(get_apps_router())

    # добавляется первым = внутренний слой
    application.add_middleware(ErrorMiddleware)
    # добавляется последним = внешний слой
    application.add_middleware(AuthMiddleware)
    # TODO: ErrorMiddleware

    register_exception_handlers(app=application)

    return application


app = get_application()
