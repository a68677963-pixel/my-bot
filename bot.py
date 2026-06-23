import os
import logging
import httpx
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Крошечный сервер для обмана Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        return  # Отключаем лишний спам в консоль

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

PLACEMENT_TEST = [
    {"question": "Переведи: 'Hello, my name is John'"},
    {"question": "Заполни пропуск: I ___ a student. (am/is/are)"},
    {"question": "Переведи: 'She went to the shop yesterday'"},
    {"question": "Исправь ошибку: 'He don't like coffee'"},
    {"question": "Переведи: 'If I had more time, I would travel the world'"},
]

LESSONS = {
    "A1": [
        {"title": "🌍 Приветствия", "text": "━━━━━━━━━━━━━━━━━━━━\n👋 *УРОК 1: Приветствия*\n━━━━━━━━━━━━━━━━━━━━\n\n🗣 *Основные фразы:*\n├ Hello → Привет\n├ Good morning → Доброе утро\n├ Good afternoon → Добрый день\n├ Good evening → Добрый вечер\n├ Good night → Спокойной ночи\n└ Goodbye → До свидания\n\n👤 *Знакомство:*\n├ My name is... → Меня зовут...\n├ Nice to meet you → Приятно познакомиться\n└ How are you? → Как дела?", "test": "Как переводится 'Good morning'?", "answer": "доброе утро"},
        {"title": "🔢 Числа 1-20", "text": "━━━━━━━━━━━━━━━━━━━━\n🔢 *УРОК 2: Числа 1-20*\n━━━━━━━━━━━━━━━━━━━━\n\n1️⃣ One   2️⃣ Two   3️⃣ Three\n4️⃣ Four  5️⃣ Five  6️⃣ Six\n7️⃣ Seven 8️⃣ Eight 9️⃣ Nine\n🔟 Ten\n\n11 → Eleven    12 → Twelve\n13 → Thirteen  14 → Fourteen\n15 → Fifteen   16 → Sixteen\n17 → Seventeen 18 → Eighteen\n19 → Nineteen  20 → Twenty", "test": "Как пишется число 15 по-английски?", "answer": "fifteen"},
        {"title": "🎨 Цвета", "text": "━━━━━━━━━━━━━━━━━━━━\n🎨 *УРОК 3: Цвета*\n━━━━━━━━━━━━━━━━━━━━\n\n🔴 Red → Красный\n🔵 Blue → Синий\n🟢 Green → Зелёный\n🟡 Yellow → Жёлтый\n⚫ Black → Чёрный\n⚪ White → Белый\n🟠 Orange → Оранжевый\n🟣 Purple → Фиолетовый\n🟤 Brown → Коричневый\n🩷 Pink → Розовый", "test": "Как переводится 'Purple'?", "answer": "фиолетовый"},
        {"title": "👨‍👩‍👧 Семья", "text": "━━━━━━━━━━━━━━━━━━━━\n👨‍👩‍👧 *УРОК 4: Семья*\n━━━━━━━━━━━━━━━━━━━━\n\n👩 Mother → Мама\n👨 Father → Папа\n👧 Sister → Сестра\n👦 Brother → Брат\n👵 Grandmother → Бабушка\n👴 Grandfather → Дедушка\n👶 Baby → Малыш\n🧑 Child → Ребёнок\n💑 Wife → Жена\n💑 Husband → Муж", "test": "Как переводится 'Grandmother'?", "answer": "бабушка"},
        {"title": "🍎 Еда и напитки", "text": "━━━━━━━━━━━━━━━━━━━━\n🍎 *УРОК 5: Еда и напитки*\n━━━━━━━━━━━━━━━━━━━━\n\n🍎 Apple → Яблоко\n🍞 Bread → Хлеб\n💧 Water → Вода\n🥛 Milk → Молоко\n🍚 Rice → Рис\n🥩 Meat → Мясо\n🥚 Egg → Яйцо\n☕ Tea → Чай\n☕ Coffee → Кофе\n🧃 Juice → Сок", "test": "Как переводится 'Juice'?", "answer": "сок"},
    ],
    "A2": [
        {"title": "📝 Present Simple", "text": "━━━━━━━━━━━━━━━━━━━━\n📝 *УРОК 1: Present Simple*\n━━━━━━━━━━━━━━━━━━━━\n\n📌 *Формула:*\nI/You/We/They + V1\nHe/She/It + V1+s\n\n✅ *Примеры:*\n├ I work → Я работаю\n├ She works → Она работает\n├ They play → Они играют\n└ He studies → Он учится\n\n❌ *Отрицание:*\n├ I don't work\n└ She doesn't work", "test": "Как будет 'Она не работает'?", "answer": "she doesn't work"},
        {"title": "🏠 Дом и комнаты", "text": "━━━━━━━━━━━━━━━━━━━━\n🏠 *УРОК 2: Дом*\n━━━━━━━━━━━━━━━━━━━━\n\n🏠 House → Дом\n🛋 Living room → Гостиная\n🍳 Kitchen → Кухня\n🛏 Bedroom → Спальня\n🚿 Bathroom → Ванная\n🚪 Door → Дверь\n🪟 Window → Окно\n🪑 Chair → Стул\n🛋 Sofa → Диван\n📺 TV → Телевизор", "test": "Как переводится 'Bedroom'?", "answer": "спальня"},
        {"title": "🌤 Погода", "text": "━━━━━━━━━━━━━━━━━━━━\n🌤 *УРОК 3: Погода*\n━━━━━━━━━━━━━━━━━━━━\n\n☀️ Sunny → Солнечно\n🌧 Rainy → Дождливо\n❄️ Snowy → Снежно\n💨 Windy → Ветрено\n☁️ Cloudy → Облачно\n🌡 Hot → Жарко\n🥶 Cold → Холодно\n\n💬 *Фразы о погоде:*\n├ What's the weather like? → Какая погода?\n└ It's raining → Идёт дождь", "test": "Как переводится 'It's raining'?", "answer": "идёт дождь"},
        {"title": "⏰ Время", "text": "━━━━━━━━━━━━━━━━━━━━\n⏰ *УРОК 4: Время*\n━━━━━━━━━━━━━━━━━━━━\n\n🕐 What time is it? → Который час?\n├ It's 3 o'clock → 3 часа\n├ Half past 3 → Половина четвёртого\n├ Quarter to 4 → Без четверти 4\n\n📅 *Дни недели:*\nMonday, Tuesday, Wednesday\nThursday, Friday, Saturday, Sunday", "test": "Как переводится 'What time is it?'", "answer": "который час"},
    ],
    "B1": [
        {"title": "⏰ Past Simple", "text": "━━━━━━━━━━━━━━━━━━━━\n⏰ *УРОК 1: Past Simple*\n━━━━━━━━━━━━━━━━━━━━\n\n📌 *Формула:* Subject + V2\n\n✅ *Правильные глаголы:*\n├ work → worked\n├ play → played\n└ study → studied\n\n⚡ *Неправильные глаголы:*\n├ go → went\n├ eat → ate\n├ see → saw\n├ buy → bought\n└ come → came", "test": "Как будет 'Они купили машину'?", "answer": "they bought a car"},
        {"title": "✨ Present Perfect", "text": "━━━━━━━━━━━━━━━━━━━━\n✨ *УРОК 2: Present Perfect*\n━━━━━━━━━━━━━━━━━━━━\n\n📌 *Формула:* have/has + V3\n\n✅ *Примеры:*\n├ I have seen → Я видел\n├ She has eaten → Она поела\n├ They have gone → Они ушли\n└ He has bought → Он купил\n\n🔑 *Слова-маркеры:*\nalready, just, ever, never, yet", "test": "Переведи: 'I have never been to London'", "answer": "я никогда не был в лондоне"},
        {"title": "🔮 Future Simple", "text": "━━━━━━━━━━━━━━━━━━━━\n🔮 *УРОК 3: Future Simple*\n━━━━━━━━━━━━━━━━━━━━\n\n📌 *Формула:* will + V1\n\n✅ *Примеры:*\n├ I will go → Я пойду\n├ She will call → Она позвонит\n├ They will come → Они придут\n\n❌ *Отрицание:* won't\n├ I won't go → Я не пойду\n└ He won't come → Он не придёт", "test": "Как будет 'Она не позвонит'?", "answer": "she won't call"},
    ],
    "B2": [
        {"title": "🔀 Conditionals", "text": "━━━━━━━━━━━━━━━━━━━━\n🔀 *УРОК 1: Условные предложения*\n━━━━━━━━━━━━━━━━━━━━\n\n*1️⃣ тип (реальное):*\nIf + Present, will + V1\n├ If it rains, I will stay home\n\n*2️⃣ тип (нереальное):*\nIf + Past, would + V1\n├ If I had money, I would buy a car\n\n*3️⃣ тип (прошлое):*\nIf + Past Perfect, would have + V3\n└ If I had studied, I would have passed", "test": "Какой тип: 'If I were rich, I would travel'?", "answer": "второй"},
        {"title": "🔄 Passive Voice", "text": "━━━━━━━━━━━━━━━━━━━━\n🔄 *УРОК 2: Пассивный залог*\n━━━━━━━━━━━━━━━━━━━━\n\n📌 *Формула:* be + V3\n\n✅ *Примеры:*\n├ The book was written → Книга была написана\n├ English is spoken here → Здесь говорят по-английски\n├ The car is being repaired → Машину чинят\n└ The letter has been sent → Письмо было отправлено", "test": "Переведи: 'The house was built in 1990'", "answer": "дом был построен в 1990"},
    ],
}

