"""
=========================================================
버전 정보 [DarkRoom]
0.1 :   sensor_influence_sum_all 제작 및 적용
0.2 :   조명의 초기 제어상태가 [all24, all498]과 다른 경우
        에너지 최적값을 찾지 못함.
        초기 상태를 최대한 변화시키지 않으려는 방향으로
        코딩이 되어있어서 그럼.
        1. 평균조도를 측정하고 판단하기 전에 켜져있는 조명을
        총 영향도에 기반한 제어로 변경을 시키기
        2. 낮추거나 높혀야 할 때 유사 영향도를 가진 조명을
        판단한 후에 총 영향도 기반에 벗어나는 제어가 있다면
        그 조명을 낮추고 총 영향도가 높은 조명을 높이는걸
        우선시 하는 방향 [단점 : 이후에 개별 조명 컨트롤이
        필요한 시점 = 평균조도가 만족할때, 제어방식이 겹침]

        1번 제어를 기준으로 해야할 듯 함.
0.3 :   0.2 버전의 1번 제어 기준으로 제작중
        전체를 단계별로 차차 제어를 안하고 한번에 했더니
        유사한 영향도를 고려하지 못해서
        유사한 영향도를 고려 할 수 있게 변경 및
        led_up, led_down 메소드에서 중복이 되는
        led 선정 과정과 유사한 영향도를 가진 조명을
        비교 및 선정하는 과정을 모듈화하여 up과 down 과정의
        메소드를 조금 더 간소화 함.

0.4 :   0.3 버전에서 전부 잠겨버리고 멈추는 상태를 도달할때까지
        만족하는 것을 찾지못함
        전부 잠금이라 컨트롤이 불가능할때 잠금을 초기화 해줌.
        초기화 하면서 총영향도에 기반한 제어로 변경

0.5 :   여러개 한번에 테스트 + 제어지표 새롭게 변경

0.6 :   제어지표 바꾸니 너무 느린거 같기도하고 이전에도 느렸기에
        속도 향상을 위한 가속도 메소드 get_control_step 을 추가하고
        led up, led down 하는 과정에서 그 스텝만큼 혹은 최소 최대보다
        넘어가게 되면 딱 그 선까지만 제어되게 변경
=========================================================
버전 정보 [Open_Window]
0.4 :   방향성 추가
0.5 :   방향성 대각선 제외
0.6 :   open window 버전을 만들면서 없앴던 센서 잠금을 다시 도입.
        이유 : 진행하는 과정에 있어서 2번센서의 제어 가능조명이 전부다 24라서 제어가 불가능한데
        잠금은 진행이 되지 않아서 그 다음 목적 센서를 제어하지 못함.
        만일 문제가 될 시 추후 버전에서 롤백 예정
        또한, 잠금을 했을때는 제어가 안들어가기에 센서값을 초기화 하지않고
        받을 수 있는 값만 다 받아오고 다시 바로 제어에 들어감
        제어 다 끝내고 1초 기다리는거도 안기다림.
=========================================================
버전 정보 [Open_Processor]
0.1 :   파일 분리하여 모듈화
0.2 :   lock을 n차례 잠금하여 step을 진행할 때마다 1씩 다운시켜 n차례 만큼만 잠굼.
0.3 :   방향성을 선택하고 그 바운더리에 제어가능한 조명이 없으면 -1을 반환해서
        제어조명을 조명 전체의 영향도 50% 이상인 조명내에서 선택하도록 변경
0.4 :   실제 데이터를 기반으로 제어하던 거에서 조명의 제어를 시뮬레이션화
        (이유 : 서비스와 조도 계산부를 분리하기 위함)
        (분리하지 않는다면 1분이 아니라 매순간순간 변화하는 자연광에)
        (대응하기 어려울 것임)
        따라서 영향도 기반의 조도 계산 시뮬레이션을 제작 (실제 조도를 
        센싱하는 것 대신 시뮬레이션으로 변하는 조도를 알고리즘 프로세스 부분에 제공)
        계산이 끝나기 전에는 이전에 계산된 조도를 기반으로 서비스 해 줌.
        스텝별로 세이브 하던것도 제어를 하고 난 후 저장되게 변경하애 햘 듯
        
        변경 사항
        1. 프로세스에 조도를 실제 측정 조도가 아닌 시뮬레이션 조도를 제공
            1) 시뮬레이션 조도란 :  조명이 가지고 있는 영향도에 의해 제어된 조도를 기반으로
                                 각 지점에 조도를 합산해준다.
            2) 계산방법 :   실제 조도를 센싱하는 부분에서 1분에 한번씩만 센싱하는것으로 교체하고
                           경계 찾기가 어려워보임.
        3. 세이브 스텝을 계산된 조명 제어지표를 제공하고 난 3초 후 저장
master :가상조도 더하는거 제거 + 1분마다 센싱하면서 지점별 조도가 만족하면 제어 X
        만족하지 못한다면은 그때 제어 -> 실시간 자연광 받는 준비 + 블라인드 제어 준비
=========================================================
버전 정보 [Open_Processor_NL]
0.1 :   자연광조도 조절을 위한 블라인드 제어 포함
        방안 1
        INIT : 최소단계인 24Lux로 모두 제어
        1. 조도 +++
            1) 블라인드 더 열 수 있는지 확인(블라인드 현재상태 체크 -> 아마 무조건 가능(밤이 될때쯤은 다열수도 잇겠더라) 그런데 열고 닫고를 반복하는 무한 루프에 빠질수가 있음)
                -> 무한루프 방지를 위해서 바운더리 내의 조명 상태를 확인하는 작업 중 전부 최소단계라면 블라인드 제어를 잠금. (블라인드 lock) -> 각 지점별 lock을 어떻게 관리할지 생각해야될듯
            2) 블라인드를 열 수 없다면(아마 x 직사광이 들어오면 조도가 넘쳐버릴것임) 조명을 제어
        2. 조도 충분
            1) 조도 +
                [1] 조도를
            2) 조도 -
        3. 조도 ---
            1)

        방안 2
=========================================================
"""
import threading
import time
from datetime import datetime

