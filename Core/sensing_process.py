# 1분에 한번씩 모든 센서값들을 취합해서 각자의 DB로 삽입하도록 함.
# 그리고 그거 취합한걸로 uniformity 작성해서 db 삽입
import socket
from Core.Intsain_Illum import II
from Core.Intsain_Curr import IC
import threading, time

def get_intsain():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("192.168.100.213", 50213))
    II1 = II.getInstance()
    IC1 = IC.getInstance()
    while True:
        msg = "AT+PRINT=SENSOR_DATA\r\n"
        sock.sendto(msg.encode(), ("192.168.100.213", 50213))
        # print("보냄!")
        total_data = ""
        for i in range(4):
            recvMsg, addr = sock.recvfrom(500)
            # print(type(recvMsg))
            # print(sys.getsizeof(recvMsg))
            data = recvMsg.decode()
            data.replace("\r\n", "")
            total_data = total_data + data
            # print(len(data))
        # total_data.replace(",","")
        # print(total_data)
        temp = total_data.split("data:[")
        temp = temp[1].split("]")
        # print(temp[0])
        temp = temp[0].split("},")

        for i in range(9):
            illum = temp[i].split(",")[3].split(":")[1].replace('"', "")
            II1.set_illum_data(i, illum)

        for i in range(9, 19):
            curr = temp[i].split(",")[3].split(":")[1].replace('"', "")
            IC1.set_curr_data(i - 9, curr)
        time.sleep(3)

    sock.close()

def get_Uniformity():
    # 최소조도, 종합조도, 평균조도, 균제도, 평균 색온도, 총전력량, 평균 전력량
    # 개별 조도, 개별 색온도, 개별 전력량
    # gui로 색과 표를 만들기
    return 1

if __name__ == '__main__':
    auto_get = threading.Thread(target=get_intsain())
    auto_get.daemon = True
    auto_get.start()

#     get uniformity 함수 만들어서 균제도 평균조도 등을 반환.




