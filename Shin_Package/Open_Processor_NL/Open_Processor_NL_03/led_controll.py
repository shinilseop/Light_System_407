# LED 제어, DB에 누적
import socket
import threading
import time
import numpy as np

global LED_state
LED_state = np.zeros((30,5))
global flag

def __init__():
    global flag
    flag = False

def re_ack(sock):
    global flag
    try:
        recvMsg, addr = sock.recvfrom(500)
        # print(recvMsg)
        flag = True

    except:
        return 0


def set_LED(num, ch1, ch2, ch3, ch4):
    global LED_state
    global flag
    flag = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = "AT+CONTROL=FLAT_PWM,A,%d,%d,%d,%d,%d\r\n" % (num, ch1, ch2, ch3, ch4)
    # LED_state[num-1] = [num, ch1, ch2, ch3, ch4]
    # print(LED_state[num-1])
    while True:
        sock.sendto(msg.encode(), ("192.168.100.210", 50210))
        api = threading.Thread(target=re_ack, args=(sock,))
        api.daemon = True
        api.start()
        time.sleep(0.3)

        if flag:
            LED_state[num-1] = [num, ch1, ch2, ch3, ch4]
            # print(str(num) + "번 완료\n")
            break
    sock.close()

def all_set_LED(ch1, ch2, ch3, ch4):
    global flag
    global LED_state

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(1,31):
        # print(i)
        flag = False
        msg = "AT+CONTROL=FLAT_PWM,A,%d,%d,%d,%d,%d\r\n" % (i, ch1, ch2, ch3, ch4)
        # print(LED_state[i-1])
        # sock.sendto(msg.encode(), ("192.168.100.210", 50210))

        while True:
            sock.sendto(msg.encode(), ("192.168.100.210", 50210))
            api = threading.Thread(target=re_ack, args=(sock,))
            api.daemon = True
            api.start()
            time.sleep(0.3)


            if flag:
                LED_state[i - 1] = [i, ch1, ch2, ch3, ch4]
                # print(str(i) + "번 완료\n")
                break

    sock.close()

def get_LED_state():
    global LED_state
    return LED_state

if __name__ == '__main__':
    all_set_LED(0,0,0,0)
    # for i in range(30):
    # set_LED(1, 0, 0, 0, 0)
    # set_LED(2, 0, 0, 0, 0)
    # set_LED(3, 0, 0, 0, 0)
    # set_LED(4, 0, 0, 0, 0)
    # set_LED(5, 0, 0, 0, 0)
    # set_LED(6, 0, 0, 0, 0)
