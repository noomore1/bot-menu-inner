import logging
import asyncio
import random
import nest_asyncio

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Для корректной работы в Jupyter/nested loops
nest_asyncio.apply()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния беседы
(
    STATE_START,
    STATE_ACTION,
    STATE_BREAKFAST_TYPE,
    STATE_BREAKFAST,
    STATE_LUNCH_TYPE,
    STATE_LUNCH_CHOICE,
    STATE_LUNCH_CONFIRM,
    STATE_DINNER_TYPE,
    STATE_DINNER_CHOICE,
    STATE_DINNER_CONFIRM
) = range(10)

# Меню
COFFEE_MENU = [
    "Фильтр кофе ☕️", "Эспрессо 🔋", "Двойной эспрессо ⚡️", "Капучино 🐮",
    "Бамбл кофе с фрешом 🍊", "Бамбл кофе с вишневым соком 🍒",
    "Чай зеленый в асс 💚", "Чай черный в асс 🖤", "Ромашка 🌼"
]
SWEET_BREAKFASTS = [
    "Сырники",
    "Овсянка с ягодами и сезонными фруктами",
    "Овсянка с камамбером, смородиной и розмарином",
    "Блинчики",
    "Творог с сезонными фруктами и орешками",
    "Творог с пармезаном и грушей",
    "Завтрак из \"Люди любят\"",
    "Завтрак из \"Буше\"",
    "Чиа пудинг"
]
SAVORY_BREAKFASTS = [
    "Рулетики с творогом",
    "Шакшука",
    "Авокадо тост",
    "Яйца по-турецки",
    "Горячие бутерброды + яйца",
    "Бутерброды с тунцом",
    "Брускетты с камамбером и брускетта с огурчиками",
    "Омлет с ветчиной и сыром",
    "Бутерброды с хумусом и сыром халуми",
    "Брускетты с грушей и ветчиной",
    "Брускетты с томатами",
    "Круассаны с беконом и яйцом",
    "Круассаны с песто, мортаделлой и моцареллой",
    "Бейглы с ветчиной, творожным сыром и яйцом Бенедикт"
]
LIGHT_MEALS = [
    "Цезарь",
    "Паста с креветками, чесноком, тимьяном и розмарином",
    "Куриные роллы",
    "Куриный суп",
    "Салат с курицей и ананасом",
    "Салат с киноа и креветками (апельсиновый соус)",
    "Салат с курицей, яблоками и шпинатом",
    "Салат с морковкой и сыром"
]
HEARTY_MEALS = [
    "Запеченные куриные бедра в сметане с макаронами",
    "Паста Карбонара",
    "Паста Болоньезе",
    "Куриные котлетки с сыром",
    "Белая рыба под соусом из мазика и сыра + печеные овощи",
    "Красная рыба с терияки",
    "Красная рыба в сливках",
    "Курочка Гордона Рамзи",
    "Пельмени",
    "Жареный рис по-азиатски",
    "Драники",
    "Каннеллони с соусом из рикотты и шпината на овощной подушке",
    "Фрикадельки с пюре",
    "Жульен",
    "Отбивные с грибами",
    "Голубцы из Пекинской капусты",
    "Чкмерули",
    "Чахохбили",
    "Паста с песто и грибами",
    "Макароны с сосисками",
    "Ризотто",
    "Птитим",
    "Мясо в горшочках",
    "Лазанья",
    "Гречка с грибами и курицей",
    "Мусака"
]

