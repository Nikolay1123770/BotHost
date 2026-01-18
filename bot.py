import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from groq import Groq

# ============ НАСТРОЙКИ ============
TELEGRAM_TOKEN = "7860018044:AAGRy4G3gGFoPhW8lRCQVHuJtb6Y_W7AyW4"  # Твой токен (удали из публичного кода!)
GROQ_API_KEY = "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"  # Получи бесплатно!

# ============ ИНИЦИАЛИЗАЦИЯ ============
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — бот технической поддержки BotHost.ru.

Помогаешь с:
- Ошибками в коде Python
- Telegram ботами (aiogram, telebot)
- Деплоем на BotHost
- Любыми вопросами по программированию

Всегда отвечай на русском языке.
Код оформляй в блоках ```python или ```"""

user_chats = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_chats[message.from_user.id] = []
    
    await message.answer(
        "👋 **Привет! Я техподдержка BotHost.ru**\n\n"
        "Помогу тебе с:\n"
        "🔹 Ошибками в коде\n"
        "🔹 Telegram ботами\n" 
        "🔹 Деплоем на BotHost\n"
        "🔹 Python и другими языками\n\n"
        "📝 **Просто опиши проблему или скинь код!**\n\n"
        "Команды:\n"
        "/clear — новый диалог\n"
        "/help — подробная помощь",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 **Как пользоваться:**\n\n"
        "1️⃣ Опиши проблему подробно\n"
        "2️⃣ Если есть ошибка — скинь её текст\n"
        "3️⃣ Если проблема с кодом — отправь код\n\n"
        "**Примеры вопросов:**\n"
        "• Как сделать inline кнопки в aiogram?\n"
        "• Ошибка: AttributeError в строке 15\n"
        "• Как подключить базу данных к боту?\n\n"
        "💡 Бот помнит контекст диалога!",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_chats[message.from_user.id] = []
    await message.answer("🔄 История очищена! Начинаем новый диалог.")

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # Создаём историю если нет
    if user_id not in user_chats:
        user_chats[user_id] = []
    
    # Показываем typing
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Добавляем в историю
        user_chats[user_id].append({
            "role": "user", 
            "content": message.text
        })
        
        # Ограничиваем историю последними 10 сообщениями
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(user_chats[user_id][-10:])
        
        # Запрос к Groq
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Быстрая модель
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        
        # Сохраняем ответ
        user_chats[user_id].append({
            "role": "assistant",
            "content": answer
        })
        
        # Отправляем (разбиваем если длинный)
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await message.answer(answer[i:i+4000])
        else:
            await message.answer(answer)
            
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        await message.answer(
            "❌ **Произошла ошибка**\n\n"
            f"```{str(e)}```\n\n"
            "Попробуй:\n"
            "• Написать вопрос по-другому\n"
            "• Использовать /clear\n"
            "• Подождать минуту",
            parse_mode=ParseMode.MARKDOWN
        )

# Обработка фото с кодом
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer(
        "📸 Я пока не умею читать изображения.\n\n"
        "**Скопируй код текстом** и отправь мне!",
        parse_mode=ParseMode.MARKDOWN
    )

async def main():
    print("=" * 40)
    print("✅ БОТ ТЕХПОДДЕРЖКИ ЗАПУЩЕН!")
    print("=" * 40)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