import numpy as np
import pandas as pd

import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.init_setter as initial
import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.datas as datas
import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.led_controller as controller
import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.printer as printer
import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.sensing as sensing
import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.illum_adder as illum_adder
from Shin_Package.Open_Processor_NL.Cal_Open_Processor_master import led_controller


def process(start, case_num, change_time, illum_change_value):
    controller.locking_init_led()
    controller.locking_init_sensor()

    time.sleep(3)
    # 초기값 설정 (대기조도, 대기전력 등)
    sensing.init_datas()

    first_matched = True
    first = True
    get_times = 0
    change_idx = -1
    cal_times = 0

    # 0step 진행 상태 기록
    sensing_time = datetime(2000, 1, 1, 12, 0, 0)
    datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
    for i in range(9):
        time.sleep(2)
        datas.II_illum[i] += datas.illum_add[i]
        datas.cal_lux[i] = datas.II_illum[i]
    avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(datas.wait_illum, datas.wait_curr, get_times)
    printer.save_data(start, avg_cct, avg_illum, sum_curr, uniformity,
                      get_times, "_E%s_U%s" % (int(sum_curr), uniformity), False)

    # illum_add_thread = threading.Thread(target=illum_adder.illum_thread,
    #                                     args=(datas.illum_add, change_time, illum_change_value))
    # illum_add_thread.start()
    datas.can_control = False

    datas.can_control = True
    while datas.isFinish:
        """
        센서 데이터의 일관성을 위해 값을 0으로 초기화 하고
        모든 데이터가 받을때까지 검사하다가 받는 순간 알고리즘 시작
        """
        # 현재 시간이 센싱했던 시간보다 1분이 지났으면 실제 데이터 센싱
        # print("time compare :",datetime.now(),",",sensing_time)
        if ((datetime.now() - sensing_time).seconds >= 60):
            datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
            for i in range(9):
                datas.II_illum[i] += datas.illum_add[i]
                datas.cal_lux[i] = datas.II_illum[i]
            avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(datas.wait_illum, datas.wait_curr, get_times)
            sensing_time = datetime.now()
            get_times += 1
            printer.save_data(start, avg_cct, avg_illum, sum_curr, uniformity,
                              get_times, "_change_illum_E%s_U%s" % (int(sum_curr), uniformity), False)

            datas.can_control = True
            for i in range(9):
                if (datas.II_illum[i] < (datas.object_illum - datas.object_diff)) | (
                        (datas.object_illum + datas.object_diff) < datas.II_illum[i]) | (
                        (datas.object_illum - (datas.object_diff / 2)) > avg_illum) | (
                        avg_illum > (datas.object_illum + (datas.object_diff / 2))):
                    datas.can_control = False
                    print(f"{i + 1} 지점 만족 x [{datas.II_illum[i]}]")
                    print("#####  제어시작  #####")
                    cal_times = 0
                    break
            if datas.can_control:
                print('데이터 센싱 (조도 만족) 후 제어 X')

        if datas.can_control:
            datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
            for i in range(9):
                datas.II_illum[i] += datas.illum_add[i]
                datas.cal_lux[i] = datas.II_illum[i]
            sensing.need_value(datas.wait_illum, datas.wait_curr, get_times)
            time.sleep(1)
            continue

        # 계산용 조도 평균 재산출
        cal_avg = (datas.cal_lux[0] + datas.cal_lux[1] * 2 + datas.cal_lux[2] + datas.cal_lux[3] * 2 + \
                   datas.cal_lux[4] * 4 + datas.cal_lux[5] * 2 + datas.cal_lux[6] + datas.cal_lux[7] * 2 +
                   datas.cal_lux[8]) / 16

        get_times += 1
        save_flag = False
        first = False
        if (cal_avg < (datas.object_illum - datas.object_cal_diff)):  # 평균조도가 낮을때
            # first = True
            print("AVG Illum is Low")
            controller.illum_before_needs(datas.cal_lux, cal_avg)
        elif ((datas.object_illum - datas.object_cal_diff) <= cal_avg) & (
                cal_avg <= (datas.object_illum + datas.object_cal_diff)):  # 평균조도가 매칭상태일때
            print("AVG Illum is Matched")
            # 처음 평균조도를 만족한 순간이라면
            # 잠금 상태를 한번 초기화 하고 시작
            # 조도가 극한으로 높은 상황에서 만족상태를 달성할때까지 보면
            # 조명을 24[첫단계]로 끄는 경우 때문에
            # 지점을 잠궈버리는 경우가 많음
            # if first_matched:
            #     first_matched = False
            #     controller.locking_init_led()

            controller.illum_match_needs(datas.cal_lux, cal_avg)
        elif ((datas.object_illum + datas.object_cal_diff) < cal_avg):  # 평균조도가 높을때
            # first = True
            print("AVG Illum is High")
            controller.illum_after_needs(datas.cal_lux, cal_avg)

        ###### 계산 조도를 지점별로 확인
        datas.can_control = True
        resensing = False
        cal_avg = (datas.cal_lux[0] + datas.cal_lux[1] * 2 + datas.cal_lux[2] + datas.cal_lux[3] * 2 + \
                   datas.cal_lux[4] * 4 + datas.cal_lux[5] * 2 + datas.cal_lux[6] + datas.cal_lux[7] * 2 +
                   datas.cal_lux[8]) / 16

        ###### 계산조도의 적합 정도
        for i in range(9):
            if (datas.cal_lux[i] < (datas.object_illum - datas.object_cal_diff)) | (
                    (datas.object_illum + datas.object_cal_diff) < datas.cal_lux[i]) | (
                    (datas.object_illum - (datas.object_cal_diff / 2)) > cal_avg) | (
                    cal_avg > (datas.object_illum + (datas.object_cal_diff / 2))):
                datas.can_control = False
                break

        if datas.can_control:  ###### 조도가 만족했다면 계산조도로 전부 제어한 후 조도 재실측 후 실측값이 만족한지 테스트
            print("MATCH SUCCESS")
            led_controller.led_control_use_state_is_change(datas.led_control, datas.led_state)
            time.sleep(3)
            datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
            for i in range(9):
                datas.II_illum[i] += datas.illum_add[i]
                resensing = True
                # datas.cal_lux[i] = datas.II_illum[i]
            avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(datas.wait_illum, datas.wait_curr, get_times)

            save_flag = True
            for i in range(9):
                if (datas.II_illum[i] < (datas.object_illum - datas.object_diff)) | (
                        (datas.object_illum + datas.object_diff) < datas.II_illum[i]) | (
                        avg_illum < (datas.object_illum - (datas.object_diff / 2))) | (
                        avg_illum > (datas.object_illum + (datas.object_diff / 2))):
                    print(f"{i + 1} 지점 만족 x [{datas.II_illum[i]}]")
                    save_flag = False
                    datas.can_control = False
                    print("#####  실측 오류 재 탐색 시작  #####")
                    break

            if save_flag:  ###### 계산조도로 제어한 조도가 만족했다면 sucess 저장
                printer.save_data(start, avg_cct, avg_illum, sum_curr, uniformity,
                                  get_times, "_match_success_E%s_U%s" % (int(sum_curr), uniformity), True)
                if not datas.satisfy_flag[0]:
                    datas.satisfy_flag[0] = True
                    print("Success Time ", datetime.now())
                    datas.illum_satisfy_time.append(datetime.now())
            else:
                printer.save_data(start, avg_cct, avg_illum, sum_curr, uniformity,
                                  get_times, "_match_E%s_U%s" % (int(sum_curr), uniformity), False)
        else:
            # else:  ###### 만족못했을때
            # printer.save_data(start, avg_cct, avg_illum, sum_curr, uniformity,
            #                   get_times, "_E%s_U%s" % (int(sum_curr), uniformity), False)
            get_times += 1
            cal_times += 1
        printer.print_all()

        if resensing:
            for i in range(9):
                datas.cal_lux[i] = datas.II_illum[i]


