from db import *
import telebot
from lib import *
import time
from telebot import *


# Глобальные переменные
# переменная равна 0 пока мы не узнали, что в аккаунте нет параметра username
none_username = 0
# номер карты
user_card_number = 0
# сумма перевода
summ_from_user = 0
# валютная пара
change_pair = 0
# статус заявки
status = 0

mess_id = 0
pol = 0


# Подключаем базу
DB = connect_to_db(connect)



# токен
bot = telebot.TeleBot('6146642902:AAHA02ejfF5QUA7JK-vOfUN63Z1c9Tvwdb4')

@bot.message_handler(commands=['start', 'help'],content_types=['text'])
def check_user(message):
    global none_username, mess_id,connect,DB
    if message.from_user.username == None:
        bot.send_message(message.from_user.id, "В целях безопасности и возможности обратной связи необходимо создать имя пользователя в твоём Telegram🙂")
        none_username = 1
    uid = (search_uid_by_telegram_username(message.from_user.username,DB))
    check_order = (check_orders_userid(uid,DB))
    if none_username == 0:
        # Если нет текущих заявок
        if check_order == False and status < 4:
            create_user_if_not_exists(DB,message,bot,types)
            keyboard = types.InlineKeyboardMarkup()
            # сбор валютных пар для обмена
            DB = connect_to_db(connect)
            with DB.cursor() as db:
                currency_pairs = f'SELECT * FROM currency_pairs WHERE status = 1'
                currency_pairs = db.execute(currency_pairs)
                currency_pairs = db.fetchall()
                for currency_pair in currency_pairs:
                    keyboard.add(types.InlineKeyboardButton(text=str(currency_pair['name']),
                                                            callback_data=str(str(currency_pair['id']) + '_pair_id')))
            bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}. Я могу помочь тебе с обменом валют."
                                                f" Давай выберем валютную пару.", reply_markup=keyboard)
            DB.close()
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Проверить статус заявки', callback_data='check_order'))
            mess_id = bot.send_message(message.from_user.id,
                             f"{message.from_user.first_name}, на тебя уже создана заявка. В целях безопасности мы можем держать открытой только одну. Проверь статус заявки"
                             f"", reply_markup=keyboard).id
    # регистрируем следующий шаг
    bot.register_next_step_handler(message, get_card)

def get_card(message):
    global user_card_number
    if message.text != '/start':

        if message.text.isdigit() == False:
            bot.send_message(message.from_user.id,
                             f"{message.from_user.first_name}, номер карты некорректный. Попробуй ещё раз.")
            bot.register_next_step_handler(message, get_card)
        else:
            bot.send_message(message.from_user.id,
                             f"Отлично!")
            user_card_number = message.text
            bot.send_message(message.from_user.id, f'Теперь уточните сумму для обмена. Используйте только цифры.')
            bot.register_next_step_handler(message, get_summ)


def get_summ(message):
    global summ_from_user,change_pair,DB,connect
    import datetime
    if message.text != '/start':
        if message.text.isdigit() == False:
            bot.send_message(message.from_user.id,
                             f"{message.from_user.first_name}, сумма введена некорректно. Попробуй ещё раз.")
            bot.register_next_step_handler(message, get_summ)
        else:
            # создаём заявку в базе
            username = message.from_user.username
            created = time.time()
            summ_from_user = message.text
            # смотрим идентификатор пользователя в нашей БД на основе username
            see_uid = f"SELECT * FROM users WHERE telegram_username = '{username}'"
            DB = connect_to_db(connect)
            with DB.cursor() as db:
                db.execute(see_uid)
                data = db.fetchall()
                for content in data:
                    userid = content['id']
            DB.close()
            DB = connect_to_db(connect)
            create_order_sql = f"INSERT INTO orders (tg_user_id,pair_id,summ,created,client_bank_card_number) VALUES ('{userid}','{change_pair}','{summ_from_user}','{created}','{user_card_number}')"
            # create_push_sql = f"INSERT INTO orders (tg_user_id,pair_id,summ,created,client_bank_card_number) VALUES ('{userid}','{change_pair}','{summ_from_user}','{created}','{user_card_number}')"
            with DB.cursor() as db:
                db.execute(create_order_sql)
                lr = db.lastrowid
                date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                create_push_sql = f"INSERT INTO request_money_log (`order`,`last`,`date`) VALUES ('{lr}','1','{date}')"
                print(create_push_sql)

                db.execute(create_push_sql)
                DB.commit()
            DB.close()
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Проверить '
                                                         'статус заявки', callback_data='check_order'))
            bot.send_message(message.from_user.id,
                             f"Заявка на обмен создана. Ожидайте уведомления.",
                             reply_markup=keyboard)
            # bot.register_next_step_handler(message)


