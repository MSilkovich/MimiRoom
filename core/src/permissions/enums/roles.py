from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"          # полный доступ
    MANAGER = "manager"      # управление записями, услугами, складом
    GROOMER = "groomer"      # мастер: только свои записи
    CLIENT = "client"        # клиент: свои питомцы, свои записи
