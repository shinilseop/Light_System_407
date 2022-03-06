# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
import pandas as pd
from MongoDB import Load_MongoDB as LMDB
from NL_System import Base_Process as bp
import numpy as np
import threading, time
from Core.arduino_color_sensor import acs
from Core.Intsain_Illum import II
from Core.Intsain_Curr import IC

import Shin_Package.others.shin_Intsain_LED as led

# 제어조건(변형가능)
led_lock_range = 2  # LED 잠금시 잠굴 범위 값
similar_led_range = 1  # 방향성고려나 제어조도기준 선정할 때 영향도의 비슷한 범위를 위한 값

# 저장 변수
df_record = []

# led control index
led_control = [[0, 0, 0, 0], [0, 16, 0, 0], [16, 8, 8, 0], [16, 16, 8, 8], [0, 32, 16, 0], [32, 0, 32, 0],
               [32, 16, 32, 0], [32, 32, 0, 16], [32, 32, 16, 16], [0, 64, 16, 16], [48, 16, 48, 0], [48, 32, 32, 16],
               [64, 32, 0, 32], [16, 64, 48, 0], [0, 80, 32, 16], [16, 80, 32, 16], [0, 80, 48, 0],
               [64, 16, 64, 0], [64, 32, 48, 16], [48, 64, 16, 32], [16, 96, 0, 32], [64, 32, 64, 0],
               [80, 32, 32, 32], [64, 48, 32, 32], [0, 112, 0, 32], [32, 80, 48, 16], [32, 96, 16, 32],
               [16, 112, 16, 32], [32, 80, 64, 0], [48, 80, 32, 32], [0, 112, 48, 16], [96, 16, 64, 16],
               [16, 112, 48, 16], [80, 32, 80, 0], [96, 48, 0, 48], [32, 112, 32, 32], [64, 64, 64, 16],
               [16, 128, 32, 32], [128, 0, 32, 48], [128, 16, 32, 48], [80, 64, 48, 32], [64, 96, 0, 48],
               [80, 80, 16, 48], [128, 32, 32, 48], [128, 0, 64, 32], [112, 16, 96, 0], [48, 112, 48, 32],
               [16, 128, 80, 0], [48, 128, 16, 48], [160, 16, 0, 64], [160, 16, 16, 63], [80, 64, 96, 0],
               [128, 0, 96, 16], [128, 16, 96, 15], [64, 96, 80, 15], [128, 64, 0, 63], [128, 16, 111, 0],
               [48, 112, 95, 0], [0, 192, 16, 47], [0, 160, 80, 15], [0, 160, 95, 0]]
led_control_lux = [0, 24, 46, 62, 77, 122, 138, 154, 168, 225, 254, 263, 310, 315, 322, 345, 353, 368, 377,
                   387, 395, 409, 416, 422, 431, 443, 450, 467, 475, 484, 498, 507, 519, 523, 532, 545, 557, 562, 571,
                   586, 594, 602, 612, 626, 636, 648, 660, 668, 676, 688, 696, 702, 713, 726, 733, 744, 756, 764, 773,
                   782, 813]  # 174, 295 제거

# init LED state
led_state_0 = [0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, ]
led_state = [0, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]

led_lock = [0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0]

# led inflence
sensor_influence = [[8, 2, 7, 9, 1, 3, 14, 15, 13],
                    [4, 3, 9, 10, 8, 5, 11, 2, 15, 16],
                    [5, 11, 12, 6, 10, 4, 17, 16, 18],
                    [14, 8, 20, 15, 13, 7, 19, 21, 9],
                    [15, 16, 9, 22, 21, 10, 14, 17, 8, 11, 20],
                    [17, 11, 23, 16, 18, 24, 22, 10, 12],
                    [20, 26, 19, 21, 27, 25, 14, 13, 15],
                    [28, 27, 21, 22, 23, 20, 29, 26, 15, 16],
                    [23, 29, 24, 28, 22, 30, 17, 16, 18]]