def check_order_status(message):
    global user_card_number, summ_from_user
    if user_card_number != 0 and summ_from_user !=0:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Проверить '
                                                     'статус заявки', callback_data='check_order'))
        bot.send_message(message.from_user.id,
                         f"Заявка на обмен создана. С Вами свяжется Рустам через личные сообщения.",reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def start(call):
    global change_pair,status, mess_id, pol,connect
    if '_pair_id' in call.data:

        id = call.data.split('_')[0] # идентификатор валютной пары из БД
        change_pair = id
        DB = connect_to_db(connect)
        with DB.cursor() as db:
            currency_pairs_courses = f'SELECT * FROM currency_pairs_courses WHERE pair_id = {id}'
            currency_pairs_courses = db.execute(currency_pairs_courses)
            currency_pairs_courses = db.fetchall()
            for currency_pairs_course in currency_pairs_courses:
                course = str(currency_pairs_course['value'])
        DB.close()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Да', callback_data='create_order'))
        keyboard.add(types.InlineKeyboardButton(text='Нет', callback_data='0'))
        bot.send_message(call.message.chat.id, f'Курс по данной паре равен {course}. Создать заявку на обмен?',
                         reply_markup=keyboard)
    if 'create_order' in call.data:
        bot.send_message(call.message.chat.id, f'Уточните номер карты. Используйте только цифры.')


    # если нажата кнопка проверки заявки
    if 'check_order' in call.data:
        DB = connect_to_db(connect)
        # собираем инфу по заявке на основе username телеги, предварительно смотрим под каким ИД он в нашей базе
        with DB.cursor() as db:
            user_id = f"SELECT * FROM users WHERE telegram_username = '{call.from_user.username}'"
            user_id = db.execute(user_id)
            user_id = db.fetchall()
            DB.cursor().close()
            for userid in user_id:
                user__id = userid['id']
        DB.close()
        DB = connect_to_db(connect)
        with DB.cursor() as db:
            user__id = search_uid_by_telegram_username(call.from_user.username,DB)
            username_order_sql = f'SELECT ' \
                             f'ord.id, ord.pair_id, ord.tg_user_id, refst.name, ord.summ, ROUND(ord.summ / courses.value) as value, DATE_FORMAT(FROM_UNIXTIME(ord.created),"%d-%m-%Y, %H:%i:%s") as created, ord.client_bank_card_number' \
                             f' FROM orders ord ' \
                             f' INNER JOIN order_ref_status refst ON refst.id = ord.status_id' \
                             f' INNER JOIN currency_pairs_courses courses ON courses.pair_id = ord.pair_id' \
                             f' WHERE ord.tg_user_id = {user__id} AND refst.id != 4'
            username_order_data = db.execute(username_order_sql)
            username_order_fetch = db.fetchall()

            if username_order_fetch:
                for order in username_order_fetch:
                    # Функция проверяет сколько заявок на данную валютную пару сейчас висит (заявками в очереди считаются заявки созданные раньше текущей, по текущей ВП и с незакрытым статусом)
                    count_orders = db.execute(f"SELECT count(*) FROM orders WHERE id < {order['id']} AND status_id != 4 AND pair_id = {order['pair_id']}")
                    answer = f"Время создания заявки: {order['created']}\n" \
                             f"Статус заявки: {order['name']}\n" \
                             f"Указанная Вами карта: {order['client_bank_card_number']}\n" \
                             f"Запрошенная сумма перевода: {order['summ']}\n" \
                             f"Перед Вами в очереди: {count_orders} заявка(-вок) на обмен\n" \
                             f"Вы получите в конечной валюте: {order['value']}\n" \
                             f"/start"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text=f'Проверить '
                                                             f'статус заявки', callback_data='check_order'))
                bot.send_message(call.message.chat.id, answer,reply_markup=keyboard)

            else:
                answer = "Нет активных заявок. Нажмите /start для создания"
                bot.send_message(call.message.chat.id, answer)
        DB.close()

bot.polling(none_stop=True)
