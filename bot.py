import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from groq import Groq

# ============ НАСТРОЙКИ ============
TELEGRAM_TOKEN = "8373375366:AAEJyCescKsmltC9xMLtkKg9ocPNiM503X4"
GROQ_API_KEY = "AIzaSyCakMKDuS-k3XFjlBieTQa-iWokPo2GlkE"  # Получи на https://console.groq.com

# ============ ИНИЦИАЛИЗАЦИЯ ============
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — бот технической поддержки BotHost.ru.

Твои задачи:
- Помогать пользователям решать проблемы с кодом
- Отвечать на вопросы о хостинге ботов
- Помогать с Python, aiogram, телеграм ботами
- Исправлять ошибки в коде

Правила:
- Отвечай на русском языке
- Будь дружелюбным
- Давай конкретные решения с примерами кода"""

user_histories = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_histories[message.from_user.id] = []
    await message.answer(
        "👋 Привет! Я бот техподдержки **BotHost.ru**\n\n"
        "Помогу с кодом, ошибками и хостингом!\n\n"
        "📝 Напиши свой вопрос\n"
        "/clear — очистить историю",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_histories[message.from_user.id] = []
    await message.answer("🗑 История очищена!")

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        user_histories[user_id].append({"role": "user", "content": message.text})
        
        # Ограничиваем историю
        history = user_histories[user_id][-20:]
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history
        )
        
        answer = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": answer})
        
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await message.answer(answer[i:i+4000])
        else:
            await message.answer(answer)
            
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
