import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
import google.generativeai as genai

# ============ НАСТРОЙКИ ============
TELEGRAM_TOKEN = "8373375366:AAEJyCescKsmltC9xMLtkKg9ocPNiM503X4"
GEMINI_API_KEY = "AIzaSyCakMKDuS-k3XFjlBieTQa-iWokPo2GlkE"  # Твой полный ключ

# ============ ИНИЦИАЛИЗАЦИЯ ============
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Системный промпт
SYSTEM_PROMPT = """Ты — бот технической поддержки BotHost.ru.

Твои задачи:
- Помогать пользователям решать проблемы с кодом
- Отвечать на вопросы о хостинге ботов
- Помогать с Python, aiogram, телеграм ботами
- Исправлять ошибки в коде

Правила:
- Отвечай на русском языке
- Будь дружелюбным и терпеливым
- Давай конкретные решения с примерами кода
- Код оформляй в блоках```"""

# Хранилище историй
user_histories = {}

# ============ ОБРАБОТЧИКИ ============

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_histories[message.from_user.id] = []
    
    await message.answer(
        "👋 Привет! Я бот техподдержки **BotHost.ru**\n\n"
        "Помогу тебе с:\n"
        "• Ошибками в коде\n"
        "• Вопросами по Python/aiogram\n"
        "• Проблемами с хостингом ботов\n\n"
        "📝 Просто напиши свой вопрос!\n\n"
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
        # Формируем промпт с историей
        user_histories[user_id].append(f"Пользователь: {message.text}")
        
        full_prompt = SYSTEM_PROMPT + "\n\nИстория диалога:\n" + "\n".join(user_histories[user_id][-10:]) + "\n\nАссистент:"
        
        response = model.generate_content(full_prompt)
        answer = response.text
        
        user_histories[user_id].append(f"Ассистент: {answer}")
        
        # Лимит Telegram
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await message.answer(answer[i:i+4000])
        else:
            await message.answer(answer)
            
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer(f"❌ Ошибка: {e}\n\nПопробуй /clear")

# ============ ЗАПУСК ============
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
