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

        # создаем таблицу профиля
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bio TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            content TEXT,
            photo_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES user_profiles(profile_id)
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


def create_user_profile(conn, bio):
    """ Создает новый профиль пользователя """
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_profiles (bio) VALUES (?)", (bio,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Ошибка при создании профиля: {e}")
        return None

def get_user_profile(conn, profile_id):
    """ Получает профиль пользователя по ID """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE profile_id = ?", (profile_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Ошибка при получении профиля: {e}")
        return None

def update_user_profile(conn, profile_id, new_bio):
    """ Обновляет био профиля пользователя """
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE user_profiles SET bio = ? WHERE profile_id = ?", (new_bio, profile_id))
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении профиля: {e}")
        return None

def delete_user_profile(conn, profile_id):
    """ Удаляет профиль пользователя """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_profiles WHERE profile_id = ?", (profile_id,))
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Ошибка при удалении профиля: {e}")
        return None

def create_post(conn, content, photo_url):
    """ Создает новый пост """
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (content, photo_url) VALUES (?, ?)", (content, photo_url))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Ошибка при создании поста: {e}")
        return None

def get_post(conn, post_id):
    """ Получает пост по ID """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Ошибка при получении поста: {e}")
        return None

def update_post(conn, post_id, new_content, new_photo_url):
    """ Обновляет содержимое и фото поста """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE posts 
            SET content = ?, photo_url = ?
            WHERE post_id = ?
        """, (new_content, new_photo_url, post_id))
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении поста: {e}")
        return None

def delete_post(conn, post_id):
    """ Удаляет пост по ID """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Ошибка при удалении поста: {e}")
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