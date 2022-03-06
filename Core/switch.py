# socket module import!
import socket
import time

def onnoff():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("192.168.100.26", 5000))

    # 0은 릴레이 off, 1은 릴레이 0N
    test_msg = "0"
    sock.send(test_msg.encode())

    time.sleep(5)
    test_msg = "1"
    sock.send(test_msg.encode())
    sock.send(test_msg.encode())
    sock.send(test_msg.encode())
    #
    sock.close()


if __name__ == '__main__':
    onnoff()