def data_init():
    datas.isFinish = True
    datas.first_matched = False
    datas.can_control = False
    datas.is_exit = [False]
    datas.satisfy_flag = [True]
    datas.has_control_before = [True]

    datas.df_record = []
    datas.led_state_case_limit = []
    datas.illum_add = []
    datas.illum_change_time = []
    datas.illum_satisfy_time = []
    datas.acs_cct = np.zeros(9)
    datas.II_illum = np.zeros(9)
    datas.IC_curr = np.zeros(10)

    datas.cal_lux = [0, 0, 0,
                     0, 0, 0,
                     0, 0, 0]

    datas.led_state = [0,
                       1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1, 1]
    datas.illum_add = [0, 0, 0,
                       0, 0, 0,
                       0, 0, 0]


if __name__ == '__main__':
    timer_data = pd.DataFrame(columns=['start', 'end', 'diff'])
    sensing.start_data_center()

    # influence_maker
    initial.reverse_maker(datas.sensor_influence_sum_all, datas.sersor_influence_sum_all_reverse)
    initial.reverse_maker(datas.sensor_influence_value_sum_all, datas.sersor_influence_value_sum_all_reverse)
    initial.dir_inf_make()

    # 실험용
    # change_time = [10,5, 3, 2]
    # illum_change_value = [9.5,19, 33, 47.5]
    # save_folder_name = ['_조도변화 9.5','_조도변화 19','_조도변화 33','_조도변화 47.5']

    # test
    # led_lock_range_list = [5, 4, 3, 2]
    # accel_list  = [2, 4, 6]
    # change_time = [10, 5, 3, 2]
    # illum_change_value = [9.5, 19, 33, 47.5]
    # save_folder_name = ['30m', '15m', '9m', '6m']
    # start = 1
    # test
    led_lock_range_list = [5]
    accel_list = [2]
    change_time = [10, 5, 3, 2, 1]
    illum_change_value = [9.5, 19, 33, 47.5, 90]
    save_folder_name = ['30m', '15m', '9m', '6m', '3m']
    start = 0

    target_illum_list = [800]
    object_cal_diff_list = [15]
    led_lock_range_list = [3]
    accel_list = [5]
    change_time = [5]
    illum_change_value = [19]
    save_folder_name = ['800_24_start']
    start = 0

    for acc in range(len(accel_list)):
        datas.accel = accel_list[acc]
        for lock_value in range(len(led_lock_range_list)):
            datas.lock_step = led_lock_range_list[lock_value]
            datas.object_illum = target_illum_list[lock_value]
            datas.object_cal_diff = object_cal_diff_list[lock_value]
            data_init()
            for k in range(start, len(change_time)):
                print("%s loop start" % k)
                datas.isFinish = True
                datas.illum_change_time = []
                datas.illum_satisfy_time = []
                # # 조도 상태 매칭시켜서 단계로 state 넣는 방법
                for i in range(1, len(datas.led_state_lux)):
                    for j in range(len(datas.led_control_lux)):
                        if datas.led_state_lux[i] == datas.led_control_lux[j]:
                            datas.led_state[i] = j
                print('조도상태매칭')
                print(datas.led_state)
                save_cnt = 0

                datas.save_folder = f'계산\\acc_{accel_list[acc]}\\lock_{led_lock_range_list[lock_value]}\\{save_folder_name[k]}'
                start = datetime.now()
                print('START :', start)
                # init led
                controller.led_control_use_state(datas.led_control, datas.led_state_0)
                time.sleep(3)
                # start
                process(start, i, change_time[k], illum_change_value[k])
                print("%s loop finish" % k)
            start = 0
    # end = datetime.now()
    # print('END :', end)
    # print('걸린시간 :', (end - start))
    # timer_data.loc[0] = {'start': start, 'end': end, 'diff': (end - start)}
    #
    # timer_data.to_csv("\\timer.csv"%datas.path)
    # print(timer_data)
    # print("timer save")
    print("PROCESS FINISH")
    controller.led_control_use_state(datas.led_control, datas.led_state_0)
