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
    total_value = ch[0]+ch[1]+ch[2]+ch[3]
    max_cut = 255-total_value

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

    acs_cct = acs1.get_sensor_data()[0][:9]
    II_illum = II1.get_illum_data()[:9]
    IC_curr = IC1.get_curr_data()[:9]

    print("색온도 표준편차(92이하)", stdev(acs_cct[:9]))
    print("조도 표준편차(18이하)", stdev(II_illum[:9]))
    # print(acs_cct)

    # 3차원 면보정식
    # for i in range(9):
    #     acs_cct[i] = (acs_cct[i] * 1.207566) + (II_illum[i] * -0.74406) + 494.1541

    # print(acs_cct)

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
                final_df = temp_df[temp_df['illum'] == target_illum1[i]]
                # print(final_df[['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])
                cut = (target_illum1[i] / target_illum[i])
                # cut = 1

                if cut == 0:
                    cut = 1
                # print(cut , target_illum1[i], target_illum[i])
                # print(final_df[['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])

                ch1 = int(final_df['ch.1'].values[0] / cut)
                ch2 = int(final_df['ch.2'].values[0] / cut)
                ch3 = int(final_df['ch.3'].values[0] / cut)
                ch4 = int(final_df['ch.4'].values[0] / cut)
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

        if (abs(500 - avg_illum) > 20):

            scale = (abs(500 - avg_illum) / 30)
            if scale - int(scale) > 0.5:
                scale = int(scale) + 1
            else:
                scale = int(scale)

            print(scale, "이만큼!")
            if scale == 1:
                count = count + 1

            if avg_illum < 500:
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

def dimming_illum_2(cct_now,illum_flag):
    impact_index = [
        [8, 2, 7, 9, 1, 3, 14, 15, 13],
        [4, 3, 9, 10, 8, 5, 11, 2, 15, 16],
        [5, 11, 12, 6, 10, 4, 17, 16, 18],
        [14, 8, 20, 15, 13, 7, 19, 21, 9],
        [15, 16, 9, 22, 21, 10, 14, 17, 8, 11, 20, 23],
        [17, 11, 23, 16, 18, 24, 22, 10, 12],
        [20, 26, 19, 21, 27, 25, 14, 13, 15],
        [28, 27, 21, 22, 23, 20, 29, 26, 15, 16],
        [23, 29, 24, 28, 22, 30, 17, 16, 18]
    ]
    while True:
        # illum_flag = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        zero_index = []
        for i in range(len(data_pd)):
            illum = data_pd.loc[i, 'illum']
            if (abs(illum - 500) >= 20):
                if illum > 500:
                    # print("-")
                    for j in impact_index[i]:
                        illum_flag[j - 1] = illum_flag[j - 1] - 1
                elif illum < 500:
                    # print("+")
                    for j in impact_index[i]:
                        illum_flag[j - 1] = illum_flag[j - 1] + 1
            else:
                zero_index.append(i)

        if len(zero_index) == 9:
            print("조도 제어 필요없음")
            sensing_data_check()
            data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
            return 0

        LED_state = ILED.get_LED_state()
        # illum_gap = 1
        for i in range(len(illum_flag)):
            # illum_gap = illum_flag[i]
            if illum_flag[i] != 0:
                illum_gap = illum_flag[i] / abs(illum_flag[i])

                ch1 = update_state_illum(LED_state[i][1], illum_gap)
                ch2 = update_state_illum(LED_state[i][2], illum_gap)
                ch3 = update_state_illum(LED_state[i][3], illum_gap)
                ch4 = update_state_illum(LED_state[i][4], illum_gap)
                # print(i+1,ch1, ch2, ch3, ch4)
                if (ch1 + ch2 + ch3 + ch4) != 0:
                    ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)
            else:
                continue

