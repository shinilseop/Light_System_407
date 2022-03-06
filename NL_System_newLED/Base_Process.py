# 1. API 서버 개설
# 2. 데이터 베이스 연결
# 3. 릴레이 한번 껏다 켜기.
# 4. 알고리즘 시작(이건 따로 상위에서 돌림)
import threading, time
from API import TCP_Server
from Core import switch
from Core import sensing_process as sp
from multiprocessing import Process, Queue


def process():

    api = threading.Thread(target=TCP_Server.process)
    api.start()

    # switch.onnoff()

    auto_get = threading.Thread(target=sp.get_intsain)
    auto_get.start()

if __name__ == '__main__':
    process()



