import time
import serial
from multiprocessing import Process
import time
import sys

from Shin_Package.Open_Processor_NL.Open_Processor_NL_02 import datas

TIMEOUT = 12
a = 'info_getter_timerstart'

# 주소 : 왼쪽 1, 오른쪽 2, 둘다 3
# 위치 : 최상단으로 부터 이격거리 mm
# 각도 : 2.8 도 단위로 작성

# 1. 하단 리미트 포지션 설정  (주소|L|위치|\n)

# 2. 블라인드 틸트 제어      (주소|A|각도|\n)  //return
# 3. 블라인드 위치 설정      (주소|M|위치|\n) - 틸트각도 변경  //return
# 4. 블라인드 상승          (주소|U|\n)  - 정지 시킬 때 까지 상승
# 5. 블라인드 스텝 상승      (주소|T|스텝|\n) - 1mm 단위로 제어
# 6. 블라인드 하강          (주소|D|\n)  - 정지 시킬 때 까지 하강
# 7. 블라인드 스텝 하강      (주소|B|스텝|\n) - 1mm 단위로 제어
# 8. 이동중 정지            (주소|S|\n)

# 9. 저장된 데이터 로드      (주소|R|\n) - 현재 포지션, 틸트각도*10 ,하단 리미트 ,엔코더 \\ 주소는 필히 1,2로만 사용  //return
# 10.블라인드 위치 설정(2)   (주소|K|위치|\n) - 틸트각도 고정.  //return
# 11.블라인드 위치 설정 후 틸트 동작 수행 (주소|G|위치|;|각도|\n)  //return

def connect_serial():
    return
    datas.blind_serial = serial.Serial(port="COM1", baudrate=9600)
    print("Serial Connect Complete")


def cmd_blind(number, cmd):
    test = serial.Serial(port="COM1", baudrate=9600)
    # test.write("2A-70\n".encode())
    send_msg = '%s%s\n' % (number, cmd)
    print("COMMAND BLIND : %s" % send_msg, end='')
    test.write(send_msg.encode())
    result = test.readline()
    test.close()

    return result


def control_blind(number, cmd, value):
    test = serial.Serial(port="COM1", baudrate=9600)
    # test.write("2A-70\n".encode())
    send_msg = '%s%s%s\n' % (number, cmd, value)
    print("CONTROL BLIND : %s" % send_msg, end='')
    test.write(send_msg.encode())
    test.close()


def get_blind_info(a):
    print(cmd_blind('1', 'R').decode(), end='')
    print(cmd_blind('2', 'R').decode(), end='')

def getter_timeout_wrapped():
    actionProcess = Process(target=get_blind_info, args=(a, ))
    actionProcess.start()
    actionProcess.join(timeout=TIMEOUT)
    actionProcess.terminate()

# if __name__ == "__main__":
#     TIMEOUT = 10
#     a = 'info_getter_timerstart'
#     actionProcess = Process(target=get_blind_info, args=(a, ))
#     actionProcess.start()
#     actionProcess.join(timeout=TIMEOUT)
#     actionProcess.terminate()


def blind_open():
    if datas.blind_deg < 0:
        datas.blind_deg = datas.blind_deg + (2.8 * datas.blind_accel)
        if datas.blind_deg >= 0:
            datas.blind_deg = 0

        print("BLIND OPEN(+2.8*%s degree)"%datas.blind_accel)
        # control_blind('1', 'A', '-70')
        # time.sleep(0.3)
        # control_blind('2', 'A', '-70')
        # time.sleep(0.3)
        #
        # blind_state = cmd_blind('2', 'R').decode()
        # time.sleep(0.3)
        # print(blind_state)

        init_blind()

        control_blind('1', 'A', str(datas.blind_deg))
        control_blind('2', 'A', str(datas.blind_deg))
        getter_timeout_wrapped()
        # print(cmd_blind('1', 'R').decode(), end='')
        # print(cmd_blind('2', 'R').decode(), end='')

        datas.cal_times = 0
        print("BLIND CONTROL RESULT : %s" % (datas.blind_deg))
    else:
        getter_timeout_wrapped()
        # print(cmd_blind('1', 'R').decode(), end='')
        # print(cmd_blind('2', 'R').decode(), end='')
        print("BLIND DEGREE IS MAX OPEN, BLIND LOCK. (%s)"%(datas.blind_deg))
        datas.blind_lock = datas.blind_lock_step
        # datas.blind_lock = True


