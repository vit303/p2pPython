import miniupnpc
import socket
import threading

class Server:
    client_sockets = []
    server_socket = None
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
    def is_port_open(cls, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                return s.connect_ex((host, port)) == 0
        except Exception as e:
            cls.log_message(f"[Error] Port check failed: {e}")
            return False

    @classmethod
    def open_port(cls, external_port, internal_port, protocol='TCP', description='Chat Server'):
        cls.log_message("Searching for UPnP devices...")
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 200
        
        try:
            devices = upnp.discover()
            if devices == 0:
                cls.log_message("[Error] No UPnP devices found!")
                return False
                
            upnp.selectigd()
            lan_address = upnp.lanaddr
            external_ip = upnp.externalipaddress()
            cls.log_message(f"[Info] Local IP: {lan_address}")
            cls.log_message(f"[Info] External IP: {external_ip}")

            try:
                existing_mapping = upnp.getspecificportmapping(external_port, protocol)
                if existing_mapping:
                    cls.log_message(f"[Info] Existing mapping found for port {external_port}")
                    try:
                        upnp.deleteportmapping(external_port, protocol)
                        cls.log_message("[Success] Removed existing mapping")
                    except Exception as e:
                        cls.log_message(f"[Error] Failed to remove mapping: {e}")
                        return False
            except Exception as e:
                cls.log_message(f"[Warning] Could not check existing mappings: {e}")

            upnp.addportmapping(external_port, protocol, lan_address, internal_port, description, '', 0)
            cls.log_message(f"[Success] Port {external_port} opened via UPnP")
            return True
            
        except Exception as e:
            cls.log_message(f"[Error] UPnP failed: {e}")
            return False

    @classmethod
    def start_server(cls, port):
        cls.running = True
        cls.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.server_socket.bind(('', port))
        cls.server_socket.listen(5)
        cls.log_message(f"[Server] Listening on port {port}")

        try:
            while cls.running:
                client_socket, addr = cls.server_socket.accept()
                cls.log_message(f"[Server] New connection from {addr[0]}")
                cls.client_sockets.append(client_socket)
                threading.Thread(target=cls.handle_client, args=(client_socket, addr), daemon=True).start()
        except Exception as e:
            if cls.running:
                cls.log_message(f"[Server] Error: {e}")
        finally:
            cls.stop_server()

    @classmethod
    def handle_client(cls, client_socket, addr):
        try:
            while cls.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8', errors='ignore')
                cls.log_message(f"[Client {addr[0]}] {message}")
                cls.broadcast(message, addr)
        except Exception as e:
            cls.log_message(f"[Server] Client error: {e}")
        finally:
            client_socket.close()
            if client_socket in cls.client_sockets:
                cls.client_sockets.remove(client_socket)
            cls.log_message(f"[Server] Client {addr[0]} disconnected")

    @classmethod
    def broadcast(cls, message, sender_addr):
        for client in cls.client_sockets:
            try:
                client.sendall(f"[Server] {message}".encode('utf-8'))
            except Exception as e:
                cls.log_message(f"[Server] Broadcast error: {e}")

    @classmethod
    def stop_server(cls):
        cls.running = False
        if cls.server_socket:
            cls.server_socket.close()
        for client in cls.client_sockets:
            client.close()
        cls.client_sockets = []
        cls.log_message("[Server] Server stopped")