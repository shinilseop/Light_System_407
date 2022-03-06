import threading
import time

import pandas as pd

from NL_System import Base_Process as bp

from Core import switch
from Core.Intsain_Curr import IC
from Core.Intsain_Illum import II
from Core.arduino_color_sensor import acs

import Shin_Package.led_select_module_blind_not_include.datas as datas
import Shin_Package.led_select_module_blind_not_include.illum_controller as controller

acs1 = acs.getInstance()
II1 = II.getInstance()
IC1 = IC.getInstance()

def start_data_center():
    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()

def init_datas():
    # 센서 데이터 값 초기화
    for i in range(1, 10):
        acs1.set_sensor_data(i, 0, 0)
        II1.set_illum_data(i - 1, 0)
        IC1.set_curr_data(i - 1, 0)
    data_flag = True
    data_count = 0

    # 데이터 받기 (초기화 한 후에 모든 데이터가 다 들어올때 까지 대기)
    # 색온도는 초기값 설정을 안하기 때문에 여기서는 체크 x
    while data_flag:
        data_flag = False

        II_illum = II1.get_illum_data().copy()[:9]
        IC_curr = IC1.get_curr_data().copy()[:10]

        print(II_illum)
        print(IC_curr)

        # 조도 9개 체크
        for i in II_illum:
            if i == 0:
                print(i)
                data_flag = True
                continue

        # 소비전력 9개 체크
        for i in IC_curr:
            if i == 0:
                data_flag = True
                continue

        if data_count > 50:
            break
        else:
            time.sleep(0.1)
            data_count = data_count + 1

    # 초기값 설정 시작
    II_illum = II1.get_illum_data().copy()[:9]
    IC_curr = IC1.get_curr_data().copy()[:10]
    sum_curr = 0
    min_illum = 99999
    # 단위구역이 연속하는경우 KS C 7612 기준 평균 계산법
    sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[5] * 2 + \
                II_illum[6] + II_illum[7] * 2 + II_illum[8]
    avg_illum = sum_illum / 16
    # 초기 대기 조도 설정
    for i in range(9):
        sum_curr += IC_curr[i]
        if (min_illum > II_illum[i]):
            min_illum = II_illum[i]
    print("10\t\t-1\t\t-1\t\t" + str(IC_curr[9]))
    # 대기전력 설정
    sum_curr += IC_curr[9]

    # 대기전력 및 대기조도 출력 및 led 초기 제어
    if sum_curr > 0:
        datas.wait_curr = round(sum_curr, 2)
        print("대기전력 : %s" % datas.wait_curr)
        print("대기조도")
        for i in range(9):
            datas.wait_illum[i] = II_illum[i]
            print(str(i + 1) + " wait illum : " + str(datas.wait_illum[i]))
        controller.led_control_use_state(datas.led_control, datas.led_state)
        time.sleep(5)

def sensing_datas():
    for i in range(1, 10):
        acs1.set_sensor_data(i, 0, 0)
        II1.set_illum_data(i - 1, 0)
        IC1.set_curr_data(i - 1, 0)
    data_flag = True
    data_count = 0
    while data_flag:
        data_flag = False

        # 값 불러옴
        acs_cct = acs1.get_sensor_data()[0][:9]
        II_illum = II1.get_illum_data()[:9]
        IC_curr = IC1.get_curr_data()[:10]
        # print(acs_cct)
        # print(II_illum)
        # print(IC_curr)

        # CCT 체크
        # for i in acs_cct:
        #     if i == 0:
        #         data_flag = True
        #         continue
        #
        # # 조도 체크
        for i in II_illum:
            if i == 0:
                data_flag = True
                continue

        # 소비 전력 체크
        # if IC_curr[9] == 0:
        #     data_flag=True
        #     continue
        # for i in IC_curr:
        #     if i == 0:
        #         data_flag = True
        #         continue

        # 만약 100번 카운트 하는동안 받지 못하면 릴레이를 한번 온오프 시작
        if data_count > 100:
            # switch.onnoff()
            print("sensing data_count 100 over")
            data_count = 0
        else:
            time.sleep(0.2)
            data_count = data_count + 1

    # 문제없으면 받아와서 알고리즘 실행
    acs_cct = acs1.get_sensor_data().copy()[0][:9]
    II_illum = II1.get_illum_data().copy()[:9]
    IC_curr = IC1.get_curr_data().copy()[:10]

    return acs_cct, II_illum, IC_curr