VOCABULARY = [
    {"word": "Ambitious", "translate": "Амбициозный", "example": "She is very ambitious"},
    {"word": "Brilliant", "translate": "Блестящий", "example": "A brilliant idea"},
    {"word": "Curious", "translate": "Любопытный", "example": "Children are naturally curious"},
    {"word": "Determined", "translate": "Целеустремлённый", "example": "He is determined to succeed"},
    {"word": "Enthusiastic", "translate": "Восторженный", "example": "She was enthusiastic about the project"},
    {"word": "Flexible", "translate": "Гибкий", "example": "You need to be flexible"},
    {"word": "Generous", "translate": "Щедрый", "example": "He is very generous"},
    {"word": "Honest", "translate": "Честный", "example": "Always be honest"},
    {"word": "Imaginative", "translate": "Творческий", "example": "An imaginative solution"},
    {"word": "Joyful", "translate": "Радостный", "example": "A joyful occasion"},
    {"word": "Knowledgeable", "translate": "Знающий", "example": "She is very knowledgeable"},
    {"word": "Loyal", "translate": "Верный", "example": "A loyal friend"},
    {"word": "Motivated", "translate": "Мотивированный", "example": "Stay motivated!"},
    {"word": "Optimistic", "translate": "Оптимистичный", "example": "Try to be optimistic"},
    {"word": "Patient", "translate": "Терпеливый", "example": "Be patient with yourself"},
]

