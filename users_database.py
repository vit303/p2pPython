import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ Создает соединение с базой данных SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Подключение к SQLite DB {db_file} успешно")
        return conn
    except Error as e:
        print(f"Ошибка при подключении к SQLite DB: {e}")
    return conn

def create_tables(conn):
    """ Создает таблицы, если они не существуют """
    try:
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей, если ее нет
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
        """)
        
        # Создаем таблицу сообщений, если ее нет
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)
        
        conn.commit()
        print("Таблицы созданы успешно")
    except Error as e:
        print(f"Ошибка при создании таблиц: {e}")

def insert_message(conn, username, message):
    """ Вставляет сообщение для пользователя (создает пользователя, если не существует) """
    try:
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
        else:
            # Если пользователя нет, создаем его
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            user_id = cursor.lastrowid
        
        # Добавляем сообщение
        cursor.execute("""
        INSERT INTO messages (user_id, message_text) 
        VALUES (?, ?)
        """, (user_id, message))
        
        conn.commit()
        print(f"Сообщение для пользователя '{username}' успешно добавлено")
        return True
    except Error as e:
        print(f"Ошибка при добавлении сообщения: {e}")
        return False

def get_user_messages(conn, username):
    """ Получает все сообщения пользователя """
    try:
        cursor = conn.cursor()
        
        # Получаем все сообщения пользователя с сортировкой по времени
        cursor.execute("""
        SELECT m.message_text, m.timestamp 
        FROM messages m
        JOIN users u ON m.user_id = u.user_id
        WHERE u.username = ?
        ORDER BY m.timestamp
        """, (username,))
        
        messages = cursor.fetchall()
        return messages
    except Error as e:
        print(f"Ошибка при получении сообщений: {e}")
        return None

# Пример использования
if __name__ == '__main__':
    database = "chat_db.sqlite"
    
    # Создаем соединение с базой данных
    conn = create_connection(database)
    
    if conn is not None:
        # Создаем таблицы
        create_tables(conn)
        
        # Добавляем несколько сообщений
        insert_message(conn, "user1", "Привет, как дела?")
        insert_message(conn, "user1", "Что нового?")
        insert_message(conn, "user2", "Здравствуйте!")
        insert_message(conn, "user1", "Как погода?")
        
        # Получаем сообщения пользователя
        username = "user1"
        messages = get_user_messages(conn, username)
        
        if messages:
            print(f"\nВсе сообщения пользователя '{username}':")
            for i, (message, timestamp) in enumerate(messages, 1):
                print(f"{i}. [{timestamp}] {message}")
        
        # Закрываем соединение
        conn.close()
    else:
        print("Ошибка! Не удалось создать соединение с базой данных.")