def sensing_curr():
    for i in range(1, 10):
        IC1.set_curr_data(i - 1, 0)
    data_flag = True
    data_count = 0
    while data_flag:
        data_flag = False

        # 값 불러옴
        IC_curr = IC1.get_curr_data()[:10]

        # 소비 전력 체크
        for i in IC_curr:
            if i == 0:
                data_flag = True
                continue

        # 만약 100번 카운트 하는동안 받지 못하면 릴레이를 한번 온오프 시작
        if data_count > 100:
            switch.onnoff()
            data_count = 0
        else:
            time.sleep(0.5)
            data_count = data_count + 1

    # 문제없으면 받아와서 알고리즘 실행
    IC_curr = IC1.get_curr_data().copy()[:10]

    return IC_curr

def need_value(wait_illum, wait_curr, get_times):
    # 필요 변수 설정
    sum_cct = 0.0  # CCT 합산용
    sum_curr = -wait_curr  # 소비전력 합산용
    min_illum = 10000  # 균제도 계산을 위한 변수
    uniformity = 0.0  # 균제도 용

    # 대기조도 제외
    # for i in range(9):
    #     datas.II_illum[i] -= wait_illum[i]

    # 단위구역이 연속하는경우 KS C 7612 기준 평균 계산법
    sum_illum = datas.II_illum[0] + datas.II_illum[1] * 2 + datas.II_illum[2] + datas.II_illum[3] * 2 + datas.II_illum[4] * 4 + datas.II_illum[5] * 2 + \
                datas.II_illum[6] + datas.II_illum[7] * 2 + datas.II_illum[8]

    # 센서값 데이터프레임으로 통합 및 필요한 값 계산 및 출력
    data_pd = pd.DataFrame(datas.acs_cct, columns=['cct'])
    print("\n\n\t\t측정데이터", str(get_times), "STEP", datetime.now())
    print("P\t\tCCT\t\t\tIllum\t\tCurr")
    for i in range(9):
        data_pd.loc[i, 'illum'] = datas.II_illum[i]
        data_pd.loc[i, 'curr'] = datas.IC_curr[i]
        print(str(i + 1) + "\t\t" + str(datas.acs_cct[i])[:7] + "\t\t" + str(datas.II_illum[i])[:7] + "\t\t" + str(
            datas.IC_curr[i]))
        sum_cct += datas.acs_cct[i]
        sum_curr += datas.IC_curr[i]
        if (min_illum > datas.II_illum[i]):
            min_illum = datas.II_illum[i]
    print("10\t\t-1\t\t-1\t\t" + str(datas.IC_curr[9]))
    avg_illum = sum_illum / 16
    avg_cct = sum_cct / 9
    sum_curr += datas.IC_curr[9]
    sum_curr = round(sum_curr, 2)
    if (avg_illum != 0):
        uniformity = round(min_illum / avg_illum, 7)
    print(
        "Avg_CCT\t\t%s\t\tAvg_Ill\t\t%s\t\tSum_Curr\t\t%s\t\tUniformity\t\t%s" % (
            str(avg_cct)[:7], str(avg_illum)[:8], str(sum_curr), str(uniformity)))

    return avg_cct, avg_illum, sum_curr, uniformity

