from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.list import (
    MDList, OneLineAvatarListItem, ImageLeftWidget,
    TwoLineAvatarListItem, ThreeLineAvatarListItem
)
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.behaviors import CommonElevationBehavior
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
import threading
import json
import os
from server import Server
from client import Client
from kivy.metrics import dp


class ChatListItem(OneLineAvatarListItem):
    last_message = StringProperty()
    time = StringProperty()
    unread = NumericProperty(0)
    online = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image = ImageLeftWidget(source="assets/user.png")
        self.add_widget(self.image)
        
        self.bind(on_release=self.open_chat)
    
    def open_chat(self, *args):
        app = MDApp.get_running_app()
        app.root.current = "chat"
        app.root.get_screen("chat").current_chat = self.text


class MessageBubble(MDCard, CommonElevationBehavior):
    text = StringProperty()
    time = StringProperty()
    is_me = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = "250dp"
        self.radius = [15, 15, 15, 15]
        self.md_bg_color = (0.2, 0.5, 0.7, 1) if self.is_me else (0.2, 0.2, 0.2, 1)
        self.orientation = "vertical"
        self.padding = "10dp"
        self.spacing = "5dp"

        self.label = MDLabel(
            text=self.text,
            halign="left",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            markup=True,
            font_style="Body1",
        )
        self.label.bind(
            texture_size=self.update_height
        )
        self.label.text_size = (self.width, None)

        self.add_widget(self.label)

    def update_height(self, instance, value):
        self.height = instance.texture_size[1] + 20  # отступы




class ChatScreen(MDScreen):
    current_chat = StringProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        self.box = MDBoxLayout(orientation="vertical")
        
        # Header
        self.header = MDBoxLayout(size_hint_y=None, height="56dp", md_bg_color=MDApp.get_running_app().theme_cls.primary_color)
        self.back_btn = MDIconButton(icon="arrow-left", on_release=self.go_back)
        self.avatar = ImageLeftWidget(source="assets/user.png", size_hint_x=None, width="40dp")
        self.title = MDLabel(text=self.current_chat, halign="left", size_hint_x=0.7)
        self.header.add_widget(self.back_btn)
        self.header.add_widget(self.avatar)
        self.header.add_widget(self.title)
        
        # Messages area
        self.messages_scroll = ScrollView()
        self.messages_list = MDList(size_hint_y=None)
        self.messages_list.bind(minimum_height=self.messages_list.setter('height'))
        self.messages_scroll.add_widget(self.messages_list)
        
        # Input area
        self.input_box = MDBoxLayout(size_hint_y=None, height="80dp", padding="10dp", spacing="10dp")
        self.attach_btn = MDIconButton(icon="paperclip")
        self.message_input = MDTextField(
    hint_text="Сообщение...",
    mode="fill"
)

        self.send_btn = MDIconButton(icon="send", on_release=self.send_message)
        self.input_box.add_widget(self.attach_btn)
        self.input_box.add_widget(self.message_input)
        self.input_box.add_widget(self.send_btn)
        
        self.box.add_widget(self.header)
        self.box.add_widget(self.messages_scroll)
        self.box.add_widget(self.input_box)
        self.add_widget(self.box)
    
    def go_back(self, *args):
        self.manager.current = "main"
    
    def send_message(self, *args):
        text = self.message_input.text
        if text:
            app = MDApp.get_running_app()
            if self.current_chat == "Server Chat":
                app.send_server_message(text)
            else:
                app.send_client_message(text)
            self.add_message(text, is_me=True)
            self.message_input.text = ""
    
    def add_message(self, text, is_me=False):
        msg = MessageBubble(
        text=text,
        time="12:00",
        is_me=is_me,
    )
        self.messages_list.add_widget(msg)
        Clock.schedule_once(lambda dt: self.messages_scroll.scroll_to(msg))



