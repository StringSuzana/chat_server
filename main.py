import socket
import select  # OS level IO capability, works with win, linux, ios
from random import getrandbits
from random import randint

HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 5555
UTF_8 = 'utf-8'
ASYMMETRIC_ENCRYPTION_HEADER = 'DIFFIEHELLMAN'
P: int = 0  # p has to be prime nuber = 23
G: int = 0  # g has to be primitive rood modulo g =5


def is_prime(num):
    if num > 1:
        for n in range(2, num):
            if (num % n) == 0:
                return False
        return True
    else:
        return False


def get_random_prime():
    while True:
        n = getrandbits(18)
        if is_prime(n):
            return n


def primitive_root(modulo):
    required_set = set(num for num in range(1, modulo))
    for co_prime_of_modulo in range(1, modulo):
        actual_set = set()
        for power in range(1, modulo):
            actual_set.add(pow(co_prime_of_modulo, power, modulo))
        if required_set == actual_set:
            return co_prime_of_modulo
        else:
            continue


def make_encoded_message(name, content):
    name_header = f"{len(str(name)):<{HEADER_LENGTH}}".encode(UTF_8)
    name_header_data = str(name).encode(UTF_8)
    content_header = f"{len(str(content)):<{HEADER_LENGTH}}".encode(UTF_8)
    content_header_data = str(content).encode(UTF_8)
    return name_header + name_header_data + content_header + content_header_data


def send_p_and_g(client):
    asymmetric_encryption_message = make_encoded_message(ASYMMETRIC_ENCRYPTION_HEADER, ASYMMETRIC_ENCRYPTION_HEADER)
    p_name = 'p'
    g_name = 'g'
    p_message = make_encoded_message(p_name, P)
    g_message = make_encoded_message(g_name, G)

    client.send(asymmetric_encryption_message + p_message + g_message)


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


def make_and_define_p_and_g():
    global P
    P = get_random_prime()
    global G
    G = primitive_root(int(P))  # g has to be primitive rood modulo p =5
    print(f"P: {P}, G: {G}")


if __name__ == '__main__':
    make_and_define_p_and_g()
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
                    f' {client_address[0]}:{client_address[1]} '
                    f'from {user["data"].decode("utf-8")}')
                send_p_and_g(client_socket)
                if len(clients) == 2:  # Ako su dva covjeka u razgovoru
                    for c in clients:
                        if c != notif_sock:
                            c.send(b'16        pub_key_exchange')


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
                        if message["data"] == 'pub_key':
                            pass
                        else:
                            client.send(user["header"] + user["data"] + message["header"] + message["data"])

        for notif_sock in exception_sockets:
            sockets_list.remove(notif_sock)
            del clients[notif_sock]
