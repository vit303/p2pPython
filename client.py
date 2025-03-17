import socket

def start_client(server_ip, port):
    """Starts the client to connect to the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, port))  # Connect to the server
        print(f'Connected to server at {server_ip}:{port}')

        while True:
            message = input("Enter message (or 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Exiting chat.")
                break
            client_socket.sendall(message.encode())  # Send message to server
            response = client_socket.recv(1024)  # Wait for response from server
            print(f'Received from server: {response.decode()}')

if __name__ == '__main__':
    server_ip = input("Enter the server IP address: ")  # Get server IP address from user
    port = 8080  # Port must match the server's port
    start_client(server_ip, port)
