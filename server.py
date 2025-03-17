import miniupnpc
import socket
import threading

def is_port_open(host, port):
    """Checks if the specified port is open on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)  # Set timeout
        return s.connect_ex((host, port)) == 0

def open_port(external_port, internal_port, protocol='TCP', description='My Port Forwarding'):
    # Initialize UPnP
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200  # Delay for device discovery
    upnp.discover()  # Search for UPnP devices
    upnp.selectigd()  # Select the first found IGD

    # Get local address
    lan_address = upnp.lanaddr
    print(f'Local address: {lan_address}')

    # Check if the port is open
    if is_port_open(lan_address, int(external_port)):
        print(f'Port {external_port} is already open.')
    else:
        # Open the port
        try:
            upnp.addportmapping(external_port, protocol, lan_address, internal_port, description, '', 0)
            print(f'Port {external_port} successfully opened')
        except Exception as e:
            print(f'Error opening port: {e}')

def start_server(port):
    """Starts the server to wait for incoming connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('', port))  # Bind server to port
        server_socket.listen()  # Start listening
        print(f'Server started. Waiting for connections on port {port}...')

        while True:
            client_socket, addr = server_socket.accept()  # Wait for a connection
            with client_socket:
                print(f'Connected to {addr}')
                while True:
                    message = client_socket.recv(1024)  # Receive message from client
                    if not message:
                        print(f'Client {addr} disconnected.')
                        break
                    received_message = message.decode()
                    print(f'Received from client: {received_message}')
                    
                    response = input()
                    
                    client_socket.sendall(response.encode())  # Send response back to client

if __name__ == '__main__':
    external_port = 8080
    internal_port = 8080

    open_port(external_port, internal_port)

    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(internal_port,))
    server_thread.start()
