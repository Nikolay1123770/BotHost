import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from groq import Groq

# ==========================================
# 👇 ВНИМАТЕЛЬНО ЗАПОЛНИ ЭТИ ДВЕ СТРОЧКИ 👇
# ==========================================

# 1. Твой ключ от Groq (начинается на gsk_)
GROQ_API_KEY = "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"

# 2. Токен от BotFather (цифры:буквы)
TELEGRAM_TOKEN = "8373375366:AAEJyCescKsmltC9xMLtkKg9ocPNiM503X4"

# ==========================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация Groq
client = Groq(api_key=GROQ_API_KEY)

# Актуальная модель (Mixtral удалили, используем Llama 3.3)
CURRENT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Ты — дружелюбный бот технической поддержки BotHost.ru. 
Твоя задача — помогать пользователям с их ботами (Python, aiogram) и хостингом.
Отвечай кратко, по делу и на русском языке. Код пиши в блоках."""

user_histories = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_histories[message.from_user.id] = []
    await message.answer(
        "👋 **Привет! Я техподдержка BotHost.**\n\n"
        "Я обновлен и работаю на модели **Llama 3.3** (через Groq).\n"
        "Задай мне любой вопрос по коду!",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_histories[message.from_user.id] = []
    await message.answer("✅ Память бота очищена.")

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_histories: user_histories[user_id] = []
    
    # Показываем статус "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Добавляем сообщение в историю
        user_histories[user_id].append({"role": "user", "content": message.text})
        
        # Ограничиваем историю (последние 8 сообщений), чтобы не перегружать
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user_id][-8:]
        
        completion = client.chat.completions.create(
            model=CURRENT_MODEL,
            messages=messages_payload,
            temperature=0.7,
            max_tokens=1024,
        )
        
        answer = completion.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": answer})
        
        await message.answer(answer, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error: {error_msg}")
        
        if "401" in error_msg:
            await message.answer("❌ Ошибка ключа API. Проверь GROQ_API_KEY в коде.")
        elif "400" in error_msg:
             await message.answer("❌ Ошибка модели. Попробуй позже.")
        else:
            await message.answer(f"❌ Ошибка: {error_msg}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
