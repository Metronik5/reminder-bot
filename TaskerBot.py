import telebot
import time
import threading
from datetime import datetime

bot = telebot.TeleBot("ТОКЕН")

# Словарь задач: {время: (сообщение, chat_id)}
tasks = {}
# Отображение списка задач в порядке для удаления: {chat_id: [(время, сообщение)]}
user_task_index = {}

# Функция добавления задачи
def add_task(chat_id, date, message):
    try:
        task_time = datetime.strptime(date, "%Y/%m/%d %H:%M")
        tasks[task_time] = (message, chat_id)
        bot.send_message(chat_id, f"✅ Задача добавлена: '{message}' на {task_time.strftime('%Y/%m/%d %H:%M')}")
    except ValueError:
        bot.send_message(chat_id, "❌ Неверный формат. Используй: YYYY/MM/DD HH:MM")

# Фоновая проверка задач
def execute_task():
    while True:
        now = datetime.now()
        for task_time in list(tasks):
            if now >= task_time:
                message, chat_id = tasks[task_time]
                bot.send_message(chat_id, f"🔔 Напоминание: {message}")
                del tasks[task_time]
        time.sleep(60)

def run_scheduler():
    threading.Thread(target=execute_task, daemon=True).start()

# /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот-напоминалка.\n\n📌 Отправь:\n`YYYY/MM/DD HH:MM, текст задачи`\n"
        "или используй /help для списка команд.",
        parse_mode="Markdown",
    )

# /help
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "🛠 *Команды:*\n"
        "• `/start` — инструкция\n"
        "• `/help` — список команд\n"
        "• `/list` — список активных задач\n"
        "• `/delete N` — удалить задачу по номеру\n\n"
        "*Пример задачи:*\n`2025/06/20 18:30, Встретиться с другом`",
        parse_mode="Markdown",
    )

# /list — вывод задач
@bot.message_handler(commands=["list"])
def list_tasks(message):
    chat_id = message.chat.id
    user_tasks = [
        (dt, msg)
        for dt, (msg, cid) in tasks.items()
        if cid == chat_id
    ]
    if not user_tasks:
        bot.send_message(chat_id, "🗒 У тебя нет активных напоминаний.")
        return

    # Сохраняем индекс задач для этого пользователя
    user_tasks.sort()
    user_task_index[chat_id] = user_tasks

    text = "📋 *Твои задачи:*\n\n"
    for i, (dt, msg) in enumerate(user_tasks, start=1):
        text += f"{i}. `{dt.strftime('%Y/%m/%d %H:%M')}` — {msg}\n"
    bot.send_message(chat_id, text, parse_mode="Markdown")

# /delete — удаление по номеру
@bot.message_handler(commands=["delete"])
def delete_task(message):
    chat_id = message.chat.id
    try:
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            raise ValueError

        task_number = int(parts[1])
        if chat_id not in user_task_index:
            bot.send_message(chat_id, "⚠️ Сначала используй /list, чтобы увидеть задачи.")
            return

        task_list = user_task_index[chat_id]
        if task_number < 1 or task_number > len(task_list):
            bot.send_message(chat_id, "❌ Неверный номер задачи.")
            return

        task_time, _ = task_list[task_number - 1]
        if task_time in tasks and tasks[task_time][1] == chat_id:
            del tasks[task_time]
            bot.send_message(chat_id, f"🗑 Задача №{task_number} удалена.")
        else:
            bot.send_message(chat_id, "❌ Не удалось найти задачу.")
    except ValueError:
        bot.send_message(chat_id, "⚠️ Формат: `/delete N`", parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, "Произошла ошибка при удалении.")

# Обработка обычных сообщений — добавление задачи
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        date, task_message = message.text.split(",", 1)
        add_task(message.chat.id, date.strip(), task_message.strip())
    except ValueError:
        bot.send_message(
            message.chat.id,
            "⚠️ Неверный формат.\nПример: `2025/06/20 15:30, Позвонить маме`",
            parse_mode="Markdown",
        )

# Запуск бота
run_scheduler()
bot.polling(none_stop=True)
