import pymysql.cursors
import pymysql

connect = {
    'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '', 'database': 'change_money', 'cursorclass': pymysql.cursors.DictCursor
}


def connect_to_db(connect):
    try:
        DB = pymysql.connect(**connect)
    except Exception:
        exit('Ошибка подключения к базе данных')
    return DB