# 스텝별로 제어 상태, 센서 값 저장하는 함수
def save_temp(acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, sensing_time):
    led_num_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    new_df = pd.DataFrame(led_num_list, columns=['cct, illum, curr, uniformity'])
    for idx in range(1, len(datas.led_state)):
        if (idx < 10):
            new_df.loc[idx - 1, 'cct'] = acs_cct[idx - 1]
            new_df.loc[idx - 1, 'illum'] = II_illum[idx - 1]
            new_df.loc[idx - 1, 'curr'] = IC_curr[idx - 1]
            new_df.loc[idx - 1, 'curr'] = IC_curr[idx - 1]
        elif (idx < 11):
            new_df.loc[idx - 1, 'curr'] = IC_curr[idx - 1]
    new_df.loc[10, 'cct'] = avg_cct
    new_df.loc[10, 'illum'] = avg_illum
    new_df.loc[10, 'curr'] = sum_curr
    new_df.loc[0, 'uniformity'] = uniformity

    str_time = datetime.strftime(sensing_time.replace(microsecond=0), "%Y%m%d %H_%M_%S")
    new_df.to_csv(
        "D:\\BunkerBuster\\Desktop\\shin_excel\\실 자연광 측정\\20211207_-70도 조도 테스트\\4\\%s.csv" % (str_time))

from datetime import datetime

if __name__=='__main__':
    start_data_center()
    sensing_time = datetime(2000, 1, 1, 12, 0, 0)
    while True:
        datas.acs_cct, datas.II_illum, datas.IC_curr = sensing_datas()
        print(datas.acs_cct)
        print(datas.II_illum)
        print(datas.IC_curr)
        avg_cct, avg_illum, sum_curr, uniformity = need_value(datas.wait_illum, datas.wait_curr, 0)
    # while True:
    #     if ((datetime.now() - sensing_time).seconds >= 60):
    #         acs_cct, II_illum, IC_curr = sensing_datas()
    #         sensing_time = datetime.now()
    #         # print("\n\t\t\t측정데이터")
    #         # print("P\t\tCCT\t\t\tIllum\t\tCurr")
    #         # for i in range(9):
    #         #     print(str(i + 1) + "\t\t" + str(acs_cct_t[i])[:7] + "\t\t" + str(II_illum_t[i])[:7] + "\t\t" + str(IC_curr_t[i]))
    #         # print("10\t\t-1\t\t\t-1\t\t\t" + str(IC_curr_t[9]))
    #         # time.sleep(1)
    #
    #         sum_cct = 0.0  # CCT 합산용
    #         sum_curr = 0.0  # 소비전력 합산용
    #         min_illum = 10000  # 균제도 계산을 위한 변수
    #         uniformity = 0.0  # 균제도 용
    #
    #         sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[5] * 2 + \
    #                     II_illum[6] + II_illum[7] * 2 + II_illum[8]
    #
    #         print("\n\n\t\t측정데이터 %s"%sensing_time)
    #         print("P\t\tCCT\t\tIllum\t\tCurr")
    #
    #         for i in range(9):
    #             print(str(i + 1) + "\t\t" + str(acs_cct[i])[:7] + "\t\t" + str(II_illum[i])[:7] + "\t\t" + str(IC_curr[i]))
    #             sum_cct += acs_cct[i]
    #             sum_curr += IC_curr[i]
    #             if (min_illum > II_illum[i]):
    #                 min_illum = II_illum[i]
    #         print("10\t\t-1\t\t-1\t\t" + str(IC_curr[9]))
    #         avg_illum = sum_illum / 16
    #         avg_cct = sum_cct / 9
    #         sum_curr += IC_curr[9]
    #         sum_curr = round(sum_curr, 2)
    #         if (avg_illum != 0):
    #             uniformity = round(min_illum / avg_illum, 7)
    #         print(
    #             "Avg_CCT\t\t%s\t\tAvg_Ill\t\t%s\t\tSum_Curr\t\t%s\t\tUniformity\t\t%s" % (
    #                 str(avg_cct)[:7], str(avg_illum)[:8], str(sum_curr), str(uniformity)))
    #
    #         save_temp(acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, sensing_time)