sensor_influence_value = [[94.5, 94.4, 58.3, 58.2, 58.1, 58.0, 29.4, 24.2, 24.1],
                          [76.7, 76.6, 76.6, 76.5, 38.1, 38.0, 38.0, 37.9, 26.8, 26.8],
                          [94.4, 94.4, 58.2, 58.1, 58.1, 58.0, 29.4, 24.2, 24.2],
                          [94.5, 62.1, 62.1, 58.1, 58.1, 41.2, 41.2, 41.2, 41.1],
                          [88.9, 88.3, 54.6, 54.4, 54.1, 54.0, 34.4, 34.4, 25.9, 25.8, 24.5],
                          [94.6, 62.2, 62.2, 58.2, 58.1, 41.3, 41.2, 41.1, 41.1],
                          [94.8, 94.3, 58.1, 58.1, 58.1, 58.0, 29.6, 24.2, 24.2],
                          [76.7, 76.6, 76.5, 76.5, 38.1, 38.1, 38.0, 37.9, 26.8, 26.8],
                          [94.7, 94.3, 58.2, 58.2, 58.0, 58.0, 29.5, 24.2, 24.2]]


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def load_NL_CCT_mongo():
    step_data = LMDB.load_last1_cct()
    step_df = LMDB.mongodb_to_df(step_data, 'mongo_cas')
    step_df = step_df.reset_index(drop=True)
    return step_df


def process():
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()

    first = True
    get_times = 0
    wait_curr = 0
    wait_illum=[0,0,0,0,0,0,0,0,0]

    # 제어 반복
    while True:
        # 센서 데이터 받아옴
        acs_cct = acs1.get_sensor_data()[0][:9]
        II_illum = II1.get_illum_data()[:9]
        IC_curr = IC1.get_curr_data()[:10]
        min_illum = 10000
        sum_cct = 0.0
        sum_curr = -wait_curr
        uniformity = 0.0

        #대기조도 제외
        for i in range(9):
            II_illum[i]-=wait_illum[i]

        # 단위구역이 연속하는경우 KS C 7612 기준 평균 계산법
        sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[5] * 2 + \
                    II_illum[6] + II_illum[7] * 2 + II_illum[8]

        # 값 통합 및 평균 산출 + 출력
        data_pd = pd.DataFrame(acs_cct, columns=['cct'])
        print("\n\n\t\t측정데이터", str(get_times), "STEP")
        print("P\t\tCCT\t\tIllum\t\tCurr")
        for i in range(9):
            data_pd.loc[i, 'illum'] = II_illum[i]
            data_pd.loc[i, 'curr'] = IC_curr[i]
            print(str(i + 1) + "\t\t" + str(acs_cct[i])[:7] + "\t\t" + str(II_illum[i])[:7] + "\t\t" + str(IC_curr[i]))
            sum_cct += acs_cct[i]
            sum_curr += IC_curr[i]
            if (min_illum > II_illum[i]):
                min_illum = II_illum[i]
        print("10\t\t-1\t\t-1\t\t" + str(IC_curr[9]))
        avg_illum = sum_illum / 16
        avg_cct = sum_cct / 9
        sum_curr += IC_curr[9]
        if (avg_illum != 0):
            uniformity = min_illum / avg_illum

        print(
            "Avg_CCT\t\t%s\t\tAvg_Ill\t\t%s\t\tSum_Curr\t\t%s" % (str(avg_cct)[:7], str(avg_illum)[:8], str(sum_curr)))

        # 센서 데이터 출력
        # print("\n\n\t\t측정데이터", str(get_times))
        # print(data_pd)
        # print("Avg_Ill %s Avg_CCT %s Sum_Curr %s" % (avg_illum, avg_cct, sum_curr))

        # 500보다 미만 -> 상승하러 & 500 이상 -> 낮추러 (gettimes는 처음 시작할때 처음 상태 때문에 설정)
        if first:
            # 대기전력 측정
            if sum_curr > 0:
                get_times += 1
                wait_curr = sum_curr
                print("대기전력 : %s" % wait_curr)
                print("대기조도")
                for i in range(9):
                    wait_illum[i]=II_illum[i]
                    print(str(i+1)+" wait illum : "+str(wait_illum[i]))
                led_control_use_state(led_control, led_state)
                time.sleep(10)
                first = False
            # first = False
        else:
            get_times += 1
            if (avg_illum < 500):
                print("NOT ENOUGH ILLUMINATION")
                illum_before_needs(II_illum)
            elif (avg_illum >= 500):
                print("TOO MUCH ENOUGH ILLUMINATION")
                illum_after_needs(II_illum)

            # 기준을 만족하는 경우랑 일반의 경우 step 별로 저장
            if (490 <= avg_illum) & (avg_illum <= 510):
                save_data(df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, get_times, "_success")
            else:
                save_data(df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, get_times, "")


        print_control_lux()
        time.sleep(10)


