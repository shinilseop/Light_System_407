from multiprocessing import Process

from flask import Flask, request
from Core import arduino_color_sensor as acs
from Core import Intsain_Curr as IC
from Core import Intsain_Illum as II
from gevent.pywsgi import WSGIServer
#Flask 인스턴스 생성
app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'hi'

@app.route('/insert/CCT', methods = ['POST'])
def insert_cct():
    num = int(request.form.get('num'))
    cct = float(request.form.get('cct'))
    illum = float(request.form.get("illum"))
    print(num,"번 들어옴")

    # print(type(num))
    if(num == 1) :
        cct = (1.1062*cct)-618.65
    elif (num == 2) :
        cct = (1.1011*cct)-617.02
    elif (num == 3) :
        cct = (1.1201*cct)-595.18
    elif (num == 4) :
        cct = (1.1304*cct)-677.1
    elif (num == 5) :
        cct = (1.0591*cct)-607.35
    elif (num == 6) :
        cct = (1.0066*cct)-574.18
    elif (num == 7) :
        cct = (1.0347*cct)-619.09
    elif (num == 8) :
        cct = (1.0889*cct)-573.73
    elif (num == 9) :
        cct = (1.0452*cct)-602.95
    elif (num == 10) :
        cct = (1.0639*cct)-542.35
    else :
        return "num_error"

    # insert_db("cct",num, illum, cct)
    acs.set_sensor_data(num, illum, cct)
    # print(num, illum, cct)
    return "ok"


# @app.route('/insert/intsain', methods = ['POST'])
# def insert_sensor_data():
#     data = request.get_json()
#     # 위에 10개 조도센서 아래 10개 전력량계 분해하기.(패킷 받아봐야 함)
#
#
#     # insert_db("cct",num, illum, cct)
#     # acs.set_sensor_data(num, illum, cct)
#     return "ok"

def insert_db(type, num, illum, cct):
    return 0




def start_api_server():
    # app.run(host="192.168.100.100",debug=True)
    http_server = WSGIServer(("192.168.100.100", 80), app)
    http_server.serve_forever()


# 서버 실행
if __name__ == '__main__':
    # app.run(host="192.168.100.100",port=80,debug=True, threaded=True)
    http_server = WSGIServer(("192.168.100.100", 80), app)
    http_server.serve_forever()

    # api = Process(target=start_api_server())
    # api.daemon = True
    # api.start()


#  mongoDB 구축, 아두이노 포팅, udp 통신제어