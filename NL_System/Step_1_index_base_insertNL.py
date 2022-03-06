# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
from statistics import stdev

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
from MongoDB import  Load_MongoDB_local_log as lll

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def find_nearest_index(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

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

    print("색온도 표준편차(92이하)", stdev(acs_cct[:9]))
    print("조도 표준편차(18이하)", stdev(II_illum[:9]))

    data_pd = pd.DataFrame(acs_cct, columns=['cct'])
    for i in range(9):
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


def dimming_illum(temp_df, temp, target_illum, target_illum1, cct_now):
    count = 0
    first = True
    up_and_down = 0
    while count < 5:
        if first:
            for i in range(len(target_illum)):
                target_illum1[i] = find_nearest(temp, target_illum[i])
                print("인가전류!", target_illum[i])
                final_df = temp_df[temp_df['total_index'] == target_illum1[i]]
                print(final_df[['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct', 'total_index']])
                # cut = (target_illum1[i] / target_illum[i])
                # # cut = 1
                #
                # if cut == 0:
                #     cut = 1
                # print(cut, target_illum1[i], target_illum[i])
                # print(final_df[['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])
                ch1 = int(final_df['ch.1'].values[0])
                ch2 = int(final_df['ch.2'].values[0])
                ch3 = int(final_df['ch.3'].values[0])
                ch4 = int(final_df['ch.4'].values[0])
                temp_index = ch1 + ch2 + ch3 + ch4
                cut1 = int((target_illum[i] - temp_index) * (ch1 / temp_index))
                cut2 = int((target_illum[i] - temp_index) * (ch2 / temp_index))
                cut3 = int((target_illum[i] - temp_index) * (ch3 / temp_index))
                cut4 = int((target_illum[i] - temp_index) * (ch4 / temp_index))

                ch1 = update_state_illum(ch1, cut1)
                ch2 = update_state_illum(ch2, cut2)
                ch3 = update_state_illum(ch3, cut3)
                ch4 = update_state_illum(ch4, cut4)
                # print(i+1,ch1, ch2, ch3, ch4)
                ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)
                first = False

        else:
            for i in range(len(target_illum)):
                LED_state = ILED.get_LED_state()

                ch1 = update_state_illum(LED_state[i][1], up_and_down)
                ch2 = update_state_illum(LED_state[i][2], up_and_down)
                ch3 = update_state_illum(LED_state[i][3], up_and_down)
                ch4 = update_state_illum(LED_state[i][4], up_and_down)
                # print(i+1,ch1, ch2, ch3, ch4)
                ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)

        print(ILED.get_LED_state())

        #  데이터 수집에 문제가 있는지 체크
        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)

        if (abs(800 - avg_illum) > 20):

            scale = (abs(800 - avg_illum) / 40)
            if scale - int(scale) > 0.5:
                scale = int(scale) + 1
            else:
                scale = int(scale)

            print(scale, "이만큼!")
            if scale == 1:
                count = count + 1

            if avg_illum < 800:
                up_and_down = scale
                print("+조정!")

            else:
                up_and_down = -1 * scale
                print("-조정!")

            # continue

        else:
            print("완벽!")
            result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                     columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
            print(result_pd)

            LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
            return 0


def process(tasktype):
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()
    # target_illum = [24,122,24,77,295,24,46,168,62,24,24,24,24,24,62,62,77,24,24,225,24,46,263,24,24,62,24,138,24,24]

    # 800lux 기준으로 했을때 1번채널의 실제 값들.(표준편차 4까직도 내려갔었음, 1채널에선 30대..ㅎ 목표가 18이하)
    control_index = [90, 85, 53, 53, 78, 80,
                     45, 45, 45, 45, 45, 45,
                     55, 48, 55, 58, 35, 40,
                     70, 53, 60, 40, 45, 45,
                     80, 80, 40, 40, 105, 105]


    # 680lux 기준으로 했을때 4번채널의 실제 값들.(표준편차 10까직도 내려갔었음 목표가 18이하)
    # control_index = [90, 83, 43, 43, 83, 90,
    #                  45, 45, 48, 48, 43, 43,
    #                  50, 43, 53, 50, 20, 20,
    #                  60, 53, 40, 40, 40, 30,
    #                  70, 70, 40, 40, 100, 100]

    target_illum = [100, 80, 70, 70, 120, 100,
                    100, 100, 70, 70, 80, 60,
                    50, 80, 24, 24, 24, 24,
                    100, 70, 80, 80, 60, 60,
                    100, 70, 60, 60, 120, 100]
    target_illum1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # 기준 조도, 색온도 설정
    # cct_now = 2700

    while True:
        mongo_df = load_NL_CCT_mongo()
        cct_now = float(mongo_df['CCT'].values[0])
        # cct_now = 2700
        print("실시간 cas cct :" + str(cct_now))

        # log에서 해당 cct 에 가장 적합한 색온도 찾기.
        temp = lll.process('result')
        backup = temp
        temp["avg_cct"] = temp["avg_cct"].astype(float)
        temp = temp['avg_cct'].values
        log_cct = find_nearest(temp, cct_now)

        if abs(cct_now - log_cct) < 50:
            print("로그 찾음!", cct_now, log_cct)
            idx = find_nearest_index(temp, cct_now)
            # print(str(backup.loc[idx, "_id"]))
            lll.get_LED_state('LED_State', str(backup.loc[idx, "_id"]))

        else:
            print("로그 못찾음..!")
            # 제어지표 필터링.
            control_pd = pd.read_csv("../LEDcontrol_list.csv")
            control_pd["illum"] = control_pd["illum"].astype(float)
            control_pd["cct"] = control_pd["cct"].astype(float)

            # 반복 포인트 if 를 더해서.
            mask = (control_pd.cct >= cct_now - 25) & (control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
            print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct', 'total_index']])
            temp = control_pd[mask]['total_index'].values
            temp_df = control_pd[mask]
            temp_df = temp_df.reset_index(drop=True)

            # 조도 디밍1
            dimming_illum(temp_df, temp, control_index, target_illum1, cct_now)
            print("전체 조도 디밍 끝.")


        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                 columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
        LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
        # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, tasktype)
        # input("continue? (press any key) :")

        return 0
        # cct_now = cct_now + 50
        # if cct_now > 8000:
        #     break


if __name__ == '__main__':
    process("step_1_diff_cal_illum_insertNL4")


# 1채널 기준 최적화 :step_1_diff_cal_illum
# 4채널 기준 최적화 : step_1_diff_cal_illum2

# 1채널 기준 자연광 유입 :step_1_diff_cal_illum_insertNL => 흐린날 오후치(20210825)
# 1채널 기준 자연광 유입 :step_1_diff_cal_illum_insertNL3 => 흐린날 오후치(20210826)
# 1채널 기준 자연광 유입 :step_1_diff_cal_illum_insertNL4 => 00날(20210000)
