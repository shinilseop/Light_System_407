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


def update_state(ch, updown):
    if ch == 0:
        return 0
    else:
        re = ch + updown
        if re < 0:
            return 0
        else:
            return re


def process(task_type):
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()
    # target_illum = [24,122,24,77,295,24,46,168,62,24,24,24,24,24,62,62,77,24,24,225,24,46,263,24,24,62,24,138,24,24]
    target_illum = [100,80,80,80,80,100,
                    100,80,80,80,80,80,
                    50,24,24,24,24,24,
                    40,140,80,80,80,80,
                    40,140,70,70,80,80]
    target_illum1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # 기준 조도, 색온도 설정
    cct_now = 2700
    illum = 800

    while True:
        mongo_df = load_NL_CCT_mongo()
        # cct_now = float(mongo_df['CCT'].values[0])
        # cct_now = 2700
        print("실시간 cas cct :" + str(cct_now))

        # 제어지표 필터링.
        control_pd = pd.read_csv("../LEDcontrol_list.csv")
        control_pd["illum"] = control_pd["illum"].astype(float)
        control_pd["cct"] = control_pd["cct"].astype(float)

        # 반복 포인트 if 를 더해서.
        mask = (control_pd.cct >= cct_now - 25) & (control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
        print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])
        temp = control_pd[mask]['illum'].values
        temp_df = control_pd[mask]
        temp_df = temp_df.reset_index(drop=True)
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

                    ch1 = update_state(LED_state[i][1], up_and_down)
                    ch2 = update_state(LED_state[i][2], up_and_down)
                    ch3 = update_state(LED_state[i][3], up_and_down)
                    ch4 = update_state(LED_state[i][4], up_and_down)
                    # print(i+1,ch1, ch2, ch3, ch4)
                    ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)

            print(ILED.get_LED_state())

            #  데이터 수집에 문제가 있는지 체크

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

            # 문제없으면 받아와서 알고리즘 실행
            acs_cct = acs1.get_sensor_data()[0][:9]
            II_illum = II1.get_illum_data()[:9]
            IC_curr = IC1.get_curr_data()[:9]

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
            avg_cct = np.nanmean(acs_cct)
            min_illum = np.nanmin(II_illum)
            if (avg_illum != 0):
                uniformity = min_illum / avg_illum

            print("평균조도\t 타겟 색온도\t 평균 색온도\t 균제도")
            print(avg_illum, "\t", cct_now, "\t", avg_cct, "\t", uniformity)

            if (abs(illum - avg_illum) > 20):

                scale = (abs(illum - avg_illum) / 30)
                if scale - int(scale) > 0.5:
                    scale = int(scale) + 1
                else:
                    scale = int(scale)

                print(scale, "이만큼!")
                if scale == 1:
                    count = count + 1

                if avg_illum < illum:
                    up_and_down = scale
                    print("+조정!")

                else:
                    up_and_down = -1 * scale
                    print("-조정!")

                # continue



            else:
                print("완벽!")
                # 여기서 색온도 디밍 한번 더 해야함. 원래는...
                result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                         columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
                print(result_pd)

                LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
                # IMDB.Log_2_Mongo2(LED_pd, data_pd, result_pd)
                # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, task_type)

                break

        # 1분주기로 반복.(카스 재측정시간)
        # time.sleep(10)

        cct_now = cct_now + 10

        if cct_now > 8000:
            break


if __name__ == '__main__':
    process("step_1_diff_ver2")

    # 이걸 조도 만족할 때,  제어지표, 평균 색온도 를 데이터베이스에 저장해놓고, 실제 제어 할때마다 플마 50K의 기준으로 평균색온도를 검색.
    # 이때 있으면 그거 틀고 없으면 디밍 하고. 이렇게하면 실제 타겟색온도를 제어지표에서 따라가는게 아니고 실제 틀었던 경험으로 제어하는 것이기 때문에
    # 디밍 횟수가 점차 0으로 수렴.

    # 이렇게 만들어놓은 암막상태의 데이터를 기준으로, 이후 창 개방시에도 우선 DB 기준으로 틀고, 끌꺼끄고, 조도 올리면 좋을듯.

    # 경험에 의한 제어지표 세트를 만드는거지, 조도 500을 만족하는 색온도별 조명별. 제어지표(조도비는 일섭이꺼 실험군에 기반함.)

    # 근데 지금 색온도가 조금 잘 안맞을 수도 있음 이건 하면서 최초 검색기준을 조금 빡세게 해보고 그래도 개선불가능하면 구역별로 비율을 개입해야 할수도 있음.
