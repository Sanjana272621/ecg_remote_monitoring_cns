import socket
#from packet_extractor import packet_extractor
from .packet_extractor import packet_extractor
packet = ''

def get_packet(host='192.168.1.39', port=2000):
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse connection that is established

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            print("going into while true:")
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            
            buffer = bytearray()
            yield from packet_extractor(client_socket, buffer)
            #yield from handle_client(client_socket, buffer) #yield all 

    except KeyboardInterrupt:
        print("\nShutting down server.")

    finally:
        server_socket.close()

#get_packet()