import random
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "TOKEN"

# -----------------------
# دیتابیس
# -----------------------
conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    money INTEGER,
    stage INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS yaro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    power INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    type TEXT
)
""")

conn.commit()

# -----------------------
# یاروها
# -----------------------
yaro_types = [
    ("معمولی", 50),
    ("جنگجو", 60),
    ("نینجا", 70),
    ("شوالیه", 80),
    ("تیرانداز", 65),
    ("سپردار", 75),
    ("پزشک", 60),
    ("مزدور", 55),
    ("غول", 90),
    ("جادوگر", 85),
    ("قاتل", 88),
    ("فرمانده", 95),
]

# -----------------------
# آیتم‌ها
# -----------------------
shop_items = [
    ("شمشیر آهنی", 100, "yaro"),
    ("زره سبک", 120, "yaro"),
    ("پرچم جنگ", 200, "camp"),
    ("چادر درمان", 150, "camp"),
]

# -----------------------
# منو
# -----------------------
def menu():
    return ReplyKeyboardMarkup([
        ["📊 وضعیت", "👥 یارو"],
        ["🔍 جستجوی یارو", "🛒 بازار"],
        ["🎒 آیتم", "⚔ مرحله"],
        ["❌ لغو"]
    ], resize_keyboard=True)

# -----------------------
# ساخت بازیکن
# -----------------------
def get_player(user_id, name=""):
    cursor.execute("SELECT * FROM players WHERE user_id=?", (user_id,))
    p = cursor.fetchone()

    if not p:
        cursor.execute("INSERT INTO players VALUES (?, ?, ?, ?)", (user_id, name, 300, 1))
        conn.commit()
        return (user_id, name, 300, 1)

    return p

# -----------------------
# /start
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_player(user_id, update.effective_user.first_name)

    await update.message.reply_text("🏕 به بازی پادگان خوش آمدی!", reply_markup=menu())

# -----------------------
# وضعیت
# -----------------------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = get_player(user_id)

    cursor.execute("SELECT COUNT(*) FROM yaro WHERE user_id=?", (user_id,))
    yaro_count = cursor.fetchone()[0]

    text = f"""
🏕 پادگان
💰 دلار: {p[2]}
📈 مرحله: {p[3]}
👥 یارو: {yaro_count}
"""
    await update.message.reply_text(text)

# -----------------------
# یاروها
# -----------------------
async def show_yaro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT name, power FROM yaro WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()

    text = "👥 یاروهای شما:\n\n"
    for i, y in enumerate(rows):
        text += f"{i+1}. {y[0]} | قدرت: {y[1]}\n"

    await update.message.reply_text(text)

# -----------------------
# جستجوی یارو
# -----------------------
async def search_yaro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = random.sample(yaro_types, 3)
    context.user_data["search"] = options

    text = "🔍 یاروهای پیدا شده:\n\n"
    for i, (name, price) in enumerate(options):
        text += f"{i+1}. {name} - {price}$\n"

    text += "\nبرای خرید 1 یا 2 یا 3 را بزن"
    await update.message.reply_text(text)

# -----------------------
# بازار
# -----------------------
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = random.sample(shop_items, 3)
    context.user_data["market"] = items

    text = "🛒 بازار:\n\n"
    for i, (name, price, typ) in enumerate(items):
        text += f"{i+1}. {name} - {price}$\n"

    text += "\nبرای خرید 1 یا 2 یا 3 را بزن"
    await update.message.reply_text(text)

# -----------------------
# آیتم‌های بازیکن
# -----------------------
async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT name, type FROM items WHERE user_id=?", (user_id,))
    items = cursor.fetchall()

    text = "🎒 آیتم‌های شما:\n\n"

    if not items:
        text += "هیچ آیتمی نداری"
    else:
        for i, it in enumerate(items):
            text += f"{i+1}. {it[0]} ({it[1]})\n"

    await update.message.reply_text(text)

# -----------------------
# خرید (یارو + بازار)
# -----------------------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = get_player(user_id)

    try:
        choice = int(update.message.text.strip()) - 1
    except:
        return

    # خرید یارو
    if "search" in context.user_data:
        options = context.user_data["search"]
        name, price = options[choice]

        if p[2] < price:
            return await update.message.reply_text("💸 پول نداری")

        cursor.execute("INSERT INTO yaro (user_id, name, power) VALUES (?, ?, ?)",
                       (user_id, name, random.randint(40, 100)))

        cursor.execute("UPDATE players SET money=money-? WHERE user_id=?", (price, user_id))
        conn.commit()

        del context.user_data["search"]

        return await update.message.reply_text(f"✅ {name} خریداری شد!")

    # خرید آیتم
    if "market" in context.user_data:
        items = context.user_data["market"]
        name, price, typ = items[choice]

        if p[2] < price:
            return await update.message.reply_text("💸 پول نداری")

        cursor.execute("INSERT INTO items (user_id, name, type) VALUES (?, ?, ?)",
                       (user_id, name, typ))

        cursor.execute("UPDATE players SET money=money-? WHERE user_id=?", (price, user_id))
        conn.commit()

        del context.user_data["market"]

        return await update.message.reply_text(f"🎒 {name} خریداری شد!")

# -----------------------
# مرحله ساده
# -----------------------
async def stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = get_player(user_id)

    cursor.execute("SELECT SUM(power) FROM yaro WHERE user_id=?", (user_id,))
    power = cursor.fetchone()[0] or 0

    enemy = p[3] * 60 + random.randint(0, 50)

    if power > enemy:
        cursor.execute("UPDATE players SET stage=stage+1, money=money+100 WHERE user_id=?", (user_id,))
        conn.commit()
        await update.message.reply_text("🏆 بردی +100 دلار")
    else:
        await update.message.reply_text("💀 باختی")

# -----------------------
# کنترل پیام‌ها
# -----------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 وضعیت":
        return await status(update, context)

    if text == "👥 یارو":
        return await show_yaro(update, context)

    if text == "🔍 جستجوی یارو":
        return await search_yaro(update, context)

    if text == "🛒 بازار":
        return await market(update, context)

    if text == "🎒 آیتم":
        return await show_items(update, context)

    if text == "⚔ مرحله":
        return await stage(update, context)

    if text in ["1", "2", "3"]:
        return await buy(update, context)

    if text == "❌ لغو":
        return await update.message.reply_text("لغو شد", reply_markup=menu())

# -----------------------
# اجرا
# -----------------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()
