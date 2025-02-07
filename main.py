import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

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

# Состояния для диалога
FULLNAME, AGE, PHONE, POSITION, ACTIVITY = range(5)

def start(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    c.execute("SELECT id, fullname FROM employees")
    employees = c.fetchall()
    
    for emp in employees:
        keyboard.append([InlineKeyboardButton(emp[1], callback_data=f"view_{emp[0]}")])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить сотрудника", callback_data="add_employee")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.message.edit_text("Выберите сотрудника:", reply_markup=reply_markup)
    else:
        update.message.reply_text("Выберите сотрудника:", reply_markup=reply_markup)
    return ConversationHandler.END

def view_employee(update: Update, context: CallbackContext):
    query = update.callback_query
    emp_id = query.data.split("_")[1]
    c.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    emp = c.fetchone()
    
    if emp:
        text = (f"📌ФИО: {emp[1]}\n"
                f"🎂Возраст: {emp[2]}\n"
                f"📱Телефон: {emp[3]}\n"
                f"💼Должность: {emp[4]}\n"
                f"🔧Деятельность: {emp[5]}\n"
                f"⭐️Баллы: {emp[6]}")
        keyboard = [
            [InlineKeyboardButton("Удалить сотрудника", callback_data=f"delete_{emp_id}")],
            [InlineKeyboardButton("Добавить баллы", callback_data=f"add_points_{emp_id}")],
            [InlineKeyboardButton("Удалить баллы", callback_data=f"remove_points_{emp_id}")],
            [InlineKeyboardButton("⬅ Назад", callback_data="back")]
        ]
        query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def add_employee(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("Введите ФИО сотрудника:")
    return FULLNAME

def receive_fullname(update: Update, context: CallbackContext):
    context.user_data['fullname'] = update.message.text
    update.message.reply_text("Введите возраст сотрудника (1-150):")
    return AGE

def receive_age(update: Update, context: CallbackContext):
    try:
        age = int(update.message.text)
        if 1 <= age <= 150:
            context.user_data['age'] = age
            update.message.reply_text("Введите телефон сотрудника:")
            return PHONE
        update.message.reply_text("❌ Возраст должен быть от 1 до 150. Попробуйте еще раз:")
        return AGE
    except ValueError:
        update.message.reply_text("❌ Введите число от 1 до 150. Попробуйте еще раз:")
        return AGE

def receive_phone(update: Update, context: CallbackContext):
    context.user_data['phone'] = update.message.text
    update.message.reply_text("Введите должность сотрудника:")
    return POSITION

def receive_position(update: Update, context: CallbackContext):
    context.user_data['position'] = update.message.text
    update.message.reply_text("Введите деятельность сотрудника:")
    return ACTIVITY

def receive_activity(update: Update, context: CallbackContext):
    # Собираем все данные
    data = [
        context.user_data['fullname'],
        context.user_data['age'],
        context.user_data['phone'],
        context.user_data['position'],
        update.message.text  # activity
    ]
    
    # Вставляем в БД
    c.execute('''INSERT INTO employees 
              (fullname, age, phone, position, activity) 
              VALUES (?, ?, ?, ?, ?)''', data)
    conn.commit()
    
    update.message.reply_text("✅ Сотрудник успешно добавлен!")
    start(update, context)
    return ConversationHandler.END

def delete_employee(update: Update, context: CallbackContext):
    query = update.callback_query
    emp_id = query.data.split("_")[1]
    c.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    query.answer("Сотрудник удален!")
    start(update, context)

def change_points(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("_")
    emp_id = data[2]
    operation = data[0]
    
    context.user_data['emp_id'] = emp_id
    context.user_data['operation'] = operation
    
    query.message.reply_text("Введите количество баллов (1-99999):")
    return 1

def receive_points(update: Update, context: CallbackContext):
    try:
        points = int(update.message.text)
        if 1 <= points <= 99999:
            emp_id = context.user_data['emp_id']
            operation = context.user_data['operation']
            
            c.execute("SELECT points FROM employees WHERE id=?", (emp_id,))
            current_points = c.fetchone()[0]
            
            new_points = current_points + points if operation == "add" else current_points - points
            
            c.execute("UPDATE employees SET points=? WHERE id=?", (new_points, emp_id))
            conn.commit()
            
            update.message.reply_text(f"✅ Баллы обновлены! Текущий баланс: {new_points}")
            start(update, context)
            return ConversationHandler.END
        update.message.reply_text("❌ Введите число от 1 до 99999:")
        return 1
    except ValueError:
        update.message.reply_text("❌ Введите целое число:")
        return 1

def main():
    updater = Updater("ТОКЕН_БОТА", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_employee, pattern="add_employee")],
        states={
            FULLNAME: [MessageHandler(Filters.text & ~Filters.command, receive_fullname)],
            AGE: [MessageHandler(Filters.text & ~Filters.command, receive_age)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, receive_phone)],
            POSITION: [MessageHandler(Filters.text & ~Filters.command, receive_position)],
            ACTIVITY: [MessageHandler(Filters.text & ~Filters.command, receive_activity)]
        },
        fallbacks=[]
    )

    points_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(change_points, pattern=r"^(add_points|remove_points)_")],
        states={1: [MessageHandler(Filters.text & ~Filters.command, receive_points)]},
        fallbacks=[]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(view_employee, pattern=r"^view_"))
    dp.add_handler(CallbackQueryHandler(delete_employee, pattern=r"^delete_"))
    dp.add_handler(CallbackQueryHandler(start, pattern="back"))
    dp.add_handler(conv_handler)
    dp.add_handler(points_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()