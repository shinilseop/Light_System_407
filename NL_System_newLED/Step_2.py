import Core.blind as blind
from statistics import stdev
from Core import crawler_los as clos
import pandas as pd
from MongoDB import Load_MongoDB as LMDB
from MongoDB import Insert_MongoDB as IMDB
import datetime
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

def sensing_only_illum():
    II1 = II.getInstance()

    for i in range(1, 10):
        II1.set_illum_data(i - 1, 0)
    data_flag = True
    data_count = 0
    while data_flag:
        # print(data_count)
        data_flag = False

        II_illum = II1.get_illum_data()[:9]

        for i in II_illum:
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
    data = II1.get_illum_data()[:9]
    print(data)
    return data

def check_only_illum():
    temp = sensing_only_illum()
    check = True
    for i in temp:
        if 600<=i and i<=620:
            check = True
        else:
            check = False
    avg = np.average(temp)
    if 600<=avg and avg<=620:
        if 600 <= i and i <= 620:
            check = True
        else:
            check = False

    return check

def sensing_data(cct_now):
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    acs_cct = acs1.get_sensor_data()[0][:10]
    II_illum = II1.get_illum_data()[:10]
    IC_curr = IC1.get_curr_data()[:10]

    print("????????? ????????????(92??????)", stdev(acs_cct[:9]))
    print("?????? ????????????(18??????)", stdev(II_illum[:9]))

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

    print("????????????\t ?????? ?????????\t ?????? ?????????\t ?????????")
    print(avg_illum, "\t", cct_now, "\t", avg_cct, "\t", uniformity)

    return data_pd, avg_illum, cct_now, avg_cct, uniformity

def dimming_illum(temp_df, temp, target_illum, cct_now):
    target_illum1 = [0,0,0,0,0,0,
                     0,0,0,0,0,0,
                     0,0,0,0,0,0,
                     0,0,0,0,0,0,
                     0,0,0,0,0,0]
    count = 0
    first = True
    up_and_down = 0
    while count < 5:
        if first:
            for i in range(len(target_illum)):
                target_illum1[i] = find_nearest(temp, target_illum[i])
                print("????????????!", target_illum[i])
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

        #  ????????? ????????? ????????? ????????? ??????
        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)

        if (abs(500 - avg_illum) > 20):

            scale = (abs(500 - avg_illum) / 40)
            if scale - int(scale) > 0.5:
                scale = int(scale) + 1
            else:
                scale = int(scale)

            print(scale, "?????????!")
            if scale == 1:
                count = count + 1

            if avg_illum < 500:
                up_and_down = scale
                print("+??????!")

            else:
                up_and_down = -1 * scale
                print("-??????!")

            # continue

        else:
            print("??????!")
            result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                     columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
            print(result_pd)

            LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
            return 0

def blind_dimming(updown, currunt, altitude):
    change = currunt + (2.8*updown)
    if change > altitude :
        change = altitude
    elif change < -70:
        change = -70
    blind.ctrl_tilt(change)
    return change

def upscale_LED(led_state,i,nomal_index):
    total_index = int(sum(led_state[i - 1][1:]))

    ch1 = led_state[i-1][1]
    ch2 = led_state[i-1][2]
    ch3 = led_state[i-1][3]
    ch4 = led_state[i-1][4]

    up_num = np.count_nonzero(led_state[i - 1][1:])
    up_total = total_index+up_num*2
    if up_total > nomal_index[i-1]:
        up_total = nomal_index[i - 1]

    cut1 = int((up_total) * (ch1 / total_index))
    cut2 = int((up_total) * (ch2 / total_index))
    cut3 = int((up_total) * (ch3 / total_index))
    cut4 = int((up_total) * (ch4 / total_index))

    ILED.set_LED(i,cut1,cut2,cut3,cut4)
    print(i,cut1,cut2,cut3,cut4,up_total, nomal_index[i - 1])
    if up_total == nomal_index[i - 1]:
        return 1
    else:
        return 0

def downscale_LED(led_state,i,nomal_index):
    total_index = int(sum(led_state[i - 1][1:]))

    ch1 = led_state[i-1][1]
    ch2 = led_state[i-1][2]
    ch3 = led_state[i-1][3]
    ch4 = led_state[i-1][4]

    up_num = np.count_nonzero(led_state[i - 1][1:])
    down_total = total_index-up_num*2
    if down_total < up_num:
        down_total = up_num

    cut1 = int((down_total) * (ch1 / total_index))
    cut2 = int((down_total) * (ch2 / total_index))
    cut3 = int((down_total) * (ch3 / total_index))
    cut4 = int((down_total) * (ch4 / total_index))

    ILED.set_LED(i,cut1,cut2,cut3,cut4)
    print(i,cut1,cut2,cut3,cut4,down_total, nomal_index[i - 1])
    if down_total == up_num:
        return 1
    else:
        return 0

