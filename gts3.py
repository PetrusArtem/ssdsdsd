import telebot
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telebot import types


# настройки бота
bot_token = '5990588377:AAGLUbfFDUQ7GrF6qmTxxZab1oM7TWbgFDM'
bot = telebot.TeleBot(bot_token)

# настройки Google таблицы
google_sheet_key = '1uVzPBQhopvMi9Uj5fvbyQ4nbQsLcWO0QzPp9ch61Dnk'
credentials = ServiceAccountCredentials.from_json_keyfile_name('/Users/anastasiasolosina/Desktop/telebot/telebot-385720-53e038c6ef30.json',
                                                               ['https://spreadsheets.google.com/feeds',
                                                                'https://www.googleapis.com/auth/drive'])
google_sheet_client = gspread.authorize(credentials)
google_sheet = google_sheet_client.open_by_key(google_sheet_key).sheet1


# создаем словарь с названиями столбцов
column_names = {
    'id': 1,
    'username': 2,
    'current_time': 3,
    'answer_A': 4,
    'answer_B': 5,
    'answer_C': 6,
    'result': 7
}

# функция для записи ответов в таблицу
def write_answers_to_table(id, username, answer_A, answer_B, answer_C):
    current_time = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    data = google_sheet.get_all_values()
    for i in range(1, len(data)):
        if data[i][0] == "":
            row = i + 1
            break
    else:
        row = len(data) + 1
    cell_list = google_sheet.range(row, 1, row, 6)
    cell_list[0].value = id
    cell_list[1].value = username
    cell_list[2].value = current_time
    cell_list[3].value = answer_A
    cell_list[4].value = answer_B
    cell_list[5].value = answer_C
    google_sheet.update_cells(cell_list)
    
# функция для проверки, является ли введенный ответ цифрой
def is_digit(answer):
    try:
        int(answer)
        return True
    except ValueError:
        return False

# функция для задания вопроса A и проверки верности ответа
def ask_question_A(message):
    bot.send_message(message.chat.id,  "Первый вопрос: " + google_sheet.cell(1, column_names['answer_A']).value)
    bot.register_next_step_handler(message, handle_answer_A)

# функция для проверки верности ответа A, записи в таблицу и перехода к вопросу B или повторному вопросу A
def handle_answer_A(message):
    user_id = str(message.chat.id)
    username = message.chat.username
    answer_A = message.text

    if is_digit(answer_A):
        write_answers_to_table(user_id, username, answer_A, '', '')
        ask_question_B(message)
    else:
        bot.send_message(message.chat.id, "Вы ввели некорректный ответ. Пожалуйста, введите цифру.")
        bot.register_next_step_handler(message, handle_answer_A)

# функция для задания вопроса B и проверки верности ответа
def ask_question_B(message):
    bot.send_message(message.chat.id,  "Второй вопрос: " + google_sheet.cell(1, column_names['answer_B']).value)
    bot.register_next_step_handler(message, handle_answer_B)

# функция для проверки верности ответа B, записи в таблицу и перехода к вопросу C или повторному вопросу B
def handle_answer_B(message):
    user_id = str(message.chat.id)
    username = message.chat.username
    answer_B = message.text

    if is_digit(answer_B):
        row = google_sheet.find(user_id)
        google_sheet.update_cell(row.row, column_names['answer_B'], answer_B)
        ask_question_C(message)
    else:
        bot.send_message(message.chat.id,  "Вы ввели некорректный ответ. Пожалуйста, введите цифру.")
        bot.register_next_step_handler(message, handle_answer_B)

# функция для задания вопроса C и проверки верности ответа
def ask_question_C(message):
    bot.send_message(message.chat.id, "Третий вопрос: " + google_sheet.cell(1, column_names['answer_C']).value)
    bot.register_next_step_handler(message, handle_answer_C)


# функция для проверки верности ответа C, записи в таблицу и отправки результата пользователю или повторному вопросу C
def handle_answer_C(message):
    user_id = str(message.chat.id)
    username = message.chat.username
    answer_C = message.text

    if is_digit(answer_C):
        row = google_sheet.find(user_id)
        google_sheet.update_cell(row.row, column_names['answer_C'], answer_C)
        send_result(message)
    else:
        bot.send_message(message.chat.id, "Вы ввели некорректный ответ. Пожалуйста, введите цифру.")
        bot.register_next_step_handler(message, handle_answer_C)

# функция для отправки результата пользователю и предложения пройти опрос заново
def send_result(message):
    user_id = str(message.chat.id)
    row = google_sheet.find(user_id)
    result = google_sheet.cell(row.row, column_names['result']).value

    # отправляем пользователю сообщение с вопросом о получении расчета
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    item_yes = telebot.types.KeyboardButton('Да')
    item_no = telebot.types.KeyboardButton('Нет')
    markup.add(item_yes, item_no)
    bot.send_message(chat_id=user_id, text="Хотите получить расчет?", reply_markup=markup)

    # ждем ответа пользователя
    bot.register_next_step_handler(message, handle_final_answer)

# функция для обработки ответа пользователя о получении расчета
def handle_final_answer(message):
    user_id = str(message.chat.id)
    answer = message.text.lower()

    # если ответ пользователя - "да"
    if answer == 'да':
        row = google_sheet.find(user_id)
        answer_A = int(google_sheet.cell(row.row, column_names['answer_A']).value or 0)
        answer_B = int(google_sheet.cell(row.row, column_names['answer_B']).value or 0)
        answer_C = int(google_sheet.cell(row.row, column_names['answer_C']).value or 0)

        # задержка на 1 секунду, чтобы данные успели обновиться в таблице
        time.sleep(1)
        result = answer_A + answer_B + answer_C
        
        # отправляем пользователю результат
        bot.send_message(chat_id=user_id, text="Результат: " + str(result), reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(chat_id=user_id, text="Хотите пройти опрос заново?")
        ask_question_A(message)

            # если ответ пользователя - "нет"
    elif answer == 'нет':
        bot.send_message(chat_id=user_id, text="Понял")
    
    # если ответ пользователя не распознан
    else:
        bot.send_message(chat_id=user_id, text="Пожалуйста, ответьте 'Да' или 'Нет'.")
        bot.register_next_step_handler(message, handle_final_answer)

@bot.message_handler(commands=['start', 'restart'])
def send_welcome(message):
    command = message.text.split()[0][1:]
    user_id = str(message.chat.id)

    # если пользователь отправил команду "start" или "restart"
    if command in ['start', 'restart']:
        # удаляем старые ответы из таблицы, связанные с этим пользователем
        rows = google_sheet.findall(user_id)
        for row in rows:
            google_sheet.delete_rows(row.row)

        # отправляем приветственное сообщение и задаем первый вопрос
        bot.send_message(message.chat.id, "Добро пожаловать! Начнем опрос.")
        ask_question_A(message)

    # если пользователь отправил неизвестную команду
    else:
        bot.send_message(str(message.chat.id), "Команда не распознана, попробуйте еще раз.")

bot.polling(none_stop=True)