BREAKFAST_INGREDIENTS = {
    "Сырники": ["творог", "яйца", "сметана"],
    "Рулетики с творогом": ["творог", "лаваш", "сыр", "сметана", "укроп"],
    "Шакшука": ["помидоры", "томатная паста", "чеснок", "перец", "кинза", "творожный сыр", "яйца", "чиабатта"],
    "Авокадо тост": ["хлеб", "авокадо", "яйца"],
    "Яйца по-турецки": ["яйца", "греческий йогурт", "чеснок", "кинза", "хлеб"],
    "Горячие бутерброды + яйца": ["булка", "сыр", "яйца", "ветчина"],
    "Бутерброды с тунцом": ["тунец в банке", "мазик", "сельдерей", "лук красный", "соленые огурцы", "горчица зернистая"],
    "Овсянка с ягодами и сезонными фруктами": ["овсянка", "молоко", "фрукты", "мед"],
    "Овсянка с камамбером, смородиной и розмарином": ["овсянка", "камамбер", "молоко", "смородина или вишня", "розмарин"],
    "Брускетты с камамбером и брускетта с огурчиками": ["чиабатта", "хлеб", "творожный сыр", "огурцы свежие", "камамбер", "яйца", "молоко"],
    "Омлет с ветчиной и сыром": ["яйца", "ветчина", "сыр"],
    "Бутерброды с хумусом и сыром халуми": ["хлеб", "хумус", "яйца", "халуми"],
    "Блинчики": ["молоко", "яйца"],
    "Брускетты с грушей и ветчиной": ["чиабатта", "груша", "ветчина", "горчица", "лимон", "сыр фета"],
    "Брускетты с томатами": ["чиабатта", "томаты", "пармезан"],
    "Творог с сезонными фруктами и орешками": ["творог зернистый", "фрукты", "орехи любые", "сметана"],
    "Творог с пармезаном и грушей": ["творог зернистый", "пармезан", "сметана", "груша"],
    "Завтрак из \"Люди любят\"": ["Готовь бабки"],
    "Завтрак из \"Буше\"": ["Готовь бабки"],
    "Круассаны с беконом и яйцом": ["круассаны", "бекон", "сыр", "яйца"],
    "Круассаны с песто, мортаделлой и моцареллой": ["круассаны", "песто", "мортаделла", "моцарелла"],
    "Чиа пудинг": ["семена чиа", "молоко", "ягоды"],
    "Бейглы с ветчиной, творожным сыром и яйцом Бенедикт": ["чиабатта", "ветчина", "творожный сыр", "яйца"]
}

