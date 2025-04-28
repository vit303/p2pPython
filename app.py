from flask import Flask, jsonify, request
import miniupnpc
import socket
import threading

app = Flask(__name__)

clients = []  # List to hold connected client sockets

def is_port_open(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex((host, port)) == 0
    except Exception as e:
        print(f"[Ошибка] Проверка порта завершилась неудачей: {e}")
        return False

def open_port(external_port, internal_port, protocol='TCP', description='My Port Forwarding'):
    print("Поиск UPnP-устройств...")
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    try:
        devices = upnp.discover()
    except Exception as e:
        print(f"[Ошибка] Не удалось выполнить обнаружение UPnP: {e}")
        return False

    if devices == 0:
        print("[Ошибка] UPnP-устройства не найдены!")
        return False

    try:
        upnp.selectigd()
    except Exception as e:
        print(f"[Ошибка] Не удалось выбрать IGD: {e}")
        return False

    lan_address = upnp.lanaddr
    external_ip = upnp.externalipaddress()
    print(f"[Инфо] Ваш локальный IP: {lan_address}")
    print(f"[Инфо] Ваш внешний IP: {external_ip}")

    try:
        existing_mapping = upnp.getspecificportmapping(external_port, protocol)
        if existing_mapping:
            print(f"[Инфо] Обнаружено существующее правило для порта {external_port}/{protocol}: {existing_mapping}")
            try:
                upnp.deleteportmapping(external_port, protocol)
                print("[Успех] Существующее правило удалено.")
            except Exception as e:
                print(f"[Ошибка] Не удалось удалить существующее правило: {e}")
                return False
    except Exception as e:
        print(f"[Предупреждение] Не удалось проверить существующие правила: {e}")

    try:
        upnp.addportmapping(external_port, protocol, lan_address, internal_port, description, '', 0)
        print(f"[Успех] Порт {external_port} успешно открыт через UPnP.")
    except Exception as e:
        print(f"[Ошибка] Не удалось открыть порт: {e}")
        return False

    if is_port_open(external_ip, int(external_port)):
        print(f"[Успех] Порт {external_port} доступен снаружи!")
    else:
        print(f"[Внимание] Порт {external_port} не доступен снаружи.")
    return True

def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    print(f"[Инфо] Сервер запущен и слушает порт {port}")

    def client_handler(client_socket, addr):
        print(f"[Инфо] Подключился клиент: {addr}")
        clients.append(client_socket)  # Add client socket to the list

        def receive_messages():
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        print(f"[Инфо] Клиент {addr} отключился.")
                        break
                    print(f"\n[Сообщение от {addr}]: {data.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"[Ошибка] Ошибка при получении данных от {addr}: {e}")
            finally:
                client_socket.close()
                clients.remove(client_socket)  # Remove client from the list on disconnect

        threading.Thread(target=receive_messages, daemon=True).start()

    try:
        while True:
            client_socket, addr = server.accept()
            threading.Thread(target=client_handler, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[Инфо] Работа сервера остановлена пользователем.")
    finally:
        server.close()

@app.route('/open-port', methods=['POST'])
def open_port_route():
    data = request.json
    external_port = data.get('external_port', 15001)
    internal_port = data.get('internal_port', 15001)
    protocol = data.get('protocol', 'TCP')
    description = data.get('description', 'My Port Forwarding')

    success = open_port(external_port, internal_port, protocol, description)
    return jsonify(success=success)

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    external_port = data.get('external_port', 15001)
    # Start the server in a separate thread
    threading.Thread(target=start_server, args=(external_port,), daemon=True).start()
    return jsonify(success=True)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify(success=False, error="Message cannot be empty"), 400

    if not clients:
        return jsonify(success=False, error="No clients connected"), 400

    for client in clients:
        try:
            client.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"[Ошибка] Не удалось отправить сообщение клиенту: {e}")
            # Optionally remove the client from the list if sending fails
            clients.remove(client)

    return jsonify(success=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

