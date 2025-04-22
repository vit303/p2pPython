import socket
import threading

class Client:
    client_socket = None
    running = False
    gui_callback = None

    @classmethod
    def set_gui_callback(cls, callback):
        cls.gui_callback = callback

    @classmethod
    def log_message(cls, message):
        if cls.gui_callback:
            cls.gui_callback(message)
        print(message)

    @classmethod
    def start_client(cls, server_ip, port):
        cls.running = True
        cls.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            cls.client_socket.connect((server_ip, port))
            cls.log_message(f"[Client] Connected to {server_ip}:{port}")
            
            while cls.running:
                data = cls.client_socket.recv(1024)
                if not data:
                    break
                cls.log_message(data.decode('utf-8', errors='ignore'))
        except Exception as e:
            cls.log_message(f"[Client] Error: {e}")
        finally:
            cls.stop_client()

    @classmethod
    def send_message(cls, message):
        if cls.client_socket and cls.running:
            try:
                cls.client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                cls.log_message(f"[Client] Send error: {e}")
                cls.stop_client()

    @classmethod
    def stop_client(cls):
        cls.running = False
        if cls.client_socket:
            cls.client_socket.close()
            cls.client_socket = None
        cls.log_message("[Client] Disconnected")