# Клавиатуры
def kb_main():
    return ReplyKeyboardMarkup(
        ["🚀 Запустить бота", "Меню на день 🍽", "Кофейня ☕️"],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_action():
    return ReplyKeyboardMarkup(
        [["Составлю меню сам", "Сгенерировать всё меню"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_breakfast_type():
    return ReplyKeyboardMarkup(
        [["Сладкий завтрак", "Солёный завтрак"], ["Случайный завтрак"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_lunch_type():
    return ReplyKeyboardMarkup(
        [["Лёгкий обед", "Сытный обед"], ["Случайный обед"], ["У меня есть обед"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_dinner_type():
    return ReplyKeyboardMarkup(
        [["Лёгкий ужин", "Сытный ужин"], ["Случайный ужин"], ["У меня есть ужин"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_confirm():
    return ReplyKeyboardMarkup(
        [["Да", "Нет"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_breakfast_type():
    return ReplyKeyboardMarkup(
        [["Сладкий завтрак", "Солёный завтрак"], ["Случайный завтрак"], ["🔙 Назад"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_lunch_type():
    return ReplyKeyboardMarkup(
        [["Лёгкий обед", "Сытный обед"], ["Случайный обед"], ["У меня есть обед"], ["🔙 Назад"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def kb_dinner_type():
    return ReplyKeyboardMarkup(
        [["Лёгкий ужин", "Сытный ужин"], ["Случайный ужин"], ["У меня есть ужин"], ["🔙 Назад"]],
        resize_keyboard=True, one_time_keyboard=True
    )

# (продолжение после определения клавиатур)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Что выберешь сегодня?",
        reply_markup=kb_main()
    )
    return STATE_START

async def lunch_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Да":
        context.user_data['lunch'] = "Вот это повезло! Обед уже есть!"
    else:
        context.user_data['lunch'] = random.choice(LIGHT_MEALS + HEARTY_MEALS)
    await update.message.reply_text("У тебя уже есть ужин?", reply_markup=kb_confirm())
    return STATE_DINNER_CONFIRM

async def dinner_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lunch = context.user_data.get("lunch")
    all_meals = LIGHT_MEALS + HEARTY_MEALS
    if text == "Да":
        context.user_data['dinner'] = "Вот это повезло! Ужин уже есть!"
    else:
        remaining = [m for m in all_meals if m != lunch]
        context.user_data['dinner'] = random.choice(remaining)
    return await show_summary(update, context)

# Обработка главного меню
async def action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🚀 Запустить бота":
        return await start(update, context)
    if text == "Кофейня ☕️":
        await update.message.reply_text(
            "Выбери напиток:",
            reply_markup=ReplyKeyboardMarkup([[c] for c in COFFEE_MENU], resize_keyboard=True)
        )
        return STATE_ACTION
    if text in COFFEE_MENU:
        await update.message.reply_text("Ваш заказ принят, ожидайте ❤️", reply_markup=kb_main())
        user = update.message.from_user
        order = (
            f"☕️ Новый заказ:\n"
            f"👤 {user.full_name} (@{user.username})\n"
            f"📌 Напиток: {text}"
        )
        await context.bot.send_message(chat_id=674860394, text=order)
        return STATE_START
    if text == "Меню на день 🍽":
        await update.message.reply_text("Сейчас составим меню на день:", reply_markup=kb_action())
        return STATE_ACTION
    if text == "Сгенерировать всё меню":
        context.user_data['breakfast'] = random.choice(SWEET_BREAKFASTS + SAVORY_BREAKFASTS)
        await update.message.reply_text("У тебя уже есть обед?", reply_markup=kb_confirm())
        return STATE_LUNCH_CONFIRM
    if text == "Составлю меню сам":
        await update.message.reply_text("Выбери завтрак:", reply_markup=kb_breakfast_type())
        return STATE_BREAKFAST_TYPE
    return STATE_START

# Завтрак
async def breakfast_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        await update.message.reply_text("Что выберешь сегодня?", reply_markup=kb_main())
        return STATE_START
    if text == "Сладкий завтрак":
        options = SWEET_BREAKFASTS
    elif text == "Солёный завтрак":
        options = SAVORY_BREAKFASTS
    else:
        context.user_data['breakfast'] = random.choice(SWEET_BREAKFASTS + SAVORY_BREAKFASTS)
        await update.message.reply_text("Выбери тип обеда:", reply_markup=kb_lunch_type())
        return STATE_LUNCH_TYPE
    buttons = [[b] for b in options] + [["🔙 Назад"]]
    await update.message.reply_text(
    "Выбери завтрак:",
    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return STATE_BREAKFAST

async def breakfast_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await update.message.reply_text("Выбери тип завтрака:", reply_markup=kb_breakfast_type())
        return STATE_BREAKFAST_TYPE
    context.user_data['breakfast'] = update.message.text
    await update.message.reply_text("Выбери тип обеда:", reply_markup=kb_lunch_type())
    return STATE_LUNCH_TYPE

# Обед
async def lunch_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        await update.message.reply_text("Выбери завтрак:", reply_markup=kb_breakfast_type())
        return STATE_BREAKFAST_TYPE
    if text == "Лёгкий обед":
        options = LIGHT_MEALS
    elif text == "Сытный обед":
        options = HEARTY_MEALS
    elif text == "У меня есть обед":
        context.user_data['lunch'] = "Вот это повезло! Обед уже есть!"
        await update.message.reply_text("Выбери тип ужина:", reply_markup=kb_dinner_type())
        return STATE_DINNER_TYPE
    else:
        context.user_data['lunch'] = random.choice(LIGHT_MEALS + HEARTY_MEALS)
        await update.message.reply_text("Выбери тип ужина:", reply_markup=kb_dinner_type())
        return STATE_DINNER_TYPE
    buttons = [[m] for m in options] + [["🔙 Назад"]]
    await update.message.reply_text(
    "Выбери обед:",
    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return STATE_LUNCH_CHOICE

async def lunch_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await update.message.reply_text("Выбери тип обеда:", reply_markup=kb_lunch_type())
        return STATE_LUNCH_TYPE
    context.user_data['lunch'] = update.message.text
    await update.message.reply_text("Выбери тип ужина:", reply_markup=kb_dinner_type())
    return STATE_DINNER_TYPE

# Ужин
async def dinner_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        await update.message.reply_text("Выбери тип обеда:", reply_markup=kb_lunch_type())
        return STATE_LUNCH_TYPE
    if text == "Лёгкий ужин":
        options = LIGHT_MEALS
    elif text == "Сытный ужин":
        options = HEARTY_MEALS
    elif text == "У меня есть ужин":
        context.user_data['dinner'] = "Вот это повезло! Ужин уже есть!"
        return await show_summary(update, context)
    else:
        context.user_data['dinner'] = random.choice(LIGHT_MEALS + HEARTY_MEALS)
        return await show_summary(update, context)
    buttons = [[m] for m in options] + [["🔙 Назад"]]
    await update.message.reply_text(
    "Выбери ужин:",
    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return STATE_DINNER_CHOICE

async def dinner_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await update.message.reply_text("Выбери тип ужина:", reply_markup=kb_dinner_type())
        return STATE_DINNER_TYPE
    context.user_data['dinner'] = update.message.text
    return await show_summary(update, context)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🍽 Меню на день:\n"
        f"🥣 Завтрак: {context.user_data['breakfast']}\n"
        f"🍛 Обед: {context.user_data['lunch']}\n"
        f"🌙 Ужин: {context.user_data['dinner']}",
        reply_markup=kb_main()
    )

    await show_shopping_list(update, context)
    return STATE_START

async def show_shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breakfast = context.user_data.get("breakfast")
    ingredients = BREAKFAST_INGREDIENTS.get(breakfast, [])

    if ingredients:
        ingredients_text = "\n".join(f"• {item}" for item in ingredients)
        await update.message.reply_text(
            f"🛒 Вот список продуктов на завтрак:\n{ingredients_text}"
        )
    else:
        await update.message.reply_text(
            "🛒 Для этого завтрака список ингредиентов пока не указан."
        )

from telegram.ext import ApplicationBuilder
from aiohttp import web

BOT_TOKEN = "8122015182:AAGcVNiLbj6ZK1uNwcfIh3NRZ-w61zoVQHA"
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://bot-menu-inner.onrender.com{WEBHOOK_PATH}"

# Healthcheck для Render
async def healthcheck(request):
    return web.Response(text="OK")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем ConversationHandler (если у тебя уже создан — просто вставь его сюда)
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🚀 Запустить бота$"), start)
        ],
        states={
            STATE_START: [MessageHandler(filters.TEXT, action_handler)],
            STATE_ACTION: [MessageHandler(filters.TEXT, action_handler)],
            STATE_BREAKFAST_TYPE: [MessageHandler(filters.TEXT, breakfast_type)],
            STATE_BREAKFAST: [MessageHandler(filters.TEXT, breakfast_chosen)],
            STATE_LUNCH_TYPE: [MessageHandler(filters.TEXT, lunch_type)],
            STATE_LUNCH_CHOICE: [MessageHandler(filters.TEXT, lunch_chosen)],
            STATE_DINNER_TYPE: [MessageHandler(filters.TEXT, dinner_type)],
            STATE_DINNER_CHOICE: [MessageHandler(filters.TEXT, dinner_chosen)],
            STATE_LUNCH_CONFIRM: [MessageHandler(filters.TEXT, lunch_confirm)],
            STATE_DINNER_CONFIRM: [MessageHandler(filters.TEXT, dinner_confirm)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(conv)

    # 👇 добавим эндпоинт для Render
    app.web_app.router.add_get("/", healthcheck)

    print("✅ Bot is running via Webhook...")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())