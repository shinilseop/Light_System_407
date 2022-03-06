from socket import *
from Core.arduino_color_sensor import acs


def process():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    # Prepare a sever socket
    serverSocket.bind(('192.168.100.100', 80))
    serverSocket.listen(80)

    acs1 = acs.getInstance()

    while True:
        # print('Ready to serve...')
        # Establish the connection
        connectionSocket, addr = serverSocket.accept()
        try:
            message = connectionSocket.recv(1024)
            str = message.decode().split("\n")[5].split("&")
            # print(str)
            num = int(str[0].split("=")[1])
            illum = float(str[1].split("=")[1])
            cct = float(str[2].split("=")[1])
            # print(num, "번 들어옴")
            # 30개 보정식(지금 FULL_CONTROL하던건 이걸로.)
            # if(num == 1) :
            #     cct = (1.24498696*cct)-1105.423232
            # elif (num == 2) :
            #     cct = (1.24062724*cct)-1106.674882
            # elif (num == 3) :
            #     cct = (1.25937117*cct)-1090.490959
            # elif (num == 4) :
            #     cct = (1.27553676*cct)-1174.399201
            # elif (num == 5) :
            #     cct = (1.19333697*cct)-1105.055017
            # elif (num == 6) :
            #     cct = (1.12704578*cct)-1062.479705
            # elif (num == 7) :
            #     cct = (1.1664019*cct)-1124.688802
            # elif (num == 8) :
            #     cct = (1.235*cct)-1085.5
            # elif (num == 9) :
            #     cct = (1.18249764*cct)-1139.85934302

            # 요건 세현이형 하던 보정식
            # if (num == 1):
            #     cct = (1.1062 * cct) - 618.65
            # elif (num == 2):
            #     cct = (1.1011 * cct) - 617.02
            # elif (num == 3):
            #     cct = (1.1201 * cct) - 595.18
            # elif (num == 4):
            #     cct = (1.1304 * cct) - 677.1
            # elif (num == 5):
            #     cct = (1.0591 * cct) - 607.35
            # elif (num == 6):
            #     cct = (1.0066 * cct) - 574.18
            # elif (num == 7):
            #     cct = (1.0347 * cct) - 619.09
            # elif (num == 8):
            #     cct = (1.0889 * cct) - 573.73
            # elif (num == 9):
            #     cct = (1.0452 * cct) - 602.95
            # elif (num == 10):
            #     cct = (1.0639 * cct) - 542.35

            # 요건 플라스틱 디퓨져 올린 상태에서 보정한것.
            # if (num == 1):
            #     cct = (1.2097963984 * cct) - 808.0531418844
            # elif (num == 2):
            #     cct = (1.1935746132 * cct) - 795.3383657509
            # elif (num == 3):
            #     cct = (1.2165430984 * cct) - 786.7693855705
            # elif (num == 4):
            #     cct = (1.1882591805 * cct) - 780.1406520483
            # elif (num == 5):
            #     cct = (1.1365120695 * cct) - 720.8215078871
            # elif (num == 6):
            #     cct = (1.0686456951 * cct) - 675.1933825789
            # elif (num == 7):
            #     cct = (1.1174706189 * cct) - 788.4300484164
            # elif (num == 8):
            #     cct = (1.1969873653 * cct) - 791.3948252077
            # elif (num == 9):
            #     cct = (1.1196141442 * cct) - 765.8215582012

            # print(num,"cct 보정 전 :", cct)
            ## 407호 신조명 CCT 보정식
            if (num == 1):
                cct = (1.280016756 * cct) - 1019.120201
            elif (num == 2):
                cct = (1.276247007 * cct) - 1034.686022
            elif (num == 3):
                cct = (1.276861368 * cct) - 951.0860705
            elif (num == 4):
                cct = (1.267826025 * cct) - 1013.54309
            elif (num == 5):
                cct = (1.23963053 * cct) - 1152.045508
            elif (num == 6):
                cct = (1.20009237 * cct) - 1297.94552
            elif (num == 7):
                cct = (1.188784498 * cct) - 1132.065582
            elif (num == 8):
                cct = (1.272535324 * cct) - 1004.004535
            elif (num == 9):
                cct = (1.198625105 * cct) - 1139.436785
            # print(num,"cct 보정 후 :", cct)

            # insert_db("cct",num, illum, cct)
            acs1.set_sensor_data(num, illum, cct)

            # Send one HTTP header line into socket
            # connectionSocket.send('HTTP/1.0 200 OK\r\n\r\n')
        except Exception as err:
            print(err)
            # Send response message for file not found
            # connectionSocket.send('404 Not Found')
            # Close client socket
            print("socket close")
            connectionSocket.close()
    serverSocket.close()


if __name__ == '__main__':
    process()
