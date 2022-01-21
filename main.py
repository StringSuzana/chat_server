import socket
import select
from random import getrandbits
from time import sleep

HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 5555
UTF_8 = 'utf-8'
ASYMMETRIC_ENCRYPTION_HEADER = 'DIFFIEHELLMAN'

"""
- P has to be prime nuber (i.e. 23) To ensure security, it is recommended that P is at least 2048 bits long:
https://en.wikipedia.org/wiki/Logjam_(computer_security)
=> TLDR: Most of the servers used to use precomputed p and g. And they reused them very often.

- G has to be primitive rood modulo p (i.e. 5)
"""
P: int = 0
G: int = 0


def make_and_define_p_and_g():
    global P
    # Even this is not secure enough: *** !!! ***
    #P = 523276359721148582961119532877840338939233252222644577622862528354240605322418224344246000862830949201226342187945243756720766842987724933927624612802819
    P = get_random_prime()
    global G
    G = primitive_root(int(P))
    print(f"P: {P}, G: {G}")


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
        """
         22 bits are the most I can get in reasonable amount of 
         time, at least with current method of checking if number is prime
         """
        n = getrandbits(20)
        if is_prime(n):
            return n


def primitive_root(modulo):
    required_set = set(num for num in range(1, modulo)) # [1, (modulo-1)]
    for co_prime_of_modulo in range(1, modulo):
        actual_set = set()
        for power in range(1, modulo):
            #Here set is used so that only unique numbers should fall in
            actual_set.add(pow(co_prime_of_modulo, power, modulo)) # co_prime_of_modulo ^ power % modulo
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
        return {"header": message_header,
                'data': client_socket.recv(message_length)}
    except:
        return False


if __name__ == '__main__':

    make_and_define_p_and_g()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((IP, PORT))
    server_socket.listen(10)

    sockets_list = [server_socket]

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
                    f'from {user["data"].decode(UTF_8)}')
                send_p_and_g(client_socket)
                if len(clients) == 2:  # Two people connected
                    for c in clients:
                        sleep(1)
                        print(f'Send pub_key_exchange flag to client {clients[c]["data"].decode(UTF_8)}')
                        c.send(b'16        pub_key_exchange')  # 10 places in header


            else:
                message = receive_message(notif_sock)
                if message is False:
                    print(f"Closed connection from {clients[notif_sock]['data'].decode(UTF_8)}")
                    sockets_list.remove(notif_sock)
                    del clients[notif_sock]
                    continue
                user = clients[notif_sock]
                print(f'Received message from {user["data"].decode(UTF_8)}, '
                      f'message: {message["data"].decode(UTF_8)}')
                for client in clients:
                    if (client != notif_sock) & (message["data"] == b'pub_key'):  # pub key exchange
                        pub_key_message = receive_message(notif_sock)
                        print(f'Sending message from {user["data"].decode(UTF_8)}, '
                              f' flag: {message["data"].decode(UTF_8)}'
                              f' and public key:  {pub_key_message["data"].decode(UTF_8)}')
                        client.send(
                            user["header"] + user["data"] + message["header"] + message["data"] +
                            user["header"] + user["data"] + pub_key_message["header"] + pub_key_message["data"])
                    elif (client != notif_sock) & (message["data"] != b'pub_key'):  # regular messages
                        client.send(user["header"] + user["data"] + message["header"] + message["data"])

        for notif_sock in exception_sockets:
            sockets_list.remove(notif_sock)
            del clients[notif_sock]
