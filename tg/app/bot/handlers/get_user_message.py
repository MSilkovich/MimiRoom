# handlers/user_messages.py

from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# 2. Ваша функция, куда вы будете передавать текст
async def process_user_data(text: str, user_id: int):

    print(f"Получен текст от {user_id}: {text}")
    return f"Я сохранил твой текст: '{text}'"

# # 3. Обработчик команды (например, чтобы начать диалог)
# @router.message(Command("ask"))
# async def ask_name(message: types.Message):
#     await message.answer("Напиши мне что-нибудь, и я передам это в функцию.")

# 4. Обработчик обычного текста
@router.message()
async def handle_text(message: types.Message):
    # Игнорируем команды, чтобы они не попадали сюда
    if message.text.startswith('/'):
        return

    user_text = message.text
    result = await process_user_data(user_text, message.from_user.id)

    await message.answer(result)