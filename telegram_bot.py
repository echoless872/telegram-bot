# telegram_bot.py
# প্রয়োজনীয় লাইব্রেরি: python-telegram-bot==13.15
import sqlite3
from telegram import (
    Bot,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext
)

# ================== CONFIG ==================
import os
BOT_TOKEN = os.getenv("8348921131:AAG0vvK9QRArrV7L5OUNbLx5xMhvfk-pl_E")   # <<=== এখানে আপনার Telegram Bot API টোকেন দিন (হাইলাইট)
ADMIN_TELEGRAM_ID = None  # যদি শুধু এক ব্যক্তিই প্রোডাক্ট যোগ করবে, এখানে তাঁর Telegram ID দিন (int). না দিলে None (সবাই যোগ করতে পারবে)
WHATSAPP_NUMBER = "01940212417"  # প্রদর্শনের জন্য নম্বর
WHATSAPP_COUNTRY_PREFIX = "88"   # বাংলাদেশের জন্য 88, wa.me তৈরিতে ব্যবহার হবে
CONTACT_EMAIL = "apexstore49@gmail.com"
# ============================================

# Conversation states
ASK_NAME = 1

# ==== Database helper ====
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS products (
    name TEXT PRIMARY KEY
)
""")
conn.commit()

# ==== Helper functions ====
def add_user(telegram_id: int, name: str) -> (bool, str):
    """রিটার্ন (success, message)"""
    try:
        c.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()
        return True, "অভিনন্দন — আপনার একাউন্ট তৈরি হয়েছে।"
    except sqlite3.IntegrityError as e:
        # নাম অথবা telegram_id conflict
        # দেখে নেই যদি একই নাম থাকে
        c.execute("SELECT telegram_id FROM users WHERE name = ?", (name,))
        row = c.fetchone()
        if row:
            return False, "এই নামটি আগে থেকেই নেয়া আছে — অন্য একটি নাম দিন।"
        # অন্য কোনো কনফ্লিক্ট
        return False, "একাউন্ট তৈরি করা যায়নি — পুনরায় চেষ্টা করুন।"

def add_product_db(name: str) -> (bool, str):
    try:
        c.execute("INSERT INTO products (name) VALUES (?)", (name,))
        conn.commit()
        return True, "প্রোডাক্ট যোগ করা হয়েছে।"
    except sqlite3.IntegrityError:
        return False, "এই নামের প্রোডাক্ট আগে থেকেই আছে।"

def remove_product_db(name: str) -> (bool, str):
    c.execute("DELETE FROM products WHERE name = ?", (name,))
    conn.commit()
    if c.rowcount:
        return True, "প্রোডাক্ট মুছে ফেলা হয়েছে।"
    else:
        return False, "প্রোডাক্ট পাওয়া যায়নি।"

def list_products():
    c.execute("SELECT name FROM products ORDER BY name")
    return [r[0] for r in c.fetchall()]

# ==== Bot handlers ====
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    # চেক করি ইউজার আগে আছে কি না
    c.execute("SELECT name FROM users WHERE telegram_id = ?", (user.id,))
    row = c.fetchone()
    if row:
        name = row[0]
        update.message.reply_text(
            f"আসসালামু আলাইকুম, {name}!\n\nনীচের মেনু থেকে বেছে নিন:",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    # নতুন — নাম চাই
    update.message.reply_text("আপনার নাম লিখে দিন (এই নামটি একবার ব্যবহার করা যাবে):")
    return ASK_NAME

def ask_name(update: Update, context: CallbackContext):
    user = update.effective_user
    name = update.message.text.strip()
    if not name:
        update.message.reply_text("নাম খালি পাঠানো হয়েছে — অনুগ্রহ করে একটি নাম দিন:")
        return ASK_NAME
    success, msg = add_user(user.id, name)
    update.message.reply_text(msg)
    if success:
        update.message.reply_text("প্রধান মেনু:", reply_markup=main_menu_keyboard())
        return ConversationHandler.END
    else:
        # যদি নাম নেবে না, পুনরায় চাই
        update.message.reply_text("অন্য একটি নাম দিন:")
        return ASK_NAME

def main_menu_keyboard():
    kb = [
        [KeyboardButton("Products 🔘"), KeyboardButton("Contact Email 🔘")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def text_message_router(update: Update, context: CallbackContext):
    text = update.message.text.strip().lower()
    if text.startswith("products"):
        show_products(update, context)
    elif text.startswith("contact"):
        # Email পাঠানো
        update.message.reply_text(f"আমাদের ইমেইল: {CONTACT_EMAIL}")
    else:
        update.message.reply_text("বুঝতে পারিনি। প্রধান মেনু থেকে বেছে নিন:", reply_markup=main_menu_keyboard())

def show_products(update: Update, context: CallbackContext):
    products = list_products()
    if not products:
        update.message.reply_text("কোনো প্রোডাক্ট পাওয়া যায়নি। অ্যাডমিন /addproduct দিয়ে যোগ করুন।")
        return
    keyboard = []
    for p in products:
        # প্রতিটি প্রোডাক্টের জন্য callback_data 'prod::<name>'
        keyboard.append([InlineKeyboardButton(p, callback_data=f"prod::{p}")])
    reply = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("পছন্দের প্রোডাক্টে ক্লিক করুন:", reply_markup=reply)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith("prod::"):
        prod_name = data.split("::", 1)[1]
        # WhatsApp message link
        wa_number_full = WHATSAPP_COUNTRY_PREFIX + WHATSAPP_NUMBER.lstrip("0")
        # Prepare message (বাংলা)
        msg = (
            f"আপনি *{prod_name}* নির্বাচন করেছেন।\n\n"
            f"দয়া করে এই নম্বরে মেসেজ দিন:\n"
            f"+{WHATSAPP_COUNTRY_PREFIX}{WHATSAPP_NUMBER}\n\n"
            "দয়া করে এই নাম্বারে মেসেজ দিন"
        )
        # Send message with clickable wa.me link
        wa_link = f"https://wa.me/{wa_number_full}?text=Hello%20I%20am%20interested%20in%20{prod_name.replace(' ', '%20')}"
        query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        query.message.reply_text(f"WhatsApp লিংক: {wa_link}")
    else:
        query.message.reply_text("Unknown action.")

# ==== Admin commands ====
def addproduct_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    # যদি ADMIN_TELEGRAM_ID সেট করা থাকে, চেক করি
    if ADMIN_TELEGRAM_ID and user.id != ADMIN_TELEGRAM_ID:
        update.message.reply_text("আপনার অনুমতি নেই।")
        return
    args = context.args
    if not args:
        update.message.reply_text("ব্যবহার: /addproduct প্রোডাক্ট-নাম")
        return
    name = " ".join(args).strip()
    ok, msg = add_product_db(name)
    update.message.reply_text(msg)

def removeproduct_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if ADMIN_TELEGRAM_ID and user.id != ADMIN_TELEGRAM_ID:
        update.message.reply_text("আপনার অনুমতি নেই।")
        return
    args = context.args
    if not args:
        update.message.reply_text("ব্যবহার: /removeproduct প্রোডাক্ট-নাম")
        return
    name = " ".join(args).strip()
    ok, msg = remove_product_db(name)
    update.message.reply_text(msg)

def listproducts_cmd(update: Update, context: CallbackContext):
    products = list_products()
    if not products:
        update.message.reply_text("কোনো প্রোডাক্ট নেই।")
    else:
        text = "প্রোডাক্ট তালিকা:\n" + "\n".join(f"- {p}" for p in products)
        update.message.reply_text(text)

def error_handler(update: Update, context: CallbackContext):
    # simple error logging
    print("Error:", context.error)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation for /start -> ask name
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_name)]
        },
        fallbacks=[]
    )
    dp.add_handler(conv)

    # Text router for menu
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message_router))

    # Callback query handler (product buttons)
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Admin product commands
    dp.add_handler(CommandHandler("addproduct", addproduct_cmd, pass_args=True))
    dp.add_handler(CommandHandler("removeproduct", removeproduct_cmd, pass_args=True))
    dp.add_handler(CommandHandler("listproducts", listproducts_cmd))

    dp.add_error_handler(error_handler)

    print("Bot started...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
