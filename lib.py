from db import *

def create_user_if_not_exists(DB, message,bot,types):
    global connect
    DB = connect_to_db(connect)
    with DB.cursor() as db:
        check_new = f"SELECT id FROM users WHERE telegram_username = '{message.from_user.username}'"
        check = db.execute(check_new)
        if check == 0:
            create_user_sql = f"INSERT INTO users (telegram_username,username,chat_id) VALUES ('{message.from_user.username}','{message.from_user.first_name}','{message.chat.id}')"
            db.execute(create_user_sql)
            DB.commit()
            DB.close()
        else:
            search_last_ids = db.fetchall()
            for search_last_id in search_last_ids:
                lastid = search_last_id['id']
                DB.close()

# ищет userid по username
def search_uid_by_telegram_username(username,DB):
    global connect
    DB = connect_to_db(connect)
    with DB.cursor() as db:
        users = f"SELECT * FROM users WHERE telegram_username = '{username}'"
        users = db.execute(users)
        users = db.fetchall()
        for user in users:
            DB.close()
            return user['id']

# смотрит, есть ли открытые заявки на юзерид
def check_orders_userid(userid,DB):
    global order_status, status, connect
    DB = connect_to_db(connect)
    with DB.cursor() as db:
        users = f"SELECT * FROM orders WHERE tg_user_id = '{userid}' AND status_id != 4"
        users = db.execute(users)
        users = db.fetchall()
        if users:
            for user in users:
                status = user['status_id']
                DB.close()
                return True
        else:
            DB.close()
            return False


def get_order_info(bot,types,call):
    global connect
    DB = connect_to_db(connect)
    with DB.cursor() as db:
        user__id = search_uid_by_telegram_username(call.from_user.username,DB)
        username_order_sql = f'SELECT ' \
                             f'ord.tg_user_id, refst.name, ord.summ, DATE_FORMAT(FROM_UNIXTIME(ord.created),"%d-%m-%Y, %H:%i:%s") as created, ord.client_bank_card_number' \
                             f' FROM orders ord ' \
                             f'INNER JOIN order_ref_status refst ON refst.id = ord.status_id' \
                             f' WHERE ord.tg_user_id = {user__id}'
        # print(username_order)
        username_order_data = db.execute(username_order_sql)
        username_order_fetch = db.fetchall()

        # print(username_order)
        if username_order_fetch:
            for order in username_order_fetch:
                answer = f"Время создания заявки: {order['created']}\n" \
                         f"Статус заявки: {order['name']}\n" \
                         f"Указанная Вами карта: {order['client_bank_card_number']}\n" \
                         f"Запрошенная сумма перевода: {order['summ']}\n" \
                         f"Данные: {username_order_sql}\n" \
                         f"Вы получите в конечной валюте: 24242\n"
            keyboard = types.InlineKeyboardMarkup()
            t = time.time()
            keyboard.add(types.InlineKeyboardButton(text=f'Проверить '
                                                         f'статус заявки {t}', callback_data='check_order'))
            bot.send_message(call.message.chat.id, answer, reply_markup=keyboard)
            DB.close()
            bot.register_callback_query_handler(call, start)

        else:
            # print(status)
            answer = "Нет активных заявок. Нажмите /start для создания"
            DB.close()
            bot.send_message(call.message.chat.id, answer)
