import miniupnpc
import socket

class UPNPManager:
    @staticmethod
    def is_port_open(host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                return s.connect_ex((host, port)) == 0
        except Exception as e:
            print(f"[Error] Port check failed: {e}")
            return False

    @staticmethod
    def open_port(external_port, internal_port, protocol='TCP', description='UPnP Port Forwarding'):
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 200
        
        try:
            devices = upnp.discover()
        except Exception as e:
            return False, f"UPnP discovery failed: {e}"
        
        if devices == 0:
            return False, "No UPnP devices found!"
        
        try:
            upnp.selectigd()
        except Exception as e:
            return False, f"Failed to select IGD: {e}"
        
        lan_address = upnp.lanaddr
        external_ip = upnp.externalipaddress()
        
        # Check for existing mapping
        try:
            existing_mapping = upnp.getspecificportmapping(external_port, protocol)
            if existing_mapping:
                try:
                    upnp.deleteportmapping(external_port, protocol)
                except Exception as e:
                    return False, f"Failed to remove existing mapping: {e}"
        except:
            pass
        
        # Add new mapping
        try:
            upnp.addportmapping(external_port, protocol, lan_address, internal_port, description, '', 0)
            return True, f"Port {external_port} opened successfully!\nLocal IP: {lan_address}\nExternal IP: {external_ip}"
        except Exception as e:
            return False, f"Failed to open port: {e}"