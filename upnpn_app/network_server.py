
import socket
import threading

class NetworkServer:
    def __init__(self, port=7777, on_message_callback=None):  # Установим порт по умолчанию
        self.port = port
        self.on_message_callback = on_message_callback
        self.server_socket = None
        self.running = False
        self.clients = []
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        self.running = True
        
        threading.Thread(target=self._accept_connections, daemon=True).start()
        return True

    def _accept_connections(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_handler.start()
                self.clients.append((client_socket, addr))
                if self.on_message_callback:
                    self.on_message_callback(f"Client connected: {addr}")
            except:
                break

    def _handle_client(self, client_socket, addr):
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8', errors='ignore')
                if self.on_message_callback:
                    self.on_message_callback(f"From {addr}: {message}")
        except:
            pass
        finally:
            client_socket.close()
            if (client_socket, addr) in self.clients:
                self.clients.remove((client_socket, addr))
            if self.on_message_callback:
                self.on_message_callback(f"Client disconnected: {addr}")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client, _ in self.clients:
            client.close()
        self.clients = []

    def send_to_all(self, message):
        for client, _ in self.clients:
            try:
                client.sendall(message.encode('utf-8'))
            except:
                pass