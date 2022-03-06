
import Core.blind as blind
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

def dimming_illum_part(temp_df, temp, control_index, target_illum1, cct_now):
    return control_index


def blind_control(nonfirst, old_illum, current_angle):
    if nonfirst:
        mongo_df = load_NL_CCT_mongo()
        illum_now = float(mongo_df['Photometric'].values[0])

        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(0)

        while(avg_illum>1000):
            if abs(old_illum-illum_now)>500:
                if old_illum<illum_now:
                    # 조도가 올라가면 블라인드는 닫아야지.
                    current_angle = current_angle-3.8*(abs(old_illum-illum_now)/500+1)
                else:
                    current_angle = current_angle+3.8*(abs(old_illum-illum_now)/500+1)
                blind.ctrl_tilt(current_angle)
                sensing_data_check()
                data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(0)
    else:
        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(0)

        while (avg_illum > 1000):
                current_angle = current_angle + 3.8
                blind.ctrl_tilt(current_angle)
                sensing_data_check()
                data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(0)
    return current_angle


def process(tasktype):
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    nonfirst = False
    current_angle=-70
    blind.ctrl_tilt(current_angle)
    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()

    # 500lux 기준으로 했을때 1번채널의 실제 값들.new LED
    control_index = [50, 55, 23, 40, 60, 40,
                     20, 20, 15, 20, 15, 15,
                     30, 20, 25, 18, 25, 30,
                     40, 23, 20, 10, 15, 15,
                     40, 30, 25, 25, 60, 40]

    target_illum1 = [50, 55, 23, 40, 60, 40,
                     20, 20, 15, 20, 15, 15,
                     30, 20, 25, 18, 25, 30,
                     40, 23, 20, 10, 15, 15,
                     40, 30, 25, 25, 60, 40]

    case_1_1 = [2, 3, 4, 5, 9, 10]
    case_1_2 = [2, 3, 4, 5, 6, 9, 10, 11, 16]
    case_1_3 = [2, 3, 4, 5, 6, 9, 10, 11, 12, 16, 17, 18, 24]

    case_2_1 = [2, 3, 4, 5, 9, 10]
    case_2_2 = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 15, 16]
    case_2_3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 30]

    case_3_1 = [2, 3, 4, 5, 9, 10]
    case_3_2 = [1, 2, 3, 4, 5, 8, 9, 10, 15]
    case_3_3 = [1, 2, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 19]

    while True:
        mongo_df = load_NL_CCT_mongo()
        cct_now = float(mongo_df['CCT'].values[0])
        new_illum = float(mongo_df['Photometric'].values[0])
        if nonfirst is False:
            old_illum = new_illum
            print("1빠..?")

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
            lll.get_LED_state('LED_State', str(backup.loc[idx, "_id"]),control_index,nonfirst)

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

        # 블라인드(1번째 : 임계값까지 틸트변경, 이후: 000lux변동시 임계값까지)
        print("블라인드 제어")
        # current_angle = blind_control(nonfirst,old_illum,current_angle)
        nonfirst = True
        # 조도디밍(구역별..?)
        # control_index = dimming_illum_part(temp_df, temp, control_index, target_illum1, cct_now)


        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                 columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
        LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
        old_illum = new_illum

        # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, tasktype)
        # input("continue? (press any key) :")



if __name__ == '__main__':
    process("test")





# 암막, 자연광 색온도, 실시간, 색온도 디바이스, 필요조도, 색온도, 블라인드 재현

# 유창공간 알고리즘
#
# 1. 블라인드 제어(조건부 디밍)
# 2. 색온도 제어(디밍x)
# 3. 조도 제어(디밍o)
#
# 부팅시
# 0. 미리 측정해놓은 30개 세트의 색온도, 조도 배열을 조명을 통해 재현(현시간 측정 색온도 기준)
#
# 시스템 시작
# 1. 처음은 블라인드를 끝까지 내려놓은 상태.
# -> 창측 조도가 지점별로 000Lux 이상 넘어가지 않는다면 지속 개방(확산판 설치 후)
# 2. 임계치 까지 올라간 블라인드제어 후 구역별 조도 디밍 실행(색온도 유지)
# -> 조도 디밍 이후 조명 별 제어지표 값(0~255)를 테이블로 가지고 있음.
#
# 여기서부터 반복.
# 3.  외부 조도가 1000이상 변화한다면. 블라인드 제어
# 3-1. 조도 디밍 추가.
# 4.  외부 색온도에 맞게 30개 세트 조명 재현(이때 30개의 제어지표 비율 적용해서 재현)
# 4-1. 조도 디밍 추가.

# 초기세팅(1번째 : 조도비율 x, 이후 : 조도비율 적용)
# 블라인드(1번째 : 임계값까지 틸트변경, 이후: 000lux변동시 임계값까지)
# 조도디밍(구역별..?)