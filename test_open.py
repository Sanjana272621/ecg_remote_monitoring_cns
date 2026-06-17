import socket



def get_packet(host='192.168.1.39', port=2000):
    buffer = bytearray()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse connection that is established

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()

            print(f"Connection from {client_address}")

            while True:
                data = client_socket.recv(4096)

                if not data:
                    break

                print(f"Received {len(data)} bytes")

            client_socket.close()

    except KeyboardInterrupt:
        print("\nShutting down server.")

    finally:
        server_socket.close()

get_packet()