class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        self.tabs = MDBottomNavigation()
        
        # Chats tab
        self.chats_tab = MDBottomNavigationItem(
            name='chats',
            text='Chats',
            icon='message-text'
        )
        self.chats_list = MDList()
        self.chats_scroll = ScrollView()
        self.chats_scroll.add_widget(self.chats_list)
        self.chats_tab.add_widget(self.chats_scroll)
        
        # Add some demo chats
        server_chat = ChatListItem(text="Server Chat", last_message="Server running", time="12:00")
        client_chat = ChatListItem(text="Client Chat", last_message="Connected", time="11:30")
        self.chats_list.add_widget(server_chat)
        self.chats_list.add_widget(client_chat)
        
        # Contacts tab
        self.contacts_tab = MDBottomNavigationItem(
            name='contacts',
            text='Contacts',
            icon='account-box'
        )
        self.contacts_list = MDList()
        self.contacts_scroll = ScrollView()
        self.contacts_scroll.add_widget(self.contacts_list)
        self.contacts_tab.add_widget(self.contacts_scroll)
        
        # Settings tab
        self.settings_tab = MDBottomNavigationItem(
            name='settings',
            text='Settings',
            icon='cog'
        )
        settings_box = MDBoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        
        # Server settings
        server_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height="150dp",
            padding="20dp",
            spacing="10dp"
        )
        server_card.add_widget(MDLabel(text="Server Settings", font_style="H6"))
        
        self.server_switch = MDCheckbox(size_hint_x=None, width="48dp")
        server_btn_box = MDBoxLayout(spacing="10dp")
        server_btn_box.add_widget(MDLabel(text="Run Server", size_hint_x=0.8))
        server_btn_box.add_widget(self.server_switch)
        server_card.add_widget(server_btn_box)
        
        self.upnp_btn = MDRaisedButton(text="Open UPnP Port", size_hint_y=None, height="48dp")
        server_card.add_widget(self.upnp_btn)
        
        # Client settings
        client_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height="150dp",
            padding="20dp",
            spacing="10dp"
        )
        client_card.add_widget(MDLabel(text="Client Settings", font_style="H6"))
        
        self.ip_input = MDTextField(hint_text="Server IP", mode="fill")
        client_card.add_widget(self.ip_input)
        
        self.connect_btn = MDRaisedButton(text="Connect", size_hint_y=None, height="48dp")
        client_card.add_widget(self.connect_btn)
        
        settings_box.add_widget(server_card)
        settings_box.add_widget(client_card)
        self.settings_tab.add_widget(settings_box)
        
        self.tabs.add_widget(self.chats_tab)
        self.tabs.add_widget(self.contacts_tab)
        self.tabs.add_widget(self.settings_tab)
        
        self.add_widget(self.tabs)
        
        # Bindings
        self.server_switch.bind(active=self.on_server_switch)
        self.upnp_btn.bind(on_release=self.on_upnp_click)
        self.connect_btn.bind(on_release=self.on_connect_click)
    
    def on_server_switch(self, instance, value):
        app = MDApp.get_running_app()
        if value:
            app.start_server()
        else:
            app.stop_server()
    
    def on_upnp_click(self, instance):
        MDApp.get_running_app().open_upnp(instance)
    
    def on_connect_click(self, instance):
        MDApp.get_running_app().toggle_client_connection(instance)


class SocialNetworkApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Blue"
        
        # Load data
        self.load_data()
        
        # Create screen manager
        self.sm = MDScreenManager()
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(ChatScreen(name="chat"))
        
        # Set callbacks
        Server.set_gui_callback(self.update_server_chat)
        Client.set_gui_callback(self.update_client_chat)
        
        return self.sm
    
    def load_data(self):
        """Load contacts and history from JSON."""
        self.contacts = []
        self.history = []
        if os.path.exists("contacts.json"):
            with open("contacts.json", "r") as f:
                self.contacts = json.load(f)
        if os.path.exists("history.json"):
            with open("history.json", "r") as f:
                self.history = json.load(f)
    
    def save_data(self):
        """Save contacts and history."""
        with open("contacts.json", "w") as f:
            json.dump(self.contacts, f)
        with open("history.json", "w") as f:
            json.dump(self.history, f)
    
    def update_server_chat(self, message):
        def update(dt):
            chat_screen = self.sm.get_screen("chat")
            if chat_screen.current_chat == "Server Chat":
                chat_screen.add_message(message, is_me=False)
            self.history.append(message)
            self.save_data()
        Clock.schedule_once(update)
    
    def update_client_chat(self, message):
        def update(dt):
            chat_screen = self.sm.get_screen("chat")
            if chat_screen.current_chat == "Client Chat":
                chat_screen.add_message(message, is_me=False)
            self.history.append(message)
            self.save_data()
        Clock.schedule_once(update)
    
    def start_server(self):
        threading.Thread(target=Server.start_server, args=(15000,), daemon=True).start()
    
    def stop_server(self):
        Server.stop_server()
    
    def open_upnp(self, instance):
        threading.Thread(target=Server.open_port, args=(15000, 15000, 'TCP', 'Chat Server'), daemon=True).start()
    
    def toggle_client_connection(self, instance):
        if Client.running:
            self.disconnect_client()
        else:
            self.connect_client()
    
    def connect_client(self):
        ip = self.sm.get_screen("main").ip_input.text
        if not ip:
            self.update_client_chat("[ERROR] Enter server IP")
            return
            
        self.sm.get_screen("main").connect_btn.text = 'Disconnect'
        threading.Thread(target=Client.start_client, args=(ip, 15000), daemon=True).start()
    
    def disconnect_client(self):
        Client.stop_client()
        self.sm.get_screen("main").connect_btn.text = 'Connect'
    
    def send_server_message(self, message):
        if not Server.running:
            self.update_server_chat("[ERROR] Server not running")
            return
            
        if message:
            Server.broadcast(f"[Server] {message}", ("Server", 0))
            self.update_server_chat(f"[You] {message}")
    
    def send_client_message(self, message):
        if not Client.running:
            self.update_client_chat("[ERROR] Not connected")
            return
            
        if message:
            Client.send_message(message)
            self.update_client_chat(f"[You] {message}")


if __name__ == '__main__':
    SocialNetworkApp().run()