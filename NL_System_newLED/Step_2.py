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

        if (abs(500 - avg_illum) > 20):

            scale = (abs(500 - avg_illum) / 40)
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
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    nonfirst = False
    # current_angle=-70
    # blind.ctrl_tilt(current_angle)
    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()
    currunt =0
    # 500lux 기준으로 했을때 1번채널의 실제 값들.new LED
    nomal_index = [50, 55, 23, 40, 60, 40,
                     20, 20, 15, 20, 15, 15,
                     30, 20, 25, 18, 25, 30,
                     40, 23, 20, 10, 15, 15,
                     40, 30, 25, 25, 60, 40]
    # 그때마다의 디밍인덱스
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
        #방위
        azimuth = float(los_df['kasi_azimuth'][0])-90
        # azimuth = 110
        #고도
        altitude = float(los_df['kasi_altitude'][0])
        # altitude = 15
        # print(azimuth)
        # print(altitude)


        # 케이스 초기화
        old_N = N
        N = int(azimuth / 60)

        # log에서 해당 cct 에 가장 적합한 색온도 찾기.
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
                print("로그 찾음!", cct_now, log_cct)
                idx = find_nearest_index(temp, cct_now)
                lll.get_LED_state2('LED_State', str(backup.loc[idx, "_id"]), control_index)

            else:
                # 제어가능한 로그를 못찾음(이건 사실 들어올 일이 없음. 제어가능한 모든 구간을 50k단위로 측정해두었기때문에)
                # 오히여 여기 들어오면 야간으로 인식하고 야간 고정 조명을 켜야 할수도.

                print("로그 못찾음..!")
                control_pd = pd.read_csv("../LEDcontrol_list_NEW.csv")
                control_pd["illum"] = control_pd["illum"].astype(float)
                control_pd["cct"] = control_pd["cct"].astype(float)
                mask = (control_pd.cct >= cct_now - 25) & (
                            control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
                # print(control_pd[mask][['idx', 'ch.1', 'ch.2', 'ch.3', 'ch.4', 'illum', 'cct', 'total_index']])
                temp = control_pd[mask]['total_index'].values
                temp_df = control_pd[mask]
                temp_df = temp_df.reset_index(drop=True)

                # 혹시나 로그에도 없고 제어지표에도 없으면 야간으로 간주...? 4000K고정 서비스
                if len(temp_df)<1:
                    cct_now = 4000
                    mask = (control_pd.cct >= cct_now - 25) & (
                            control_pd.cct <= cct_now + 25)  # & (control_pd.zero_count<=2)
                    temp = control_pd[mask]['total_index'].values
                    temp_df = control_pd[mask]
                    temp_df = temp_df.reset_index(drop=True)
                    dimming_illum(temp_df, temp, nomal_index, cct_now)
                    return M
                # 로그는 못찾앗지만 제어지표로 다시 만들수 있었다면 그 색온도의 제어지표로 30개 세트 만들고 로그 추가, 프로세스 스킵
                dimming_illum(temp_df, temp, nomal_index, cct_now)

                sensing_data_check()
                data_pd, avg_illum, cct_now, avg_cct, uniformity = sensing_data(cct_now)
                result_pd = pd.DataFrame([[avg_illum, cct_now, avg_cct, uniformity]],
                                         columns=['avg_illum', 'cct_now', 'avg_cct', 'uniformity'])
                LED_pd = pd.DataFrame(ILED.get_LED_state(), columns=['LED_No', 'ch1', 'ch2', 'ch3', 'ch4'])
                # IMDB.Log_2_Mongo_tasktype(LED_pd, data_pd, result_pd, "step_1_diff_cal_illum_newLED")
                return -1

            #작동여부 확인.
            if (nonfirst is False) or (blind_flag and azimuth_flag):
                print("부팅시 제어, 블라인드+방위변동")

                # 블라인드 최대개방
                blind.ctrl_tilt(altitude)
                currunt = altitude
                while max(sensing_only_illum()) >= 620:
                    currunt = blind_dimming(blind_updown, currunt, altitude)
                    print(currunt)
                    if currunt == -70:
                        break

                # 조명의 구역별, 깊이별 디밍
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
                    # 밖이 밝아졌을때
                    if blind_updown == -1:
                        print("블라인드, 밖이 밝아짐")
                        # M 레벨까지는 우선 꺼보기
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
                        # 블라인드 조금씩 닫기
                        while max(sensing_only_illum()) >= 620:
                            currunt = blind_dimming(blind_updown, currunt, altitude)
                        # 조명의 구역별, 깊이별 디밍
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


                    # 밖이 어두워졌을때
                    else:
                        print("블라인드, 밖이 어두워짐")
                        # 우선 블라인드 가능범위 내로 좀더 열어
                        while max(sensing_only_illum()) <= 600:
                            currunt = blind_dimming(blind_updown, currunt, altitude)
                            # 혹시나 최대개방인데 무한반복이면 멈추게함
                            if currunt == altitude:
                                break

                        # 조명의 구역별, 깊이별 디밍
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
                    # print("1. 블라인드 제어여부 설정(다 닫았을때는 외부조도, 좀 열었을때는 내부조도)에 따라서 조명을 조금씩 끄거나 조금씩 켜는기능 추가,"
                    #       "1-1. 이때, 더 밝아지면 m레벨까지만 다끄고 블라인드 조금씩 닫고 520까지 내려오면 조명 업디밍,"
                    #   "1-2. 더 어두워지면 블라인드 열면서 빛 확보. 고도각까지 블라인드 올렸는데 만족 못하면 조명더킴. // 조명을 끄는건 쉽게, 켜는건 깐깐하게.")
                elif azimuth_flag:
                    print("방위각 변동 재귀호출")
                    return control(temp, cct_now, nonfirst = False, dimming_case=case_list[N][M],N=N,M=M)
                    # print("2. 방위각 변동 확인(변동시.. 부팅시 제어랑 똑같이는 하되, 블라인드 각도는 유지하도록 함, 조명은 1~m까지만 꺼봐도 좋을것.물론 갱신하도록 수정하고")


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
            # 블라인드 각도가 다 닫혀있고, 외부조도가 블라인드 조절했던 마지막으로부터 500lux이상 차이나면 재조정
            if currunt == -70 and abs(last_illum-new_illum)>500:
                blind_flag = True
                if last_illum < new_illum:
                    blind_updown = -1
                else:
                    blind_updown = 1
            #블라인드가 다는 안닫혀 있는데 지점별 조도나, 평균조도가 500~520 범위를 벗어났다면 재조정
            if currunt != -70:
                if check_only_illum() is False:
                    blind_flag = True
                    if last_illum < new_illum:
                        blind_updown = -1
                    else:
                        blind_updown = 1

                    # 그와중에도 혹시나 평균조도는 520 이하인데, 킬수있는 표준 인덱스만큼 켰다면 조절 면제
                    if np.average(sensing_only_illum())<=620:
                        if dimming_index==nomal_index:
                            blind_flag = False
            #방위각 영역 바뀌면 그냥 재조정하면 됨.
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
