# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
import pandas as pd
from MongoDB import Load_MongoDB as LMDB
from MongoDB import Insert_MongoDB as IMDB

from NL_System import Base_Process as bp
from Core import Intsain_LED_rev as ILED
import numpy as np
import threading, time
from Core.arduino_color_sensor import acs
from Core.Intsain_Illum import II
from Core.Intsain_Curr import IC
from Core import switch


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def load_NL_CCT_mongo():
    step_data = LMDB.load_last1_cct()
    step_df = LMDB.mongodb_to_df(step_data, 'mongo_cas')
    step_df = step_df.reset_index(drop=True)
    return step_df


def update_state_illum(ch, updown):
    if ch == 0:
        return 0
    else:
        re = ch + updown
        if re < 0:
            return 0
        else:
            return re


def update_state_cct(ch, index, updown):
    total_value = ch[0] + ch[1] + ch[2] + ch[3]
    max_cut = 255 - total_value

    if updown > max_cut:
        updown = max_cut

    re = ch[index - 1] + int(updown)
    if re < 0:
        return 0

    elif re > 255:
        return 255

    else:
        return re


def sensing_data_check():
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    for i in range(1, 10):
        acs1.set_sensor_data(i, 0, 0)
        II1.set_illum_data(i - 1, 0)
        IC1.set_curr_data(i - 1, 0)
    data_flag = True
    data_count = 0
    while data_flag:
        # print(data_count)
        data_flag = False

        acs_cct = acs1.get_sensor_data()[0][:9]
        II_illum = II1.get_illum_data()[:9]
        IC_curr = IC1.get_curr_data()[:9]

        for i in acs_cct:
            if i == 0:
                data_flag = True
                continue

        for i in II_illum:
            if i == 0:
                data_flag = True
                continue

        for i in IC_curr:
            if i == 0:
                data_flag = True
                continue

        if data_count > 100:
            # print(data_count, "?")
            switch.onnoff()
            data_count = 0
        else:
            time.sleep(0.5)
            data_count = data_count + 1

    return 0


def sensing_data(cct_now):
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    acs_cct = acs1.get_sensor_data()[0][:10]
    II_illum = II1.get_illum_data()[:10]
    IC_curr = IC1.get_curr_data()[:10]

    # print(acs_cct)

    # 3차원 면보정식
    # for i in range(9):
    #     acs_cct[i] = (acs_cct[i] * 1.207566) + (II_illum[i] * -0.74406) + 494.1541

    # print(acs_cct)

    data_pd = pd.DataFrame(acs_cct, columns=['cct'])
    for i in range(10):
        data_pd.loc[i, 'illum'] = II_illum[i]
        data_pd.loc[i, 'curr'] = IC_curr[i]
    #
    print(data_pd)

    uniformity = 0
    sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[
        5] * 2 + \
                II_illum[6] + II_illum[7] * 2 + II_illum[8]
    avg_illum = sum_illum / 16
    avg_cct = np.nanmean(acs_cct[:9])
    min_illum = np.nanmin(II_illum[:9])
    if (avg_illum != 0):
        uniformity = min_illum / avg_illum

    print("평균조도\t 타겟 색온도\t 평균 색온도\t 균제도")
    print(avg_illum, "\t", cct_now, "\t", avg_cct, "\t", uniformity)

    return data_pd, avg_illum, cct_now, avg_cct, uniformity


def process(task_type):
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()

    # 1번 지점 중심
    # map_list = [[1], [2, 8], [1, 2, 7, 8, ], [1, 2, 3, 7, 8, 9, 13, 14, 15],
    #             [1, 2, 3, 4, 7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22],
    #             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
    #              29, 30]]

    # 3번 지점 중심
    # map_list = [[6], [5, 11], [5,6,11,12], [4,5,6,10,11,12,16,17,18],
    #             [3,4,5,6,9,10,11,12,15,16,17,18,21,22,23,24],
    #             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
    #              29, 30]]

    # 5번 지점 중심
    # map_list = [[15, 16], [9, 10, 15, 16, 21, 22], [8, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 23],
    #             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
    #              29, 30]]

    # 7번 지점 중심
    # map_list = [[25], [20, 26], [19, 20, 25, 26], [13, 14, 15, 19, 20, 21, 25, 26, 27],
    #             [7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22, 25, 26, 27, 28],
    #             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
    #              29, 30]]

    # 9번 지점 중심
    # map_list = [[30], [23, 29], [23, 24, 29, 30], [16, 17, 18, 22, 23, 24, 28, 29, 30],
    #             [9, 10, 11, 12, 15, 16, 17, 18, 21, 22, 23, 24, 27, 28, 29, 30],
    #             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
    #              29, 30]]

    for o in range(4):
        if o < 2:
            continue

        for j in range(10, 201, 10):
            if o == 0:
                a = j
                b = c = d = 0
            elif o == 1:
                b = j
                a = c = d = 0
            elif o == 2:
                if j <180:
                    continue
                c = j
                a = b = d = 0
            elif o == 3:
                d = j
                a = b = c = 0

            # for x in range(len(map_list)):
            #     for y in map_list[x]:
            #         # print(a, b, c, d)
            #         ILED.set_LED(y, a, b, c, d)
            #         # time.sleep(1)

            ILED.all_set_LED(a, b, c, d)
            sensing_data_check()
            data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(0)
            result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                     columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
            LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
            IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, task_type)
                # print(x,"!1")

                # if x == 0:
                #     ILED.set_LED(map_list[x][0], 0, 0, 0, 0)
                # if x == len(map_list)-1:
                #     ILED.all_set_LED(0, 0, 0, 0)

            # input("continue? (press any key) :")

if __name__ == '__main__':
    process("diff_test_point_2_2")
