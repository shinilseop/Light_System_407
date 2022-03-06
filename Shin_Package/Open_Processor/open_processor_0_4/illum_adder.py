import time
from datetime import datetime

import pandas as pd

import Shin_Package.Open_Processor.open_processor_0_4.datas as datas

STEP = 0

def save_delay(change_add, i):
    time.sleep(60)

    if datas.satisfy_flag[0]:
        datas.satisfy_flag[0] = False
    else:
        datas.illum_satisfy_time.append('-')
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간%s]_%s.csv" % (
            datas.path, datas.save_folder, change_add, i))

    datas.satisfy_flag[0] = False

def add_1(illum_add, change_time, illum_change_value, i):
    datas.satisfy_flag[0]=False
    illum_add[0] += illum_change_value
    illum_add[1] += illum_change_value * 2
    illum_add[2] += illum_change_value * 2
    illum_add[4] += illum_change_value
    illum_add[5] += illum_change_value * 2
    illum_add[8] += illum_change_value
    datas.illum_change_time.append(datetime.now())
    print('CHANGE ILLUM 1[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
    datas.can_control = False
    time.sleep(60)

    if datas.satisfy_flag[0]:
        datas.satisfy_flag[0] = False
    else:
        datas.illum_satisfy_time.append('-')
    print(datas.illum_change_time, datas.illum_satisfy_time)
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간1]_%s.csv" % (
            datas.path, datas.save_folder, i))

    datas.satisfy_flag[0] = False

def add_2(illum_add, change_time, illum_change_value, i):
    datas.satisfy_flag[0]=False
    illum_add[0] += illum_change_value
    illum_add[2] -= illum_change_value
    illum_add[3] += illum_change_value * 2
    illum_add[5] -= illum_change_value * 2
    illum_add[6] += illum_change_value
    illum_add[8] -= illum_change_value
    datas.illum_change_time.append(datetime.now())
    print('CHANGE ILLUM 2[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
    datas.can_control = False
    time.sleep(60)

    if datas.satisfy_flag[0]:
        datas.satisfy_flag[0] = False
    else:
        datas.illum_satisfy_time.append('-')
    print(datas.illum_change_time, datas.illum_satisfy_time)
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간2]_%s.csv" % (
            datas.path, datas.save_folder, i))

    datas.satisfy_flag[0] = False

def add_3(illum_add, change_time, illum_change_value, i):
    datas.satisfy_flag[0]=False
    illum_add[0] -= illum_change_value * 2
    illum_add[1] -= illum_change_value * 2
    illum_add[2] -= illum_change_value
    illum_add[3] -= illum_change_value * 2
    illum_add[4] -= illum_change_value
    illum_add[6] -= illum_change_value
    datas.illum_change_time.append(datetime.now())
    print('CHANGE ILLUM 3[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
    datas.can_control = False
    time.sleep(60)

    if datas.satisfy_flag[0]:
        datas.satisfy_flag[0] = False
    else:
        datas.illum_satisfy_time.append('-')
    print(datas.illum_change_time, datas.illum_satisfy_time)
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간3]_%s.csv" % (
            datas.path, datas.save_folder, i))

    datas.satisfy_flag[0] = False

def add_last(illum_add, change_time, illum_change_value, i):
    datas.can_control = False
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간 완료].csv" % (
            datas.path, datas.save_folder))

    print("CHANGE  TIME : %s" % datas.illum_change_time)
    print("SATISFY TIME : %s" % datas.illum_satisfy_time)

    time.sleep(60)
    datas.can_control = False
    datas.isFinish = False

def illum_thread(illum_add, change_time, illum_change_value):
    datas.illum_change_time=[]
    datas.illum_satisfy_time=[]
    time.sleep(60)
    # change_value = [0.151515, 0.30303, 0.151515]
    # while True:
    #     print('CHANGE ILLUM')
    #     # 오전에서 오후로 이동
    #     illum_add[0] += change_value[0]
    #     illum_add[2] -= change_value[0]
    #
    #     illum_add[3] += change_value[1]
    #     illum_add[5] -= change_value[1]
    #
    #     illum_add[6] += change_value[2]
    #     illum_add[8] -= change_value[2]
    #
    #     time.sleep(60)

    datas.satisfy_flag[0] = False

    STEP=1
    for i in range(change_time):
        # 밤에서 일출에서 오전으로

        illum_add[0] += illum_change_value
        illum_add[1] += illum_change_value * 2
        illum_add[2] += illum_change_value * 2
        illum_add[4] += illum_change_value
        illum_add[5] += illum_change_value * 2
        illum_add[8] += illum_change_value
        datas.illum_change_time.append(datetime.now())
        print('CHANGE ILLUM 1[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
        datas.can_control = False
        time.sleep(60)

        if datas.satisfy_flag[0]:
            datas.satisfy_flag[0] = False
        else:
            datas.illum_satisfy_time.append('-')
        pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
            "%s\\%s\\[_만족시간1]_%s.csv" % (
                datas.path, datas.save_folder, i))

        datas.satisfy_flag[0] = False

    print("CHANGE  TIME : %s" % datas.illum_change_time)
    print("SATISFY TIME : %s" % datas.illum_satisfy_time)

    STEP=2
    for i in range(change_time):
        # 오전에서 오후로

        illum_add[0] += illum_change_value
        illum_add[2] -= illum_change_value
        illum_add[3] += illum_change_value * 2
        illum_add[5] -= illum_change_value * 2
        illum_add[6] += illum_change_value
        illum_add[8] -= illum_change_value
        datas.illum_change_time.append(datetime.now())
        print('CHANGE ILLUM 2[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
        datas.can_control = False
        time.sleep(60)

        if datas.satisfy_flag[0]:
            datas.satisfy_flag[0] = False
        else:
            datas.illum_satisfy_time.append('-')
        pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
            "%s\\%s\\[_만족시간2]_%s.csv" % (
                datas.path, datas.save_folder, i))

        datas.satisfy_flag[0] = False

    print("CHANGE  TIME : %s" % datas.illum_change_time)
    print("SATISFY TIME : %s" % datas.illum_satisfy_time)

    STEP=3
    for i in range(change_time):
        # 오후에서 밤으로

        illum_add[0] -= illum_change_value * 2
        illum_add[1] -= illum_change_value * 2
        illum_add[2] -= illum_change_value
        illum_add[3] -= illum_change_value * 2
        illum_add[4] -= illum_change_value
        illum_add[6] -= illum_change_value
        datas.illum_change_time.append(datetime.now())
        print('CHANGE ILLUM 3[%s] %s' % (i, datas.illum_change_time[len(datas.illum_change_time) - 1]))
        datas.can_control = False
        time.sleep(60)

        if datas.satisfy_flag[0]:
            datas.satisfy_flag[0] = False
        else:
            datas.illum_satisfy_time.append('-')
        pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
            "%s\\%s\\[_만족시간3]_%s.csv" % (
                datas.path, datas.save_folder, i))

        datas.satisfy_flag[0] = False


    datas.can_control = False
    pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
        "%s\\%s\\[_만족시간 완료].csv" % (
            datas.path, datas.save_folder))

    print("CHANGE  TIME : %s" % datas.illum_change_time)
    print("SATISFY TIME : %s" % datas.illum_satisfy_time)


    time.sleep(60)
    datas.can_control = False
    time.sleep(60)
    datas.isFinish=False

def blind_control(illum_add, change_time, illum_change_value):
    print("BLIND CONTROLLER")
    for i in range(len(illum_add)):
        if(illum_add[i]>=10):
            illum_add[i]-=10