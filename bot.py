import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
import google.generativeai as genai

# ============ НАСТРОЙКИ ============
TELEGRAM_TOKEN = "8373375366:AAEJyCescKsmltC9xMLtkKg9ocPNiM503X4"
GEMINI_API_KEY = "gen-lang-client-0534723568..."  # Полный ключ

# ============ ИНИЦИАЛИЗАЦИЯ ============
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

genai.configure(api_key=GEMINI_API_KEY)

# Системный промпт для техподдержки
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
- Если не знаешь ответ — честно скажи
- Код оформляй в блоках ```

Если вопрос не связан с программированием/хостингом — вежливо направь к теме."""

model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# Хранилище чатов (память для каждого пользователя)
user_chats = {}

# ============ ОБРАБОТЧИКИ ============

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_chats[message.from_user.id] = model.start_chat(history=[])
    
    await message.answer(
        "👋 Привет! Я бот техподдержки **BotHost.ru**\n\n"
        "Помогу тебе с:\n"
        "• Ошибками в коде\n"
        "• Вопросами по Python/aiogram\n"
        "• Проблемами с хостингом ботов\n\n"
        "📝 Просто напиши свой вопрос или скинь код с ошибкой!\n\n"
        "Команды:\n"
        "/clear — очистить историю диалога",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_chats[message.from_user.id] = model.start_chat(history=[])
    await message.answer("🗑 История очищена. Начнём сначала!")

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # Создаём чат если его нет
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
    
    # Показываем что бот печатает
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Отправляем запрос к Gemini
        response = user_chats[user_id].send_message(message.text)
        answer = response.text
        
        # Telegram лимит 4096 символов
        if len(answer) > 4000:
            # Разбиваем на части
            for i in range(0, len(answer), 4000):
                await message.answer(answer[i:i+4000])
        else:
            await message.answer(answer)
            
    except Exception as e:
        logging.error(f"Ошибка Gemini: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Попробуй ещё раз или напиши /clear"
        )

# ============ ЗАПУСК ============

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
