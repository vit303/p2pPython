import socket
import threading

class NetworkClient:
    def __init__(self, on_message_callback=None):
        self.client_socket = None
        self.on_message_callback = on_message_callback
        self.running = False

    def connect(self, server_ip, port):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, port))
            self.running = True
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True, "Connected successfully!"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def _receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8', errors='ignore')
                if self.on_message_callback:
                    self.on_message_callback(f"Server: {message}")
            except:
                break

    def send_message(self, message):
        if self.client_socket and self.running:
            try:
                self.client_socket.sendall(message.encode('utf-8'))
                return True
            except:
                return False
        return False

    def disconnect(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()