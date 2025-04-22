from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
from server import Server
from client import Client

class ChatApp(App):
    def build(self):
        self.root = TabbedPanel()
        
        # Server Tab
        server_tab = BoxLayout(orientation='vertical')
        
        # Chat output
        self.server_chat = ScrollView()
        self.server_label = Label(size_hint_y=None, text_size=(None, None))
        self.server_label.bind(texture_size=self.server_label.setter('size'))
        self.server_chat.add_widget(self.server_label)
        server_tab.add_widget(self.server_chat)
        
        # Server controls
        server_controls = BoxLayout(size_hint_y=0.15)
        self.server_msg_input = TextInput(hint_text='Type message...', multiline=False)
        self.server_send_btn = Button(text='Send', size_hint_x=0.3)
        self.server_send_btn.bind(on_press=self.send_server_message)
        server_controls.add_widget(self.server_msg_input)
        server_controls.add_widget(self.server_send_btn)
        server_tab.add_widget(server_controls)
        
        # Server management
        server_manage = BoxLayout(size_hint_y=0.15)
        self.start_btn = Button(text='Start Server')
        self.start_btn.bind(on_press=self.toggle_server)
        self.upnp_btn = Button(text='Open UPnP Port')
        self.upnp_btn.bind(on_press=self.open_upnp)
        server_manage.add_widget(self.start_btn)
        server_manage.add_widget(self.upnp_btn)
        server_tab.add_widget(server_manage)
        
        self.root.add_widget(TabbedPanelItem(text='Server', content=server_tab))
        
        # Client Tab
        client_tab = BoxLayout(orientation='vertical')
        
        # Chat output
        self.client_chat = ScrollView()
        self.client_label = Label(size_hint_y=None, text_size=(None, None))
        self.client_label.bind(texture_size=self.client_label.setter('size'))
        self.client_chat.add_widget(self.client_label)
        client_tab.add_widget(self.client_chat)
        
        # Client controls
        client_controls = BoxLayout(size_hint_y=0.15)
        self.client_msg_input = TextInput(hint_text='Type message...', multiline=False)
        self.client_send_btn = Button(text='Send', size_hint_x=0.3)
        self.client_send_btn.bind(on_press=self.send_client_message)
        client_controls.add_widget(self.client_msg_input)
        client_controls.add_widget(self.client_send_btn)
        client_tab.add_widget(client_controls)
        
        # Connection
        conn_layout = BoxLayout(size_hint_y=0.15)
        self.ip_input = TextInput(hint_text='Server IP', multiline=False)
        self.connect_btn = Button(text='Connect', size_hint_x=0.3)
        self.connect_btn.bind(on_press=self.toggle_client_connection)
        conn_layout.add_widget(self.ip_input)
        conn_layout.add_widget(self.connect_btn)
        client_tab.add_widget(conn_layout)
        
        self.root.add_widget(TabbedPanelItem(text='Client', content=client_tab))
        
        # Setup callbacks
        Server.set_gui_callback(self.update_server_chat)
        Client.set_gui_callback(self.update_client_chat)
        
        return self.root

    def update_server_chat(self, message):
        def update(dt):
            self.server_label.text += f"\n{message}"
            self.server_chat.scroll_y = 0
        Clock.schedule_once(update)

    def update_client_chat(self, message):
        def update(dt):
            self.client_label.text += f"\n{message}"
            self.client_chat.scroll_y = 0
        Clock.schedule_once(update)

    def toggle_server(self, instance):
        if Server.running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        self.start_btn.text = 'Stop Server'
        threading.Thread(target=Server.start_server, args=(15000,), daemon=True).start()

    def stop_server(self):
        Server.stop_server()
        self.start_btn.text = 'Start Server'

    def open_upnp(self, instance):
        threading.Thread(target=Server.open_port, args=(15000, 15000, 'TCP', 'Chat Server'), daemon=True).start()

    def toggle_client_connection(self, instance):
        if Client.running:
            self.disconnect_client()
        else:
            self.connect_client()

    def connect_client(self):
        ip = self.ip_input.text
        if not ip:
            self.update_client_chat("[ERROR] Enter server IP")
            return
            
        self.connect_btn.text = 'Disconnect'
        threading.Thread(target=Client.start_client, args=(ip, 15000), daemon=True).start()

    def disconnect_client(self):
        Client.stop_client()
        self.connect_btn.text = 'Connect'

    def send_server_message(self, instance):
        if not Server.running:
            self.update_server_chat("[ERROR] Server not running")
            return
            
        msg = self.server_msg_input.text
        if msg:
            Server.broadcast(f"[Server] {msg}", ("Server", 0))
            self.update_server_chat(f"[You] {msg}")
            self.server_msg_input.text = ''

    def send_client_message(self, instance):
        if not Client.running:
            self.update_client_chat("[ERROR] Not connected")
            return
            
        msg = self.client_msg_input.text
        if msg:
            Client.send_message(msg)
            self.update_client_chat(f"[You] {msg}")
            self.client_msg_input.text = ''

if __name__ == '__main__':
    ChatApp().run()