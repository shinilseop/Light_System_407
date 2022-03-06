from datetime import datetime

import pandas as pd

import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.datas as datas

# 스텝별로 제어 상태, 센서 값 저장하는 함수
def save_data(start, avg_cct, avg_illum, sum_curr, uniformity, get_times,
              save_name,
              isPrint):
    df_record=[]
    step_end = datetime.now()
    led_num_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                    25, 26, 27, 28, 29, 30]
    df_record.append(pd.DataFrame(led_num_list, columns=['led']))
    for idx in range(1, len(datas.led_state)):
        df_record[len(df_record) - 1].loc[idx - 1, 'control'] = datas.led_control_lux[datas.led_state[idx]]
        if (idx < 10):
            df_record[len(df_record) - 1].loc[idx - 1, 'cct'] = datas.acs_cct[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'illum'] = datas.II_illum[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = datas.IC_curr[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'natural_light'] = datas.illum_add[idx - 1]
        elif (idx < 11):
            df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = datas.IC_curr[idx - 1]
    df_record[len(df_record) - 1].loc[10, 'cct'] = avg_cct
    df_record[len(df_record) - 1].loc[10, 'illum'] = avg_illum
    df_record[len(df_record) - 1].loc[10, 'curr'] = sum_curr
    df_record[len(df_record) - 1].loc[0, 'uniformity'] = uniformity
    df_record[len(df_record) - 1].loc[0, 'start'] = start
    df_record[len(df_record) - 1].loc[0, 'end'] = step_end
    df_record[len(df_record) - 1].loc[0, 'diff_time'] = step_end - start

    for i in range(len(datas.illum_change_time)):
        df_record[len(df_record) - 1].loc[i, 'illum_change_time'] = datas.illum_change_time[i]

    if (isPrint):
        print('=' * 20)
        # print(df_record[len(df_record) - 1])
        print('====save_success====')
        print('=' * 20)

    df_record[len(df_record) - 1].to_csv(
        "%s\\%s\\[%s]_step%s.csv" % (
            datas.path, datas.save_folder, get_times, save_name))
    print(start, "->", step_end)

def print_all():
    # 현재 데이터 상태 출력
    # print_control_lux()
    # print_led_locking_state(datas.led_up_lock, "UP")
    # print_led_locking_state(datas.led_down_lock, "DOWN")
    # # print_sensor_locking_state()
    # print_natural_light_state()
    # print_cal_lux()
    # print_real_lux()

    ##### new Printer
    print_led_state()
    print_sensor_lux_state()

def print_led_state():
    print("%30s%31s%31s"%('Control Lux', 'LED UP LOCK', 'LED DOWN LOCK'))
    for idx in range(1, len(datas.led_state), 6):
        for j in range(0, 6):
            print("%05s" % datas.led_control_lux[datas.led_state[idx+j]], end='')
        print('|', end='')
        for j in range(0, 6):
            print("%05s" % datas.led_up_lock[idx+j], end='')
        print('|', end='')
        for j in range(0, 6):
            print("%05s" % datas.led_down_lock[idx+j], end='')
        print()

def print_sensor_lux_state():
    print("%30s%31s%31s%31s"%('SENSOR UP LOCK', 'SENSOR DOWN LOCK', 'REAL LUX', 'CAL LUX'))
    for idx in range(0, len(datas.sensor_down_lock), 3):
        for j in range(0, 3):
            print("%10s" % datas.sensor_up_lock[idx + j], end='')
        print('|', end='')
        for j in range(0, 3):
            print("%10s" % datas.sensor_down_lock[idx + j], end='')
        print('|', end='')
        for j in range(0, 3):
            print("%10s" % datas.II_illum[idx + j], end='')
        print('|', end='')
        for j in range(0, 3):
            print("%10s" % round(datas.cal_lux[idx + j], 2), end='')
        print()

def print_sensor_state():
    print("%30s%31s"%('SENSOR UP LOCK', 'SENSOR DOWN LOCK'))
    for idx in range(0, len(datas.sensor_down_lock), 3):
        for j in range(0, 3):
            print("%10s" % datas.sensor_up_lock[idx + j], end='')
        print('|', end='')
        for j in range(0, 3):
            print("%10s" % datas.sensor_down_lock[idx + j], end='')
        print()

def print_lux_state():
    print("%30s%31s"%('SENSOR UP LOCK', 'SENSOR DOWN LOCK'))
    for idx in range(0, len(datas.II_illum), 3):
        for j in range(0, 3):
            print("%10s" % datas.II_illum[idx + j], end='')
        print('|', end='')
        for j in range(0, 3):
            print("%10s" % datas.cal_lux[idx + j], end='')
        print()

# 현재 컨트롤 lux 상태 출력
def print_control_lux():
    print("Control Lux")
    for idx in range(1, len(datas.led_state)):
        print("%s\t" % datas.led_control_lux[datas.led_state[idx]], end='')
        if idx % 6 == 0:
            print()

# 현재 cal lux 상태 출력
def print_cal_lux():
    print("Cal Lux")
    for idx in range(0, len(datas.cal_lux)):
        if (idx !=0) & (idx % 3 == 0):
            print()
        print("%s\t" % round(datas.cal_lux[idx], 2), end='')
    print()

def print_real_lux():
    print("REAL Lux")
    for idx in range(0, len(datas.II_illum)):
        if (idx !=0) & (idx % 3 == 0):
            print()
        print("%s\t" % round(datas.II_illum[idx], 2), end='')
    print()

    # print("LED state")
    # for idx in range(1, len(led_state)):
    #     print("%s\t" % led_state[idx], end='')
    #     if idx % 6 == 0:
    #         print()


# 현재 조명 잠금 상태 출력
def print_led_locking_state(led_lock, mode):
    print("LED Locking State [%s]" % mode)
    for idx in range(1, len(led_lock)):
        print("%s\t" % led_lock[idx], end='')
        if idx % 6 == 0:
            print()


# 현재 센서 잠금 상태 출력
def print_sensor_locking_state():
    print("Sensor Up Locking State")
    for idx in range(len(datas.sensor_up_lock)):
        print("%s\t" % datas.sensor_up_lock[idx], end='')
        if idx % 3 == 2:
            print()
    print("Sensor Down Locking State")
    for idx in range(len(datas.sensor_down_lock)):
        print("%s\t" % datas.sensor_down_lock[idx], end='')
        if idx % 3 == 2:
            print()


def print_natural_light_state():
    print("Virtual Natural Light")
    for i in range(len(datas.illum_add)):
        print(datas.illum_add[i], ' ', end='')
        if (i % 3 == 2):
            print()