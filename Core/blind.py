import serial

# test = serial.Serial(port="COM1", baudrate=9600)
#
#
# # test.write("2A-70\n".encode())
# test.write('1R\n'.encode())
# result = test.readline()
# print(result)
# test.close()

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


def ctrl_tilt(angle):
    test = serial.Serial(port="COM1", baudrate=9600)


    # test.write(('1A' + str(angle) + '\n').encode())
    # result = test.readline()
    # print(result)
    test.write(('3A' + str(angle) + '\n').encode())
    # result = test.readline()
    # print(result)

    test.close()

if __name__ == '__main__':
    ctrl_tilt(-50)