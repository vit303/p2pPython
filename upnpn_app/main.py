from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.lang import Builder

from upnp_manager import UPNPManager
from network_server import NetworkServer
from network_client import NetworkClient

Builder.load_file('upnp_app.kv')

class MainScreen(Screen):
    server_running = BooleanProperty(False)
    client_connected = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        # Инициализируем сервер с портом по умолчанию
        self.server = NetworkServer(on_message_callback=self.update_server_log)
        self.client = NetworkClient(on_message_callback=self.update_client_log)
        self.server_running = False
        self.client_connected = False
    
    def update_upnp_status(self, message):
        self.ids.upnp_status.text += f"\n{message}"
    
    def update_server_log(self, message):
        self.ids.server_log.text += f"\n{message}"
    
    def update_client_log(self, message):
        self.ids.client_log.text += f"\n{message}"
    
    def open_port(self):
        try:
            external_port = int(self.ids.external_port.text)
            internal_port = int(self.ids.internal_port.text)
        except ValueError:
            self.update_upnp_status("Invalid port number!")
            return
        
        success, message = UPNPManager.open_port(external_port, internal_port)
        self.update_upnp_status(message)
    
    def toggle_server(self):
        if self.server_running:
            self.server.stop()
            self.ids.start_server_btn.text = "Start Server"
            self.server_running = False
            self.update_server_log("Server stopped")
        else:
            try:
                port = int(self.ids.server_port.text)
                self.server.port = port  # Обновляем порт перед запуском
                if self.server.start():
                    self.ids.start_server_btn.text = "Stop Server"
                    self.server_running = True
                    self.update_server_log(f"Server started on port {port}")
            except ValueError:
                self.update_server_log("Invalid port number!")
        
    def send_server_message(self):
        if not self.server_running:
            self.update_server_log("Server is not running!")
            return
        
        message = self.ids.server_message.text
        if message:
            self.server.send_to_all(message)
            self.update_server_log(f"You: {message}")
            self.ids.server_message.text = ""
    
    def toggle_client(self):
        if self.client_connected:
            self.client.disconnect()
            self.ids.connect_btn.text = "Connect"
            self.client_connected = False
            self.update_client_log("Disconnected from server")
        else:
            server_ip = self.ids.server_ip.text
            if not server_ip:
                self.update_client_log("Please enter server IP!")
                return
            
            try:
                port = int(self.ids.client_port.text)
            except ValueError:
                self.update_client_log("Invalid port number!")
                return
            
            success, message = self.client.connect(server_ip, port)
            self.update_client_log(message)
            if success:
                self.ids.connect_btn.text = "Disconnect"
                self.client_connected = True
    
    def send_client_message(self):
        if not self.client_connected:
            self.update_client_log("Not connected to server!")
            return
        
        message = self.ids.client_message.text
        if message:
            if self.client.send_message(message):
                self.update_client_log(f"You: {message}")
                self.ids.client_message.text = ""
            else:
                self.update_client_log("Failed to send message")

class UPnPApp(App):
    def build(self):
        self.title = 'UPnP Port Forwarding & Network Tools'
        return MainScreen()

if __name__ == '__main__':
    UPnPApp().run()