def dimming_cct(cct_now):
    impact_index = [
        [8,2,7,9,1,3,14,15,13],
        [4,3,9,10,8,5,11,2,15,16],
        [5,11,12,6,10,4,17,16,18],
        [14,8,20,15,13,7,19,21,9],
        [15,16,9,22,21,10,14,17,8,11,20,23],
        [17,11,23,16,18,24,22,10,12],
        [20,26,19,21,27,25,14,13,15],
        [28,27,21,22,23,20,29,26,15,16],
        [23,29,24,28,22,30,17,16,18]
    ]
    count =0
    pass_stack = False
    sign_gap = 0

    while True:
        count= count+1
        print("cct_count : ", count)

        cct_flag = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        zero_index = []
        for i in range(len(data_pd)):
            cct = data_pd.loc[i,'cct']
            if (abs(cct-cct_now)>=50):
                if abs(cct - cct_now) >= 60:
                    sign_gap = 2
                else:
                    sign_gap = 1

                if cct > cct_now:
                    # print("-")
                    for j in impact_index[i]:
                        cct_flag[j-1] = cct_flag[j-1]-sign_gap
                elif cct < cct_now:
                    # print("+")
                    for j in impact_index[i]:
                        cct_flag[j-1] = cct_flag[j-1]+sign_gap
            else:
                zero_index.append(i)

        if len(zero_index)==9:
            return 0
            # if pass_stack == False:
            #     print("색온도 제어 필요없음, 조도 디밍 해봄")
            #     pass_stack = True
            #     dimming_illum_2(cct_now)
            #     continue
            # else:
            #     print("색온도 제어 필요없음, 조도 디밍도 필요없음!")
            #     return 0

        pass_stack = False

        # if avg_illum>=700:
        #     dimming_illum_2(cct_now)

        # print("플래그 그대로: ",cct_flag)

        # for i in zero_index:
        #     for j in impact_index[i]:
        #         # 요부분이 너무 가혹한거일수도 있음.. 1/2로 설정하는것도 방법일듯함.
        #         if abs(cct_flag[j - 1])!=1:
        #             cct_flag[j - 1] = int(cct_flag[j - 1]/2)

        LED_state = ILED.get_LED_state()
        print(LED_state)
        print("플래그 최적화 후 : ",cct_flag)

        for i in range(len(cct_flag)):
            ch1 = LED_state[i][1]
            ch2 = LED_state[i][2]
            ch3 = LED_state[i][3]
            ch4 = LED_state[i][4]

            gap = abs(cct_flag[i])
            # gap = 1

            # 1 채널 : 7247
            # 2 채널 : 6412
            # 3 채널 : 3980
            # 4 채널 : 2431
            #
            # 1,2채널 중간 : 6800
            # 2,3채널 중간 : 5200
            # 3,4채널 중간 : 3200

            # 조도비 역산한것.
            # 1	0.878041802	1.017484775	1.404088808
            # 1.13889794	1	1.158811314	1.599113851
            # 0.982815689	0.862953259	1	1.379960509
            # 0.712205663	0.625346344	0.724658419	1

            if cct_flag[i] > 0:
                if cct_now>=3800:
                    # print(str(i + 1) + "조명 +")
                    # print(str(i+1)+"조명 + : 1,2 채널을 켜고 3,4 채널을 끈다")
                    if cct_now>=6800:
                        # print("1채널 위주")
                        ch1 = update_state_cct(LED_state[i][1:], 1, gap)
                        if(ch4==0) & (ch3==0):
                            ch2 = update_state_cct(LED_state[i][1:], 2, gap*-0.87)
                        elif (ch4==0) & (ch3!=0):
                            ch3 = update_state_cct(LED_state[i][1:], 3, gap*-1.01)
                        else:
                            ch4 = update_state_cct(LED_state[i][1:], 4, gap*-1.4)

                    else:
                        # print("2채널 위주")
                        ch2 = update_state_cct(LED_state[i][1:], 2, gap)
                        if (ch4 == 0) & (ch3 == 0):
                            ch1 = update_state_cct(LED_state[i][1:], 1, gap * -1.13)
                        elif (ch3 == 0) & (ch4 != 0):
                            ch4 = update_state_cct(LED_state[i][1:], 4, gap * -1.15)
                        else:
                            ch3 = update_state_cct(LED_state[i][1:], 3, gap * -1.59)
                else:
                    # print("3채널 위주")
                    ch3 = update_state_cct(LED_state[i][1:], 3, gap)
                    ch4 = update_state_cct(LED_state[i][1:], 4, gap * -1.37)

            elif cct_flag[i] < 0:
                # print(str(i + 1) + "조명 -")
                if cct_now >= 6600:
                    # print("2채널 위주")
                    ch2 = update_state_cct(LED_state[i][1:], 2, gap)
                    ch1 = update_state_cct(LED_state[i][1:], 1, gap * -1.13)

                else:
                    # print(str(i+1)+"조명 - : 3,4 채널을 켜고 1,2 채널을 끈다")
                    if cct_now >= 3200:
                        # print("3채널 위주")
                        ch3 = update_state_cct(LED_state[i][1:], 3, gap)
                        if (ch1 == 0) & (ch2 == 0):
                            ch4 = update_state_cct(LED_state[i][1:], 4, gap * -1.37)
                        elif (ch1 != 0) & (ch2 == 0):
                            ch1 = update_state_cct(LED_state[i][1:], 1, gap * -0.98)
                        else:
                            ch2 = update_state_cct(LED_state[i][1:], 2, gap * -0.86)
                    else:
                        # print("4채널 위주")
                        ch4 = update_state_cct(LED_state[i][1:], 4, gap)
                        if (ch1 == 0) & (ch2 == 0):
                            ch3 = update_state_cct(LED_state[i][1:], 3, gap * -0.72)
                        elif (ch1 == 0) & (ch2 != 0):
                            ch2 = update_state_cct(LED_state[i][1:], 2, gap * -0.62)
                        else:
                            ch1 = update_state_cct(LED_state[i][1:], 1, gap * -0.71)


            # print(i+1,ch1, ch2, ch3, ch4)
            if (ch1+ch2+ch3+ch4)!=0:
                ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)
            # else:
                # print("켜긴해야해서 소등제어 무효화")

        # dimming_illum_2(cct_now,sign_gap)
        dimming_illum_2(cct_now,cct_flag)

        # print(ILED.get_LED_state())
        # print("[색온도 디밍 결과]")
        # sensing_data_check()
        # data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)

