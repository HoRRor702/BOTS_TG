import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Создаем БД
conn = sqlite3.connect("employees.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS employees (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             fullname TEXT,
             age INTEGER,
             phone TEXT,
             position TEXT,
             activity TEXT,
             points INTEGER DEFAULT 0)''')
conn.commit()
i = 0
def start(update: Update, context: CallbackContext):
    global i
    keyboard = []
    c.execute("SELECT id, fullname FROM employees")
    employees = c.fetchall()
    
    for emp in employees:
        keyboard.append([InlineKeyboardButton(emp[1], callback_data=f"view_{emp[0]}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = update.effective_chat.id
    last_msg_id = context.chat_data.get('last_msg_id')

    if last_msg_id:
        try:
            msg = update.message.reply_text("Выберите сотрудника:", reply_markup=reply_markup)
            context.chat_data['last_msg_id'] = msg.message_id
        except Exception:

                    # Если сообщение не найдено (например, удалено), отправляем новое
                msg = update.message.reply_text("Выберите сотрудника:", reply_markup=reply_markup)
                context.chat_data['last_msg_id'] = msg.message_id

    else:
        msg = update.message.reply_text("Выберите сотрудника:", reply_markup=reply_markup)
        context.chat_data['last_msg_id'] = msg.message_id


def view_employee(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    try:
        emp_id = query.data.split("_")[1]
        c.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
        emp = c.fetchone()
        
        if emp:
            text = (f"📌 ФИО: {emp[1]}\n"
                    f"🎂 Возраст: {emp[2]}\n"
                    f"📱 Телефон: {emp[3]}\n"
                    f"💼 Должность: {emp[4]}\n"
                    f"🔧 Деятельность: {emp[5]}\n"
                    f"⭐ Баллы: {emp[6]}")
            
            keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back")]]
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("❌ Сотрудник не найден в базе")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        query.edit_message_text("⚠ Ошибка при загрузке данных")

def back_to_list(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = []
    c.execute("SELECT id, fullname FROM employees")
    employees = c.fetchall()
    
    for emp in employees:
        keyboard.append([InlineKeyboardButton(emp[1], callback_data=f"view_{emp[0]}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query.edit_message_text("Выберите сотрудника:", reply_markup=reply_markup)
        context.chat_data['last_msg_id'] = query.message.message_id
    except Exception:
        query.message.reply_text("Выберите сотрудника:", reply_markup=reply_markup)


def main():
    updater = Updater("ТОКЕН_БОТА", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(view_employee, pattern=r"^view_"))
    dp.add_handler(CallbackQueryHandler(back_to_list, pattern="back"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()