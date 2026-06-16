import socket
from datetime import datetime 

LOG_FILE = "RecvMonitorData.txt"
packet = ''

def get_packet(host='192.168.1.39', port=2000):

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((host, port))

    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    try:
        while True:

            client_socket, client_address = server_socket.accept()

            print(f"Connection from {client_address}")

            packet = handle_client(client_socket)

            if packet:
                yield packet

    except KeyboardInterrupt:
        print("\nShutting down server.")

    finally:
        server_socket.close()


def handle_client(client_socket):
    buffer = ''

    with client_socket:

        while True:

            data = client_socket.recv(1024)

            if not data:
                print("CONNECTION DISCONNECTED!!!!")
                break

            try:
                
                hl7_message = data.decode('utf-8', errors='ignore')
                
                messages = hl7_message.split('\rMSH')
                #print(messages)

                if (len(messages)) > 1:
                    newmessage = buffer + messages[0]
                    buffer = messages[1]

                else:
                    buffer += messages[0]
                
                #print("START: ", newmessage)
                #print("recieved bytes: ", len(hl7_message))
                #print(repr(hl7_message))
                
                with open(LOG_FILE, "a", encoding="utf-8") as file:
                    if newmessage:
                        #file.write(str(datetime.now())+ "\n")
                        file.write('MSH|^~\\&' + newmessage[5:])
                        file.write("\n")

                if newmessage:
                    return('MSH|^\\&' + newmessage[5:])
                
            except Exception as e:

                print("Decode Error:", e)

