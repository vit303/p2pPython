import miniupnpc
import socket
import threading
import sys

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
        print("Проверьте, что вы подключены к основной сети, а не к гостевой или изолированной Wi-Fi.")
        return False

    if devices == 0:
        print("[Ошибка] UPnP-устройства не найдены!")
        print("Возможные причины:")
        print("- UPnP отключён на роутере (включите в настройках роутера)")
        print("- Вы подключены к гостевой или изолированной Wi-Fi сети")
        print("- Ваш ноутбук и роутер в разных подсетях")
        print("- Включена изоляция Wi-Fi клиентов (Client Isolation)")
        print("- Брандмауэр или антивирус блокирует UPnP-трафик")
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

    # Проверяем, есть ли уже проброс на этот порт
    try:
        existing_mapping = upnp.getspecificportmapping(external_port, protocol)
        if existing_mapping:
            print(f"[Инфо] Обнаружено существующее правило для порта {external_port}/{protocol}: {existing_mapping}")
            print("[Инфо] Удаляем существующее правило...")
            try:
                upnp.deleteportmapping(external_port, protocol)
                print("[Успех] Существующее правило удалено.")
            except Exception as e:
                print(f"[Ошибка] Не удалось удалить существующее правило: {e}")
                return False
    except Exception as e:
        # Иногда роутер не поддерживает getspecificportmapping корректно
        print(f"[Предупреждение] Не удалось проверить существующие правила: {e}")

    # Пробуем открыть порт
    try:
        upnp.addportmapping(external_port, protocol, lan_address, internal_port, description, '', 0)
        print(f"[Успех] Порт {external_port} успешно открыт через UPnP.")
    except Exception as e:
        print(f"[Ошибка] Не удалось открыть порт: {e}")
        print("Возможно, UPnP работает только для Ethernet, либо включена изоляция клиентов Wi-Fi.")
        print("Попробуйте:")
        print("- Подключиться к роутеру по кабелю (Ethernet)")
        print("- Временно отключить брандмауэр/антивирус")
        print("- Проверить настройки роутера")
        return False

    # Проверяем, открыт ли порт снаружи
    print("[Инфо] Проверка, открыт ли порт снаружи (по внешнему IP)...")
    if is_port_open(external_ip, int(external_port)):
        print(f"[Успех] Порт {external_port} доступен снаружи!")
    else:
        print(f"[Внимание] Порт {external_port} не доступен снаружи.")
        print("Возможно, провайдер блокирует внешние подключения или UPnP не сработал.")
        print("Проверьте порт на https://2ip.ru/check-port/ или аналогичных сервисах.")
    return True

def start_server(port):
    import socket
    import threading

    def client_handler(client_socket, addr):
        print(f"[Инфо] Подключился клиент: {addr}")

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

        def send_messages():
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

        # Запускаем потоки для приёма и отправки сообщений
        recv_thread = threading.Thread(target=receive_messages, daemon=True)
        send_thread = threading.Thread(target=send_messages, daemon=True)
        recv_thread.start()
        send_thread.start()

        # Ждём завершения потоков (например, при отключении клиента)
        recv_thread.join()
        send_thread.join()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    print(f"[Инфо] Сервер запущен и слушает порт {port}")

    try:
        while True:
            client_socket, addr = server.accept()
            threading.Thread(target=client_handler, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[Инфо] Работа сервера остановлена пользователем.")
    finally:
        server.close()

def main():
    external_port = 15000
    internal_port = 15000
    protocol = 'TCP'
    description = 'Test UPnP port'

    print("=== Диагностика и открытие порта через UPnP ===")
    if open_port(external_port, internal_port, protocol, description):
        print("[Инфо] Запускаем TCP-сервер...")
        start_server(internal_port)
    else:
        print("[Ошибка] Не удалось открыть порт, сервер не запущен.")

if __name__ == "__main__":
    main()