PHRASES = [
    {"phrase": "Break a leg!", "meaning": "Удачи! (буквально: сломай ногу)", "context": "Говорят перед выступлением"},
    {"phrase": "It's raining cats and dogs", "meaning": "Льёт как из ведра", "context": "О сильном дожде"},
    {"phrase": "Hit the nail on the head", "meaning": "Попасть в точку", "context": "Когда кто-то точно описал ситуацию"},
    {"phrase": "Under the weather", "meaning": "Чувствовать себя плохо", "context": "Когда болешь"},
    {"phrase": "Bite the bullet", "meaning": "Стиснуть зубы и сделать", "context": "Делать что-то неприятное"},
    {"phrase": "Cost an arm and a leg", "meaning": "Стоить очень дорого", "context": "О дорогих вещах"},
    {"phrase": "Once in a blue moon", "meaning": "Крайне редко", "context": "О редких событиях"},
    {"phrase": "Spill the beans", "meaning": "Раскрыть секрет", "context": "Когда кто-то выдал тайну"},
    {"phrase": "The ball is in your court", "meaning": "Теперь твой ход", "context": "Когда решение за другим человеком"},
    {"phrase": "Piece of cake", "meaning": "Проще простого", "context": "О лёгком задании"},
]

user_data = {}


async def ask_ai(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Ты — опытный учитель английского языка. Отвечай по-русски, коротко и понятно. Используй эмодзи."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, headers=headers, timeout=30)
        return r.json()["choices"][0]["message"]["content"]


async def determine_level(answers: list) -> str:
    prompt = f"""Пользователь прошёл тест. Его ответы:
{chr(10).join([f"Вопрос: {PLACEMENT_TEST[i]['question']}\nОтвет: {answers[i]}" for i in range(len(answers))])}
Определи уровень: A1, A2, B1 или B2. Ответь ТОЛЬКО одним вариантом."""
    result = await ask_ai(prompt)
    for level in ["B2", "B1", "A2", "A1"]:
        if level in result:
            return level
    return "A1"


def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📚 Уроки"), KeyboardButton("📖 Словарь")],
        [KeyboardButton("💬 Разговорные фразы"), KeyboardButton("🤖 AI учитель")],
        [KeyboardButton("📊 Прогресс"), KeyboardButton("🔄 Новый тест")],
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "stage": "testing",
        "test_q": 0,
        "answers": [],
        "level": None,
        "lesson": 0,
        "score": 0,
        "asking_ai": False,
        "vocab_mode": False,
        "phrase_mode": False,
        "waiting_answer": False,
        "vocab_word": None,
        "processing": False,
    }
    await update.message.reply_text(
        "🇬🇧 *English AI Tutor*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 Привет! Я твой личный учитель английского!\n\n"
        "🎯 Сначала определим твой уровень.\n"
        f"Ответь на {len(PLACEMENT_TEST)} вопросов честно!\n\n"
        f"❓ *Вопрос 1/{len(PLACEMENT_TEST)}:*\n_{PLACEMENT_TEST[0]['question']}_",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await start(update, context)
        return

    data = user_data[user_id]

    # 1. КНОПКИ ГЛАВНОГО МЕНЮ
    if text == "🔄 Новый тест":
        await start(update, context)
        return

    if text == "📊 Прогресс":
        level = data.get("level") or "Определяется..."
        await update.message.reply_text(
            f"📊 *Твой прогресс*\n━━━━━━━━━━━━━━━━\n\n"
            f"🎯 Уровень: *{level}*\n"
            f"✅ Уроков пройдено: *{data.get('lesson', 0)}*\n"
            f"⭐ Правильных ответов: *{data.get('score', 0)}*\n\n"
            f"💪 Продолжай учиться!",
            parse_mode="Markdown", reply_markup=main_menu()
        )
        return

    if text == "🤖 AI учитель":
        if data["stage"] == "testing":
            await update.message.reply_text("⚠️ Сначала заверши вступительный тест! Ответь на текущий вопрос.")
            return
        data["asking_ai"] = True
        data["vocab_mode"] = False
        data["phrase_mode"] = False
        await update.message.reply_text(
            "🤖 *AI Учитель готов помочь!*\n\n"
            "Задай любой вопрос по английскому:\n"
            "• Объясни Present Perfect\n"
            "• Как использовать артикли?\n"
            "• В чём разница между make и do?",
            parse_mode="Markdown"
        )
        return

    if text == "📖 Словарь":
        if data["stage"] == "testing":
            await update.message.reply_text("⚠️ Сначала заверши вступительный тест! Ответь на текущий вопрос.")
            return
        data["vocab_mode"] = True
        data["asking_ai"] = False
        data["phrase_mode"] = False
        word = random.choice(VOCABULARY)
        data["vocab_word"] = word
        await update.message.reply_text(
            f"📖 *СЛОВАРНЫЙ ТРЕНАЖЁР*\n━━━━━━━━━━━━━━━━\n\n"
            f"🔤 Слово: *{word['word']}*\n\n"
            f"📝 Пример: _{word['example']}_\n\n"
            f"❓ Переведи это слово на русский:",
            parse_mode="Markdown"
        )
        return

    if text == "💬 Разговорные фразы":
        if data["stage"] == "testing":
            await update.message.reply_text("⚠️ Сначала заверши вступительный тест! Ответь на текущий вопрос.")
            return
        data["phrase_mode"] = True
        data["asking_ai"] = False
        data["vocab_mode"] = False
        phrase = random.choice(PHRASES)
        await update.message.reply_text(
            f"💬 *РАЗГОВОРНАЯ ФРАЗА*\n━━━━━━━━━━━━━━━━\n\n"
            f"🗣 *{phrase['phrase']}*\n\n"
            f"📌 Значение: {phrase['meaning']}\n\n"
            f"💡 Контекст: _{phrase['context']}_\n\n"
            f"Напиши *'ещё'* для новой фразы или задай вопрос!",
            parse_mode="Markdown", reply_markup=main_menu()
        )
        return

    if text == "📚 Уроки":
        if data["stage"] == "testing":
            await update.message.reply_text("⚠️ Сначала заверши вступительный тест! Ответь на текущий вопрос.")
            return
        data["asking_ai"] = False
        data["vocab_mode"] = False
        data["phrase_mode"] = False
        await send_lesson(update, data)
        return

    # 2. ВХОДНОЙ ТЕСТ — защита от двойных сообщений
    if data["stage"] == "testing":
        if data.get("processing"):
            return

        data["processing"] = True
        data["answers"].append(text)
        data["test_q"] += 1

        if data["test_q"] < len(PLACEMENT_TEST):
            next_q = PLACEMENT_TEST[data["test_q"]]
            data["processing"] = False
            await update.message.reply_text(
                f"✅ Ответ принят!\n\n"
                f"❓ *Вопрос {data['test_q'] + 1}/{len(PLACEMENT_TEST)}:*\n"
                f"_{next_q['question']}_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⏳ *Анализирую твои ответы...*", parse_mode="Markdown")
            await update.message.chat.send_action("typing")
            level = await determine_level(data["answers"])
            data["level"] = level
            data["stage"] = "lessons"
            data["lesson"] = 0
            data["processing"] = False

            level_emoji = {"A1": "🌱", "A2": "📈", "B1": "💪", "B2": "🔥"}
            level_desc = {
                "A1": "Начинающий — начнём с самого начала!",
                "A2": "Элементарный — хороший старт!",
                "B1": "Средний — отличный уровень!",
                "B2": "Выше среднего — ты молодец!"
            }

            await update.message.reply_text(
                f"🎯 *РЕЗУЛЬТАТ ТЕСТА*\n━━━━━━━━━━━━━━━━\n\n"
                f"{level_emoji[level]} Твой уровень: *{level}*\n"
                f"📝 {level_desc[level]}\n\n"
                f"🚀 Начинаем уроки!",
                parse_mode="Markdown", reply_markup=main_menu()
            )
            await send_lesson(update, data)
        return

    # 3. ПРОВЕРКА ОТВЕТА НА ТЕСТ ВНУТРИ УРОКА
    if data["stage"] == "lessons" and data.get("waiting_answer"):
        if data.get("processing"):
            return

        data["processing"] = True
        lessons = LESSONS.get(data["level"], LESSONS["A1"])
        lesson_idx = data["lesson"]

        if lesson_idx < len(lessons):
            correct = lessons[lesson_idx]["answer"]
            if text.lower().strip() == correct.lower():
                data["score"] += 1
                msg = "✅ *Правильно! Молодец!* 🎉\n\n"
            else:
                msg = f"❌ *Неправильно*\nПравильный ответ: *{correct}*\n\n"

            data["lesson"] += 1
            data["waiting_answer"] = False
            data["processing"] = False

            if data["lesson"] < len(lessons):
                await update.message.reply_text(msg + "▶️ *Следующий урок:*", parse_mode="Markdown")
                await send_lesson(update, data)
            else:
                await update.message.reply_text(
                    msg + f"🏆 *Уровень {data['level']} пройден!*\n\nВыбери что делать дальше в меню.",
                    parse_mode="Markdown", reply_markup=main_menu()
                )
        else:
            data["processing"] = False
        return

    # 4. РЕЖИМ AI УЧИТЕЛЯ
    if data.get("asking_ai"):
        await update.message.chat.send_action("typing")
        reply = await ask_ai(text)
        await update.message.reply_text(f"🤖 {reply}", reply_markup=main_menu())
        data["asking_ai"] = False
        return

    # 5. РЕЖИМ СЛОВАРНОГО ТРЕНАЖЁРА
    if data.get("vocab_mode"):
        word = data.get("vocab_word")
        if word and text.lower().strip() == word["translate"].lower():
            response = f"✅ *Правильно!* 🎉\n\n*{word['word']}* = {word['translate']}\n\n"
        else:
            response = f"❌ *Неправильно*\n\n*{word['word']}* = *{word['translate']}*\n\n"
        new_word = random.choice(VOCABULARY)
        data["vocab_word"] = new_word
        await update.message.reply_text(
            response +
            f"📖 *Следующее слово:*\n\n"
            f"🔤 *{new_word['word']}*\n"
            f"📝 _{new_word['example']}_\n\n"
            f"❓ Переведи:",
            parse_mode="Markdown"
        )
        return

    # 6. РЕЖИМ РАЗГОВОРНЫХ ФРАЗ
    if data.get("phrase_mode"):
        if text.lower() == "ещё":
            phrase = random.choice(PHRASES)
            await update.message.reply_text(
                f"💬 *РАЗГОВОРНАЯ ФРАЗА*\n━━━━━━━━━━━━━━━━\n\n"
                f"🗣 *{phrase['phrase']}*\n\n"
                f"📌 Значение: {phrase['meaning']}\n\n"
                f"💡 Контекст: _{phrase['context']}_\n\n"
                f"Напиши *'ещё'* для новой фразы!",
                parse_mode="Markdown", reply_markup=main_menu()
            )
        else:
            await update.message.chat.send_action("typing")
            reply = await ask_ai(f"Вопрос про английские разговорные фразы: {text}")
            await update.message.reply_text(f"🤖 {reply}", reply_markup=main_menu())
        return

    # 7. ПО УМОЛЧАНИЮ — свободный запрос к AI
    await update.message.chat.send_action("typing")
    reply = await ask_ai(text)
    await update.message.reply_text(f"🤖 {reply}", reply_markup=main_menu())


async def send_lesson(update: Update, data: dict):
    level = data.get("level", "A1")
    lessons = LESSONS.get(level, LESSONS["A1"])
    idx = data["lesson"]
    if idx >= len(lessons):
        await update.message.reply_text(
            "🏆 *Все уроки пройдены!*\n\nИспользуй словарь и фразы для практики!",
            parse_mode="Markdown", reply_markup=main_menu()
        )
        return
    lesson = lessons[idx]
    total = len(lessons)
    await update.message.reply_text(
        f"📚 Урок {idx + 1}/{total} • Уровень {level}\n"
        f"{lesson['text']}\n\n"
        f"❓ *Тест:* {lesson['test']}\n\n"
        f"✏️ Напиши свой ответ:",
        parse_mode="Markdown"
    )
    data["waiting_answer"] = True


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан!")
        
    # Запуск фонового веб-сервера для Render
    threading.Thread(target=run_health_check, daemon=True).start()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("English бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