def blind_close():
    datas.can_control = True
    datas.blind_lock = datas.blind_lock_step
    print("Blind is OpenLock. Cause Blind is Close")
    if datas.blind_deg == -70:
        getter_timeout_wrapped()
        # print(cmd_blind('1', 'R').decode(), end='')
        # print(cmd_blind('2', 'R').decode(), end='')
        print("BLIND DEGREE MIN, AND MIN LED. CHECK POINT.")
    else:
        control_deg = datas.blind_deg - (2.8 * datas.blind_accel)
        if control_deg < -70:
            control_deg = -70

        print("BLIND CLOSE(-2.8*%s degree)"%datas.blind_accel)
        # control_blind('1', 'A', '-70')
        # time.sleep(0.3)
        # control_blind('2', 'A', '-70')
        # time.sleep(0.3)
        #
        # blind_state = cmd_blind('2', 'R').decode()
        # time.sleep(0.3)
        # print(blind_state)
        init_blind()

        control_blind('1', 'A', str(control_deg))
        control_blind('2', 'A', str(control_deg))
        getter_timeout_wrapped()
        # print(cmd_blind('1', 'R').decode(), end='')
        # print(cmd_blind('2', 'R').decode(), end='')

        datas.cal_times = 0
        datas.blind_deg = control_deg


def init_blind():
    # control_blind('1', 'M', str(datas.blind_init_position))
    # control_blind('2', 'M', str(datas.blind_init_position))
    # print(cmd_blind('1', 'R').decode(), end='')
    # print(cmd_blind('2', 'R').decode(), end='')
    control_blind('1', 'A', str(datas.blind_init_deg))
    control_blind('2', 'A', str(datas.blind_init_deg))
    getter_timeout_wrapped()
    # print(cmd_blind('1', 'R').decode(), end='')
    # print(cmd_blind('2', 'R').decode(), end='')
    print("======================INIT_BLIND===========================")

def init_blind_first():
    control_blind('1', 'M', str(datas.blind_init_position))
    control_blind('2', 'M', str(datas.blind_init_position))
    # control_blind('1', 'M', str(1000))
    # control_blind('2', 'M', str(1000))
    getter_timeout_wrapped()
    # print(cmd_blind('1', 'R').decode(), end='')
    # print(cmd_blind('2', 'R').decode(), end='')
    control_blind('1', 'A', str(datas.blind_init_deg))
    control_blind('2', 'A', str(datas.blind_init_deg))
    # control_blind('2', 'A', str(70))
    # control_blind('1', 'A', str(70))
    getter_timeout_wrapped()
    # print(cmd_blind('1', 'R').decode(), end='')
    # print(cmd_blind('2', 'R').decode(), end='')
    print("======================FIRST_INIT_BLIND===========================")


def init_blind2():
    data = cmd_blind('1', 'R').decode()
    print(data, end='')
    print('position', data[0:4], ", ", abs(int(data[0:4]) - (datas.blind_position)), ", ",
          abs(int(data[0:4]) >= (datas.blind_position)) > 5)
    if abs(int(data[0:4]) - (datas.blind_position)) > 5:
        control_blind('1', 'M', str(datas.blind_position))
        print(cmd_blind('1', 'R').decode(), end='')
    print('deg', data[5:8])
    if (int(data[5:8]) >= (datas.blind_deg * 10)):
        control_blind('1', 'A', str(datas.blind_deg))
        print(cmd_blind('1', 'R').decode(), end='')

    print("=================================================")

    data = cmd_blind('2', 'R').decode()
    print(data, end='')
    print('position', data[0:4], ", ", (datas.blind_position - 5))
    if abs(int(data[0:4]) - (datas.blind_position)) > 5:
        control_blind('2', 'M', str(datas.blind_position))
        print(cmd_blind('2', 'R').decode(), end='')
    print('deg', data[5:8])
    if int(data[5:8]) >= (datas.blind_deg * 10):
        control_blind('2', 'A', str(datas.blind_deg))
        print(cmd_blind('2', 'R').decode(), end='')


if __name__ == '__main__':
    connect_serial()
    init_blind_first()

    # data = cmd_blind('1', 'R').decode()
    # print(data)

    # control_blind('1', 'M', '1305')
    # data = cmd_blind('1', 'R').decode()
    # control_blind('2', 'M', '1305')
    # data = cmd_blind('2', 'R').decode()

    # control_blind('1', 'A', '-70')
    # time.sleep(0.3)
    # data = cmd_blind('1', 'R').decode()
    # print(data)
    # control_blind('2', 'A', '-70')
    # time.sleep(0.3)
    # data = cmd_blind('2', 'R').decode()
    # print(data)
    # time.sleep(0.3)
    #
    # control_blind('1', 'A', '-61')
    # time.sleep(0.3)
    # control_blind('2', 'A', '-61')
    # time.sleep(0.3)
    # data = cmd_blind('2', 'R').decode()
    # print(data)
    # time.sleep(0.3)
    # control_blind('2', 'A', '-40')
    # data = cmd_blind('2', 'R').decode()
    # print(data)
    # control_blind('1', 'L', '1519')
    # data = cmd_blind('2', 'R').decode()
    # print(data)
