# LED 제어, DB에 누적
import socket
import time
import numpy as np

global LED_state
LED_state = np.zeros((30,5))

def set_LED(num, ch1, ch2, ch3, ch4):
    global LED_state
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = "AT+CONTROL=FLAT_PWM,A,%d,%d,%d,%d,%d\r\n" % (num, ch1, ch2, ch3, ch4)
    LED_state[num-1] = [num, ch1, ch2, ch3, ch4]
    # print(LED_state[num-1])
    sock.sendto(msg.encode(), ("192.168.100.210", 50210))
    time.sleep(0.1)
    sock.sendto(msg.encode(), ("192.168.100.210", 50210))
    sock.close()

def all_set_LED(ch1, ch2, ch3, ch4):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(1,31):
        msg = "AT+CONTROL=FLAT_PWM,A,%d,%d,%d,%d,%d\r\n" % (i, ch1, ch2, ch3, ch4)
        LED_state[i-1] = [i, ch1, ch2, ch3, ch4]
        # print(LED_state[i-1])
        sock.sendto(msg.encode(), ("192.168.100.210", 50210))
        time.sleep(0.1)
        sock.sendto(msg.encode(), ("192.168.100.210", 50210))
        time.sleep(0.1)
        sock.sendto(msg.encode(), ("192.168.100.210", 50210))

    sock.close()


if __name__ == '__main__':
    # all_set_LED(0,100,0,0)
    # set_LED(6, 0, 0, 0, 0)
    for i in range(30):
        set_LED(i, 255, 0, 0, 0)
