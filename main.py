import socket
import select  # OS level IO capability, works with win, linux, ios

HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 5555


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        print(f'message_length {message_length}')
        return {"header": message_header,
                'data': client_socket.recv(message_length)}  # Kaj ako netko posalje jako veliku poruku?
    except:
        return False


if __name__ == '__main__':
    # AF Address Family INET internet
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((IP, PORT))
    server_socket.listen(100)  # listens for 100 active connections.

    sockets_list = [server_socket]  # Later, here come the clients

    clients = {}

    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [],
                                                           sockets_list)  # read_from , write_in, error_on
        for notif_sock in read_sockets:
            if notif_sock == server_socket:

                client_socket, client_address = server_socket.accept()
                user = receive_message(client_socket)
                if user is False:
                    continue
                sockets_list.append(client_socket)
                clients[client_socket] = user
                print(
                    f'Accepted new connection'
                    f' {client_address[0]} : {client_address[1]} '
                    f'from {user["data"].decode("utf-8")}')
            else:
                message = receive_message(notif_sock)
                if message is False:
                    print(f"Closed connection from {clients[notif_sock]['data'].decode('utf-8')}")
                    sockets_list.remove(notif_sock)
                    del clients[notif_sock]
                    continue
                user = clients[notif_sock]
                print(f'Received message from {user["data"].decode("utf-8")}, '
                      f'message: {message["data"].decode("utf-8")}')
                for client in clients:
                    if client != notif_sock:
                        # user.header = len(user.data),
                        # user.data = username,
                        # message.header = len(message.data),
                        # message.data = message content
                        client.send(user["header"] + user["data"] + message["header"] + message["data"])

        for notif_sock in exception_sockets:
            sockets_list.remove(notif_sock)
            del clients[notif_sock]
