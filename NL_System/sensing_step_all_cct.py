# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
import pandas as pd
from MongoDB import Load_MongoDB as LMDB
from MongoDB import Insert_MongoDB as IMDB
from MongoDB import Load_MongoDB_local_log as lll
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


def find_nearest_index(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


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


def process():
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()
    target_illum = 20
    target_illum1 = 0
    # 기준 조도, 색온도 설정
    cct_now = 2700

    while True:
        # print("실시간 cas cct :"+str(cct_now))
        #
        #
        # # log에서 해당 cct 에 가장 적합한 색온도 찾기.
        # #
        # # temp = lll.process('result')
        # # # print(temp)
        # # temp["avg_cct"] = temp["avg_cct"].astype(float)
        # # temp = temp['avg_cct'].values
        # # log_cct=find_nearest(temp, cct_now)
        #
        # # 이후 알고리즘들
        # # log에 적당한 제어지표가 없으면 아래 실행
        #
        # # 제어지표 필터링.
        # control_pd = pd.read_csv("../LEDcontrol_list.csv")
        # control_pd["illum"] = control_pd["illum"].astype(float)
        # control_pd["cct"] = control_pd["cct"].astype(float)
        #
        # # 반복 포인트 if 를 더해서.
        # mask = (control_pd.cct >= cct_now - 50) & (control_pd.cct <= cct_now + 50)
        # # print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct']])
        # temp = control_pd[mask]['illum'].values
        # temp_df = control_pd[mask]
        # temp_df = temp_df.reset_index(drop=True)
        #
        # target_illum1 = find_nearest(temp, target_illum)
        # final_df = temp_df[temp_df['illum'] == target_illum1]
        #
        # ch1 = int(final_df['ch.1'].values[0])
        # ch2 = int(final_df['ch.2'].values[0])
        # ch3 = int(final_df['ch.3'].values[0])
        # ch4 = int(final_df['ch.4'].values[0])
        # # print(i+1,ch1, ch2, ch3, ch4)
        # ILED.all_set_LED(ch1, ch2, ch3, ch4)
        # print(ILED.get_LED_state())

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

            # print(acs_cct)
            # print(II_illum)
            # print(IC_curr)

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

        result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                 columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
        LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
        # IMDB.Log_2_Mongo2(LED_pd, data_pd, result_pd)

        cct_now = cct_now + 10
        time.sleep(10)

        if cct_now > 8500:
            break


if __name__ == '__main__':
    process()