def update_dimming_index(dimming_index, LED_state):
    for i in range(len(dimming_index)):
        dimming_index[i] = int(sum(LED_state[i][1:]))
    return dimming_index

def process(tasktype):
    # ????????? ????????? ?????? ??????.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    nonfirst = False
    # current_angle=-70
    # blind.ctrl_tilt(current_angle)
    # ????????? ??????
    base = threading.Thread(target=bp.process)
    base.start()
    currunt =0
    # 500lux ???????????? ????????? 1???????????? ?????? ??????.new LED
    nomal_index = [50, 55, 23, 40, 60, 40,
                     20, 20, 15, 20, 15, 15,
                     30, 20, 25, 18, 25, 30,
                     40, 23, 20, 10, 15, 15,
                     40, 30, 25, 25, 60, 40]
    # ??????????????? ???????????????
    dimming_index = [50, 55, 23, 40, 60, 40,
                     20, 20, 15, 20, 15, 15,
                     30, 20, 25, 18, 25, 30,
                     40, 23, 20, 10, 15, 15,
                     40, 30, 25, 25, 60, 40]

    case_list = [
        [
            [
                0
            ],
            [
                1, 2, 3, 4, 5, 8, 9, 10
            ],
            [
                1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 15, 16
            ],
            [
                1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 15, 16, 17, 18, 22, 23, 24, 29, 30
            ]
        ],
        [
            [
                0
            ],
            [
                2, 3, 4, 5, 9, 10
            ],
            [
                1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 15, 16
            ],
            [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 30
            ]
        ],
        [
            [
                0
            ],
            [
                2, 3, 4, 5, 6, 9, 10, 11
            ],
            [
                1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 15, 16
            ],
            [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 19, 20, 21, 25, 26
            ]
        ]
    ]


    M = 3
    N = 0
    new_illum = 0
    last_illum = 0

    while True:
        mongo_df = load_NL_CCT_mongo()
        cct_now = float(mongo_df['CCT'].values[0])
        # cct_now = 6000
        print(cct_now)
        new_illum = float(mongo_df['Photometric'].values[0])
        today = datetime.date.today()
        year = today.year
        month = today.month
        day = today.day
        los_df = clos.Los(year, month, day)
        #??????
        azimuth = float(los_df['kasi_azimuth'][0])-90
        # azimuth = 110
        #??????
        altitude = float(los_df['kasi_altitude'][0])
        # altitude = 15
        # print(azimuth)
        # print(altitude)


        # ????????? ?????????
        old_N = N
        N = int(azimuth / 60)

        # log?????? ?????? cct ??? ?????? ????????? ????????? ??????.
        temp = lll.process('result')
        backup = temp
        temp["avg_cct"] = temp["avg_cct"].astype(float)
        temp = temp['avg_cct'].values
        log_cct = find_nearest(temp, cct_now)

        def control(temp, cct_now, N ,M, nonfirst = True, dimming_case = None, control_index = dimming_index, blind_flag = False, blind_updown = -1, azimuth_flag = False):

            if dimming_case is not None:
                for i in dimming_case:
                    control_index[i-1] = 1

            if abs(cct_now - log_cct) < 50:
                print("?????? ??????!", cct_now, log_cct)
                idx = find_nearest_index(temp, cct_now)
                lll.get_LED_state2('LED_State', str(backup.loc[idx, "_id"]), control_index)

            else:
                # ??????????????? ????????? ?????????(?????? ?????? ????????? ?????? ??????. ??????????????? ?????? ????????? 50k????????? ???????????????????????????)
                # ????????? ?????? ???????????? ???????????? ???????????? ?????? ?????? ????????? ?????? ?????????.

                print("?????? ?????????..!")
                control_pd = pd.read_csv("../LEDcontrol_list_NEW.csv")
                control_pd["illum"] = control_pd["illum"].astype(float)
                control_pd["cct"] = control_pd["cct"].astype(float)
                mask = (control_pd.cct >= cct_now - 25) & (
                            control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
                # print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct', 'total_index']])
                temp = control_pd[mask]['total_index'].values
                temp_df = control_pd[mask]
                temp_df = temp_df.reset_index(drop=True)

                # ????????? ???????????? ?????? ?????????????????? ????????? ???????????? ??????...? 4000K?????? ?????????
                if len(temp_df)<1:
                    cct_now = 4000
                    mask = (control_pd.cct >= cct_now - 25) & (
                            control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
                    temp = control_pd[mask]['total_index'].values
                    temp_df = control_pd[mask]
                    temp_df = temp_df.reset_index(drop=True)
                    dimming_illum(temp_df, temp, nomal_index, cct_now)
                    return M
                # ????????? ??????????????? ??????????????? ?????? ????????? ???????????? ??? ???????????? ??????????????? 30??? ?????? ????????? ?????? ??????, ???????????? ??????
                dimming_illum(temp_df, temp, nomal_index, cct_now)

                sensing_data_check()
                data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
                result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                         columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
                LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
                # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, "step_1_diff_cal_illum_newLED")
                return -1

            #???????????? ??????.
            if (nonfirst is False) or (blind_flag and azimuth_flag):
                print("????????? ??????, ????????????+????????????")

                # ???????????? ????????????
                blind.ctrl_tilt(altitude)
                currunt = altitude
                while max(sensing_only_illum()) >= 620:
                    currunt = blind_dimming(blind_updown, currunt, altitude)
                    print(currunt)
                    if currunt == -70:
                        break

                # ????????? ?????????, ????????? ??????
                dimming_finish = True
                while dimming_finish:
                    Set_case_N = set(case_list[N][M])
                    Set_case_Nm1 = set(case_list[N][M-1])
                    diff_case = Set_case_N-Set_case_Nm1
                    diff_case = list(diff_case)
                    diff_case.sort()
                    depth = int(max(diff_case)/6)
                    if max(diff_case)%6==0:
                        depth = depth-1

                    finish_control =0
                    while finish_control<len(diff_case):
                        finish_control = 0
                        for j in range(depth,depth-M-1,-1):
                            for i in diff_case:
                                depth_temp = int(i / 6)
                                if i % 6 == 0:
                                    depth_temp = depth_temp - 1
                                if depth_temp >= j:
                                    led_state = ILED.get_LED_state()
                                    finish_control = finish_control + upscale_LED(led_state,i,nomal_index)
                            if check_only_illum():
                                dimming_finish = False
                                return M

                    M = M-1
                    if M == 0:
                        lll.get_LED_state2('LED_State', str(backup.loc[idx, "_id"]), nomal_index)
                        return M+1

            else:

                if blind_flag:
                    # ?????? ???????????????
                    if blind_updown == -1:
                        print("????????????, ?????? ?????????")
                        # M ??????????????? ?????? ?????????
                        off = case_list[N][M]
                        off.sort()
                        depth = int(max(off) / 6)
                        if max(off) % 6 == 0:
                            depth = depth - 1

                        finish_control = 0
                        while finish_control < len(off):
                            finish_control = 0
                            for j in range(depth - 2, depth + 1):
                                print(j)
                                for i in off:
                                    depth_temp = int(i / 6)
                                    if i % 6 == 0:
                                        depth_temp = depth_temp - 1
                                    if depth_temp <= j:
                                        led_state = ILED.get_LED_state()
                                        finish_control = finish_control + downscale_LED(led_state, i, nomal_index)
                                if check_only_illum():
                                    break
                        # ???????????? ????????? ??????
                        while max(sensing_only_illum()) >= 620:
                            currunt = blind_dimming(blind_updown, currunt, altitude)
                        # ????????? ?????????, ????????? ??????
                        dimming_finish = True
                        while dimming_finish:
                            Set_case_N = set(case_list[N][M])
                            Set_case_Nm1 = set(case_list[N][M - 1])
                            diff_case = Set_case_N - Set_case_Nm1
                            diff_case = list(diff_case)
                            diff_case.sort()
                            depth = int(max(diff_case) / 6)
                            if max(diff_case) % 6 == 0:
                                depth = depth - 1

                            finish_control = 0
                            while finish_control < len(diff_case):
                                finish_control = 0
                                for j in range(depth, depth - M - 1, -1):
                                    for i in diff_case:
                                        depth_temp = int(i / 6)
                                        if i % 6 == 0:
                                            depth_temp = depth_temp - 1
                                        if depth_temp >= j:
                                            led_state = ILED.get_LED_state()
                                            finish_control = finish_control + upscale_LED(led_state, i, nomal_index)
                                    if check_only_illum():
                                        dimming_finish = False
                                        return M

                            M = M - 1
                            if M == 0:
                                lll.get_LED_state2('LED_State', str(backup.loc[idx, "_id"]), nomal_index)
                                return M + 1


                    # ?????? ??????????????????
                    else:
                        print("????????????, ?????? ????????????")
                        # ?????? ???????????? ???????????? ?????? ?????? ??????
                        while max(sensing_only_illum()) <= 600:
                            currunt = blind_dimming(blind_updown, currunt, altitude)
                            # ????????? ?????????????????? ?????????????????? ????????????
                            if currunt == altitude:
                                break

                        # ????????? ?????????, ????????? ??????
                        dimming_finish = True
                        while dimming_finish:
                            Set_case_N = set(case_list[N][M])
                            Set_case_Nm1 = set(case_list[N][M - 1])
                            diff_case = Set_case_N - Set_case_Nm1
                            diff_case = list(diff_case)
                            diff_case.sort()
                            depth = int(max(diff_case) / 6)
                            if max(diff_case) % 6 == 0:
                                depth = depth - 1

                            finish_control = 0
                            while finish_control < len(diff_case):
                                finish_control = 0
                                for j in range(depth, depth - M - 1, -1):
                                    for i in diff_case:
                                        depth_temp = int(i / 6)
                                        if i % 6 == 0:
                                            depth_temp = depth_temp - 1
                                        if depth_temp >= j:
                                            led_state = ILED.get_LED_state()
                                            finish_control = finish_control + upscale_LED(led_state, i, nomal_index)
                                    if check_only_illum():
                                        dimming_finish = False
                                        return M

                            M = M - 1
                            if M == 0:
                                lll.get_LED_state2('LED_State', str(backup.loc[idx, "_id"]), nomal_index)
                                return M + 1
                    # print("1. ???????????? ???????????? ??????(??? ??????????????? ????????????, ??? ??????????????? ????????????)??? ????????? ????????? ????????? ????????? ????????? ???????????? ??????,"
                    #       "1-1. ??????, ??? ???????????? m??????????????? ????????? ???????????? ????????? ?????? 520?????? ???????????? ?????? ?????????,"
                    #   "1-2. ??? ??????????????? ???????????? ????????? ??? ??????. ??????????????? ???????????? ???????????? ?????? ????????? ????????????. // ????????? ????????? ??????, ????????? ????????????.")
                elif azimuth_flag:
                    print("????????? ?????? ????????????")
                    return control(temp, cct_now, nonfirst = False, dimming_case=case_list[N][M],N=N,M=M)
                    # print("2. ????????? ?????? ??????(?????????.. ????????? ????????? ???????????? ??????, ???????????? ????????? ??????????????? ???, ????????? 1~m????????? ????????? ?????????.?????? ??????????????? ????????????")


        if nonfirst is False:
            M = control(temp, cct_now, nonfirst = nonfirst, dimming_case=case_list[N][M],N=N,M=M)
            dimming_index = update_dimming_index(dimming_index, ILED.get_LED_state())
            if M == -1:
                M=3
                continue
            nonfirst = True

        else:
            blind_flag = False
            azimuth_flag = False
            blind_updown = 0
            # ???????????? ????????? ??? ????????????, ??????????????? ???????????? ???????????? ????????????????????? 500lux?????? ???????????? ?????????
            if currunt == -70 and abs(last_illum-new_illum)>500:
                blind_flag = True
                if last_illum < new_illum:
                    blind_updown = -1
                else:
                    blind_updown = 1
            #??????????????? ?????? ????????? ????????? ????????? ?????????, ??????????????? 500~520 ????????? ??????????????? ?????????
            if currunt != -70:
                if check_only_illum() is False:
                    blind_flag = True
                    if last_illum < new_illum:
                        blind_updown = -1
                    else:
                        blind_updown = 1

                    # ??????????????? ????????? ??????????????? 520 ????????????, ???????????? ?????? ??????????????? ????????? ?????? ??????
                    if np.average(sensing_only_illum())<=620:
                        if dimming_index==nomal_index:
                            blind_flag = False
            #????????? ?????? ????????? ?????? ??????????????? ???.
            if old_N != N :
                azimuth_flag = True


            M = control(temp, cct_now, dimming_case=case_list[N][M],N=N,M=M, blind_updown=blind_updown, blind_flag = blind_flag, azimuth_flag = azimuth_flag)
            dimming_index = update_dimming_index(dimming_index, ILED.get_LED_state())
            if M == -1:
                M = 3
                continue
            if blind_flag:
                last_illum = new_illum

        ####################################################################################

        sensing_data_check()
        data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
        result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                 columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
        LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
        # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, tasktype)
        # input("continue? (press any key) :")

        # ###################################################################################################


if __name__ == '__main__':
    process("test")
