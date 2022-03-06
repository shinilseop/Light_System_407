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
"""
import threading
import time
from datetime import datetime

import pandas as pd

import Shin_Package.open_processor_0_1.init_setter as initial
import Shin_Package.open_processor_0_1.datas as datas
import Shin_Package.open_processor_0_1.led_controller as controller
import Shin_Package.open_processor_0_1.printer as printer
import Shin_Package.open_processor_0_1.sensing as sensing
import Shin_Package.open_processor_0_1.illum_adder as illum_adder


def process(start, case_num):
    controller.locking_init_led()
    controller.locking_init_sensor()

    sensing.init_datas()

    illum_add_thread = threading.Thread(target=illum_adder.illum_thread, args=(datas.illum_add,))
    illum_add_thread.start()

    isFinish = True
    first_matched = True
    first = True
    get_times = 0

    while isFinish:
        """
        센서 데이터의 일관성을 위해 값을 0으로 초기화 하고
        모든 데이터가 받을때까지 검사하다가 받는 순간 알고리즘 시작
        """

        acs_cct, II_illum, IC_curr = sensing.sensing_datas()
        datas.has_control_before[0] = True
        for i in range(9):
            II_illum[i] += datas.illum_add[i]
        avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(acs_cct, II_illum, IC_curr, datas.wait_illum,
                                                                      datas.wait_curr, get_times)
        """
        센서가 전부 잠겨있다면 멈춤 
        그 외
        1. 평균조도 < 490
            가장 낮은 지점을 찾고
            총 영향도가 높은 조명을 기반으로 제어
        2. 490 <= 평균조도 <= 510
            평균조도와 절대값 차이가 가장 큰 지점을 찾고
            개별 영향도가 높은 조명을 기반으로 제어
        3. 510 < 평균조도
            가장 높은 지점을 찾고
            총 영향도가 낮은 조명을 기반으로 제어
        """

        get_times += 1
        save_flag = False
        if first:
            print("FIRST MATCHED")
            first = False
            # 480<= 지점별 조도 <= 520 안에 모든 지점이 만족한다면 스텝별 저장이름에 success를 추가해서 저장
            save_flag = True
            for i in range(9):
                if (II_illum[i] < 480) | (520 < II_illum[i]):
                    save_flag = False
                    break
            # 기준을 만족하는 경우랑 일반의 경우 step 별로 저장
            if (490 <= avg_illum) & (avg_illum <= 510) & save_flag:
                printer.save_data(start, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                                  get_times,
                                  "_success_E%s_U%s" % (int(sum_curr), uniformity), True)
                datas.satisfy_flag[0] = True
            else:
                printer.save_data(start, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                                  get_times,
                                  "_E%s_U%s" % (int(sum_curr), uniformity), False)

            # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
            # if (avg_illum > 500):
            #     led_setting_based_on_influence_sum(False)
            # else:
            #     led_setting_based_on_influence_sum(True)
        else:
            if (avg_illum < 480):
                first = True
                print("AVG Illum is Low")
                controller.illum_before_needs(II_illum, avg_illum)
            elif (480 <= avg_illum) & (avg_illum <= 520):
                print("AVG Illum is Matched")
                # 처음 평균조도를 만족한 순간이라면
                # 잠금 상태를 한번 초기화 하고 시작
                # 조도가 극한으로 높은 상황에서 만족상태를 달성할때까지 보면
                # 조명을 24[첫단계]로 끄는 경우 때문에
                # 지점을 잠궈버리는 경우가 많음

                # 480<= 지점별 조도 <= 520 안에 모든 지점이 만족한다면 스텝별 저장이름에 success를 추가해서 저장
                save_flag = True
                for i in range(9):
                    if (II_illum[i] < 480) | (520 < II_illum[i]) | (avg_illum < 490) | (avg_illum > 510):
                        save_flag = False
                        break

                if first_matched:
                    first_matched = False
                    controller.locking_init_led()

                # if(not save_flag):
                #     illum_match_needs(II_illum, avg_illum)
                controller.illum_match_needs(II_illum, avg_illum)
            elif (520 < avg_illum):
                first = True
                print("AVG Illum is High")
                controller.illum_after_needs(II_illum, avg_illum)

            # 기준을 만족하는 경우랑 일반의 경우 step 별로 저장
            if (490 <= avg_illum) & (avg_illum <= 510) & save_flag:
                # time.sleep(1)
                # 값 불러옴
                acs_cct = sensing.acs1.get_sensor_data()[0][:9]
                II_illum = sensing.II1.get_illum_data()[:9]
                IC_curr = sensing.IC1.get_curr_data()[:10]
                printer.save_data(start, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_success_E%s_U%s" % (int(sum_curr), uniformity), True)
                if not datas.satisfy_flag[0]:
                    datas.satisfy_flag[0] = True
                    datas.illum_satisfy_time.append(datetime.now())
            else:
                printer.save_data(start, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_E%s_U%s" % (int(sum_curr), uniformity), False)

        printer.print_all()
        if datas.has_control_before[0]:
            time.sleep(1)



if __name__ == '__main__':
    timer_data = pd.DataFrame(columns=['start', 'end', 'diff'])
    sensing.start_data_center()

    # influence_maker
    initial.reverse_maker(datas.sensor_influence_sum_all, datas.sersor_influence_sum_all_reverse)
    initial.reverse_maker(datas.sensor_influence_value_sum_all, datas.sersor_influence_value_sum_all_reverse)
    initial.dir_inf_make()

    # # 조도 상태 매칭시켜서 단계로 state 넣는 방법
    for i in range(1, len(datas.led_state_lux)):
        for j in range(len(datas.led_control_lux)):
            if datas.led_state_lux[i] == datas.led_control_lux[j]:
                datas.led_state[i] = j
    print('조도상태매칭')
    print(datas.led_state)
    save_cnt = 0

    datas.save_folder = str(0)
    start = datetime.now()
    print('START :', start)
    # init led
    controller.led_control_use_state(datas.led_control, datas.led_state_0)
    time.sleep(3)
    # start
    process(start, 0)
    end = datetime.now()
    print('END :', end)
    print('걸린시간 :', (end - start))
    timer_data.loc[0] = {'start': start, 'end': end, 'diff': (end - start)}

    timer_data.to_csv("D:\\BunkerBuster\\Desktop\\shin_excel\\24시작\\new_index\\timer.csv")
    print(timer_data)
    print("timer save")