def process(task_type):
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()


    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()
    # target_illum = [24,122,24,77,295,24,46,168,62,24,24,24,24,24,62,62,77,24,24,225,24,46,263,24,24,62,24,138,24,24]
    # target_illum1 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    # 기준 조도, 색온도 설정
    cct_now = 0

    while True:
        # mongo_df = load_NL_CCT_mongo()
        # # cct_now = float(mongo_df['CCT'].values[0])
        # # cct_now = 2700
        # print("실시간 cas cct :"+str(cct_now))
        #
        # # 제어지표 필터링.
        # control_pd = pd.read_csv("../LEDcontrol_list.csv")
        # control_pd["illum"] = control_pd["illum"].astype(float)
        # control_pd["cct"] = control_pd["cct"].astype(float)
        #
        # # 반복 포인트 if 를 더해서.
        # mask = (control_pd.cct >= cct_now - 50) & (control_pd.cct <= cct_now + 50) & (control_pd.zero_count<=2)
        # print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])
        # temp = control_pd[mask]['illum'].values
        # temp_df = control_pd[mask]
        # temp_df = temp_df.reset_index(drop=True)
        #
        # # 조도 디밍1
        # dimming_illum(temp_df, temp, target_illum, target_illum1, cct_now)
        # # 색온도 디밍
        # dimming_cct(cct_now)
        #
        #
        # # 1분주기로 반복.(카스 재측정시간)
        # # time.sleep(10)
        #

        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                 columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
        LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
        # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd)


        # cct_now=cct_now+50
        # if cct_now >8000:
        #     break

if __name__ == '__main__':
    process("30LED_energe_point1")