def save_data(df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, get_times, save_name):
    for ill_idx in range(len(II_illum)):
        if (480 > II_illum[ill_idx]) | (II_illum[ill_idx] > 520):
            break
        if ill_idx == 8:
            led_num_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                            25, 26, 27, 28, 29, 30]
            df_record.append(pd.DataFrame(led_num_list, columns=['led']))
            for idx in range(1, len(led_state)):
                df_record[len(df_record) - 1].loc[idx - 1, 'control'] = led_control_lux[led_state[idx]]
                if (idx < 10):
                    df_record[len(df_record) - 1].loc[idx - 1, 'cct'] = acs_cct[idx-1]
                    df_record[len(df_record) - 1].loc[idx - 1, 'illum'] = II_illum[idx-1]
                    df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = IC_curr[idx-1]
                elif (idx < 11):
                    df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = IC_curr[idx-1]
            df_record[len(df_record) - 1].loc[10, 'cct'] = avg_cct
            df_record[len(df_record) - 1].loc[10, 'illum'] = avg_illum
            df_record[len(df_record) - 1].loc[10, 'curr'] = sum_curr
            df_record[len(df_record) - 1].loc[0, 'uniformity'] = uniformity

            print('=' * 20)
            print(df_record[len(df_record) - 1])
            print('=' * 20)

            df_record[len(df_record) - 1].to_csv(
                "D:\\BunkerBuster\\Desktop\\shin_excel\\24시작\\[%s]_step%s.csv" % (
                    get_times, save_name))


# 현재 컨트롤 lux 상태 출력
def print_control_lux():
    print("Control Lux")
    for idx in range(1, len(led_state)):
        print("%s\t" % led_control_lux[led_state[idx]], end='')
        if idx % 6 == 0:
            print()

    print("LED state")
    for idx in range(1, len(led_state)):
        print("%s\t" % led_state[idx], end='')
        if idx % 6 == 0:
            print()


# LED 해당 단계로 조절
def control_led(led_num, control_step):
    led.set_LED(led_num, led_control[control_step][0], led_control[control_step][1], led_control[control_step][2],
                led_control[control_step][3])


def illum_before_needs(II_illum):
    min_sensor = 0

    # 최소 지점 선정
    for i in range(9):
        if II_illum[i] < II_illum[min_sensor]:
            min_sensor = i

    # 제어할 LED 선정
    control_led_idx = sensor_influence[min_sensor][0]
    # 방향성 고려 선정
    # control_led_idx = up_search_consider_orientation();

    # 높힐 LED 선정 (잠금 X, 제어 상태 최고 X)
    if (led_lock[control_led_idx] == 1) | (led_state[control_led_idx] == len(led_control) - 1):
        print("LOCKING DETECTED")
        for idx in range(len(sensor_influence[min_sensor])):
            if (led_lock[sensor_influence[min_sensor][idx]] == 0) & (
                    led_state[sensor_influence[min_sensor][idx]] != len(led_control) - 1):
                control_led_idx = sensor_influence[min_sensor][idx]
                break
            if idx == len(sensor_influence[min_sensor]) - 1:
                print("DEAD LOCK[ALL LOCK]")
                exit()

    # 선정 LED 한단계 상승
    print("MIN LOCATION IS " + str(min_sensor + 1) + ", Control LED : " + str(control_led_idx))
    print(
        "NOW Lux : " + str(led_control_lux[led_state[control_led_idx]]) + ", CONTROL[UP] : " + str(
            led_control_lux[led_state[control_led_idx] + 1]))
    led_state[control_led_idx] += 1
    control_led(control_led_idx, led_state[control_led_idx])


def up_search_consider_orientation(min_sensor):
    select_rank = 0

    return select_rank


def illum_after_needs(II_illum):
    max_sensor = 0

    # 최고 지점 선정
    for i in range(9):
        if II_illum[i] > II_illum[max_sensor]:
            max_sensor = i

    # 2번 [비슷한 영향도 중 제어조도가 가장 낮은 조명]
    control_rank = down_search_similar_influenced_led(max_sensor)
    control_led_idx = sensor_influence[max_sensor][control_rank]

    # 조명 다운
    print("MAX LOCATION IS " + str(max_sensor + 1) + ", Control LED : " + str(control_led_idx))
    print(
        "NOW Lux : " + str(led_control_lux[led_state[control_led_idx]]) + ", CONTROL[DOWN] : " + str(
            led_control_lux[led_state[control_led_idx] - 1]))
    led_state[control_led_idx] -= 1
    control_led(control_led_idx, led_state[control_led_idx])

    # 잠금할 조명 번호 체크
    stand_influence = sensor_influence_value[max_sensor][control_rank] - led_lock_range
    lock_list = []
    for j in range(len(sensor_influence_value[max_sensor])):
        if (led_lock[sensor_influence[max_sensor][j]] == 0) & (
                sensor_influence_value[max_sensor][j] >= stand_influence):
            lock_list.append(sensor_influence[max_sensor][j])

    # 잠금
    led_locking(lock_list)


