import MySQLdb
from flask import g

def get_db():
    if 'db' not in g:
        try:
            # Подключаемся к MySQL
            g.db = MySQLdb.connect(
                host='sql7.freesqldatabase.com',  # Хост базы данных
                user='sql7731360',  # Имя пользователя
                password='Sf7UelJnpj',  # Пароль
                db='sql7731360',  # Имя базы данных
                port=3306  # Порт базы данных
            )
            print("Connected to the database")

        except MySQLdb.Error as err:
            print(f"Error connecting to the database: {err}")
            g.db = None
    return g.db

def fetch_data(query):
    db = get_db()
    try:
        cursor = db.cursor()  # Создаем курсор для выполнения запроса
        cursor.execute(query)
        rows = cursor.fetchall()
        # Преобразуем результат в список словарей вручную
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        return result
    except MySQLdb.Error as err:
        print(f"Error fetching data: {err}")
        return None
