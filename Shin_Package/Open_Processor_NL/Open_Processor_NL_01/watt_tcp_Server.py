import socket
from threading import Thread
from Shin_Package.Open_Processor_NL.Open_Processor_NL_01 import sensing

host = '0.0.0.0'
port = 9999

def receive_msg(client_socket, addr):
    while True:
        data = client_socket.recv(1024)
        print("received %s"%data)
        IC_curr_t = sensing.sensing_curr()
        print("\n\t측정데이터")
        print("P\t\tCurr")
        for i in range(10):
            print(str(i + 1) + "\t\t" + str(IC_curr_t[i]))
        client_socket.sendall(str(IC_curr_t[9]).encode())

def server_open():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen()
    print("SERVER OPEN")
    while True:
        print("Wait Client...")
        client_socket, addr = server_socket.accept()

        client_receive_thread = Thread(target=receive_msg, args=(client_socket, addr))
        client_receive_thread.daemon = True
        client_receive_thread.start()
        print("connect by", addr)

    client_socket.close()
    server_socket.close()


if __name__ == '__main__':
    sensing.start_data_center()
    server_open()