# 방법 1 : 낮출 조명 선정 (제어단계가 1단계가 아닌 애들중에 영향도가 가장 높은 조명)
def select_down_led(max_sensor):
    lock_rank = 0
    control_led_idx = sensor_influence[max_sensor][0]
    if led_state[control_led_idx] == 1:
        for idx in range(len(sensor_influence[max_sensor])):
            if led_state[sensor_influence[max_sensor][idx]] != 1:
                control_led_idx = sensor_influence[max_sensor][idx]
                lock_rank = idx
                break
            if idx == len(sensor_influence[max_sensor]) - 1:
                print("DEAD LOCK[ALL 1step control]")
                exit()

    return [control_led_idx, lock_rank]


# 방법 2 : 비슷한 영향도 중 제어조도 단계가 가장 높은놈을 기준으로 낮출 조명 선정
def down_search_similar_influenced_led(max_sensor):
    led_rank = 0

    # 센서에 미치는 영향도가 20% 이상인 조명중 1단계가 아닌 가장 영향도가 높은 조명
    for idx in range(len(sensor_influence[max_sensor])):
        if led_state[sensor_influence[max_sensor][idx]] != 1:
            led_rank = idx
            break
    print("DOWN FIRST SELECT :", sensor_influence[max_sensor][led_rank])

    select_rank = led_rank
    print("[%s]:%s" % (select_rank, sensor_influence[max_sensor][select_rank]))
    for idx in range(led_rank + 1, len(sensor_influence[max_sensor])):
        # 조명의 영향도가 처음 선정된 조명의 1(변동가능)+-에 존재하면서 제어조도가 가장 높은놈. + 제어조도가 1단계 보다는 높아야됨 (최소치)
        if (sensor_influence_value[max_sensor][led_rank] - similar_led_range <= sensor_influence_value[max_sensor][
            idx]) & (
                sensor_influence_value[max_sensor][idx] <= sensor_influence_value[max_sensor][
            led_rank] + similar_led_range) & (
                led_state[sensor_influence[max_sensor][select_rank]] < led_state[sensor_influence[max_sensor][idx]]) & (
                led_state[sensor_influence[max_sensor][idx]] != 1
        ):
            select_rank = idx
            print("DOWN SELECT :", sensor_influence[max_sensor][idx])

    return select_rank


# 방법 3 : 방향성을 고려해서 조명의 주변중 가장 낮은 조도를 찾고 그놈에 영향을 가장 많이 미치는 놈을 조정(단, 최소단계 1단계면 선정 X)
def down_search_consider_orientation():
    select_rank = 0

    return select_rank


# led 잠금
def led_locking(led_arr):
    print("Locking : ", end='')
    for led_num in led_arr:
        led_lock[led_num] = 1
        print(led_num, "", end='')
    print()


def led_control_use_state(led_control, control_state):
    print("LED SETTING...")
    for idx in range(1, len(control_state)):
        ch1 = led_control[control_state[idx]][0]
        ch2 = led_control[control_state[idx]][1]
        ch3 = led_control[control_state[idx]][2]
        ch4 = led_control[control_state[idx]][3]
        led.set_LED(idx, ch1, ch2, ch3, ch4)
        time.sleep(0.2)
        # print("[" + str(idx) + "]:" + str(led_state[idx]) + "\t", end='')
        # if (idx != 0) & (idx % 6 == 0):
        #     print()
    print("FINISH")


# led_state = [0,
#              1, 1, 1, 5, 9, 1,
#              1, 13, 1, 1, 1, 1,
#              1, 1, 3, 1, 5, 1,
#              1, 10, 1, 1, 9, 1,
#              1, 1, 1, 6, 1, 1]
# led_state = [0,
#              1, 5, 1, 5, 9, 1,
#              1, 9, 1, 1, 1, 1,
#              1, 1, 3, 1, 5, 1,
#              1, 10, 1, 1, 10, 1,
#              1, 2, 1, 6, 1, 1]
led_state = [0,
             5, 5, 5, 5, 5, 5,
             1, 4, 4, 4, 4, 1,
             1, 1, 3, 3, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]

led_state_66_passive = [0,
                        1, 5, 1, 4, 12, 1,
                        2, 8, 3, 1, 1, 1,
                        1, 1, 3, 3, 4, 1,
                        1, 9, 1, 2, 11, 1,
                        1, 3, 1, 6, 1, 1]

if __name__ == '__main__':
    # receive_thread_udp=threading.Thread(target=udp.udp_receive())
    # receive_thread_udp.start()

    # init led
    led_control_use_state(led_control, led_state_0)

    # start
    process()
