import time
from datetime import datetime

import pandas as pd

import Shin_Package.open_processor_0_1.datas as datas

def illum_thread(illum_add):
    time.sleep(120)
    change_value = [0.151515, 0.30303, 0.151515]
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

    for i in range(11):
        # 밤에서 일출에서 오전으로
        if datas.satisfy_flag[0]:
            datas.satisfy_flag[0] = False
        else:
            datas.illum_satisfy_time.append('-')
        pd.DataFrame([datas.illum_change_time, datas.illum_satisfy_time], index=['change', 'satisfy']).to_csv(
            "D:\\BunkerBuster\\Desktop\\shin_excel\\24시작\\new_index\\%s\\[_만족시간]_%s.csv" % (
                datas.save_folder, i))
        datas.illum_change_time.append(datetime.now())

        if(i!=10):
            datas.satisfy_flag[0] = False
            print('CHANGE ILLUM %s' % (datas.illum_change_time[len(datas.illum_change_time) - 1]))
            # illum_add[0] += 5
            # illum_add[1] += 10
            # illum_add[2] += 10
            # illum_add[4] += 5
            # illum_add[5] += 10
            # illum_add[8] += 5

            illum_add[0] += 10
            illum_add[1] += 20
            illum_add[2] += 20
            illum_add[4] += 10
            illum_add[5] += 20
            illum_add[8] += 10
            time.sleep(60)