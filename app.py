from flask import Flask, jsonify, request
import threading
import sqlite3
from server import is_port_open, open_port, start_server, receive_messages, send_messages, handle_client
from users_database import create_connection, insert_message, get_user_messages, create_tables

app = Flask(__name__)

# Глобальные переменные для управления сервером
server_thread = None
server_running = False
current_port = None

# Инициализация базы данных при старте API
def init_db():
    conn = create_connection("chat_db.sqlite")
    if conn is not None:
        create_tables(conn)
        conn.close()

# Функция для получения соединения с БД в каждом запросе
def get_db_connection():
    conn = create_connection("chat_db.sqlite")
    return conn

# Добавляем новый эндпоинт для работы с сообщениями
@app.route('/api/messages', methods=['GET', 'POST'])
def handle_messages():
    if request.method == 'POST':
        return save_message()
    else:
        return get_messages()

def save_message():
    data = request.get_json()
    username = data.get('username')
    message = data.get('message')
    
    if not username or not message:
        return jsonify({
            'status': 'error',
            'message': 'Username and message are required'
        }), 400
    
    conn = get_db_connection()
    try:
        success = insert_message(conn, username, message)
        if success:
            conn.commit()
            return jsonify({
                'status': 'success',
                'username': username,
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save message'
            }), 500
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        conn.close()

def get_messages():
    username = request.args.get('username')
    
    if not username:
        return jsonify({
            'status': 'error',
            'message': 'Username parameter is required'
        }), 400
    
    conn = get_db_connection()
    try:
        messages = get_user_messages(conn, username)
        if messages is not None:
            return jsonify({
                'status': 'success',
                'username': username,
                'messages': [{
                    'text': msg[0],
                    'timestamp': msg[1]
                } for msg in messages]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve messages'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        conn.close()

# Модифицируем функцию handle_client для сохранения сообщений в БД
def modified_handle_client(client_socket, addr):
    print(f"[Инфо] Подключился клиент: {addr}")
    
    def save_received_message(message):
        username = f"client_{addr[0]}"  # Генерируем имя пользователя из IP
        conn = get_db_connection()
        try:
            insert_message(conn, username, message)
            conn.commit()
        except Exception as e:
            print(f"Ошибка при сохранении сообщения: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    recv_thread = threading.Thread(
        target=receive_messages_wrapper,
        args=(client_socket, addr, save_received_message),
        daemon=True
    )
    send_thread = threading.Thread(
        target=send_messages_wrapper,
        args=(client_socket, addr),
        daemon=True
    )
    
    recv_thread.start()
    send_thread.start()
    recv_thread.join()
    send_thread.join()

def receive_messages_wrapper(client_socket, addr, callback):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f"[Инфо] Клиент {addr} отключился.")
                break
            message = data.decode('utf-8', errors='ignore')
            print(f"\n[Сообщение от {addr}]: {message}")
            callback(message)  # Сохраняем сообщение в БД
    except Exception as e:
        print(f"[Ошибка] Ошибка при получении данных от {addr}: {e}")
    finally:
        client_socket.close()

def send_messages_wrapper(client_socket, addr):
    try:
        while True:
            message = input("Введите ответ клиенту: ")
            if not message:
                continue
            client_socket.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"[Ошибка] Ошибка при отправке данных клиенту {addr}: {e}")
    finally:
        client_socket.close()

# Инициализируем базу данных при старте
init_db()

@app.route('/api/check_port', methods=['GET'])
def api_check_port():
    host = request.args.get('host', '127.0.0.1')
    port = int(request.args.get('port', 80))
    
    try:
        result = is_port_open(host, port)
        return jsonify({
            'status': 'success',
            'host': host,
            'port': port,
            'is_open': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/open_port', methods=['POST'])
def api_open_port():
    global current_port
    
    data = request.get_json()
    external_port = data.get('external_port', 15001)
    internal_port = data.get('internal_port', 15001)
    protocol = data.get('protocol', 'TCP')
    description = data.get('description', 'Flask UPnP Port')
    
    try:
        result = open_port(external_port, internal_port, protocol, description)
        if result:
            current_port = internal_port
            return jsonify({
                'status': 'success',
                'external_port': external_port,
                'internal_port': internal_port,
                'protocol': protocol,
                'description': description
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to open port'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/start_server', methods=['POST'])
def api_start_server():
    global server_thread, server_running, current_port
    
    if server_running:
        return jsonify({
            'status': 'error',
            'message': 'Server is already running'
        }), 400
    
    data = request.get_json()
    port = data.get('port', current_port or 15001)
    
    try:
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()
        server_running = True
        
        return jsonify({
            'status': 'success',
            'port': port,
            'message': 'Server started successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stop_server', methods=['POST'])
def api_stop_server():
    global server_running

    server_running = False
    
    return jsonify({
        'status': 'success',
        'message': 'Server stop requested (may take a moment)'
    })

@app.route('/api/server_status', methods=['GET'])
def api_server_status():
    return jsonify({
        'status': 'success',
        'server_running': server_running,
        'current_port': current_port
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)