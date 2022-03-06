import time

import Shin_Package.led_select_module_blind_not_include.datas as datas
import Shin_Package.led_select_module_blind_not_include.illum_controller as controller
import Shin_Package.led_select_module_blind_not_include.sensing as sensing
from Shin_Package.led_select_module_blind_not_include import illum_controller
import Shin_Package.led_select_module_blind_not_include.blind as blind

def control_led(state, lux_state, can_control_led, df):
    controller.locking_init_led()
    controller.locking_init_sensor()

    ### 블라인드 초기화 설정
    blind.init_blind_first()
    # 초기값 설정 (대기조도, 대기전력 등)
    sensing.init_datas()
    datas.led_state_index=[[0]]
    
    # 데이터 전달받기
    datas.lux_state=lux_state
    datas.control_df=df
    datas.led_state = can_control_led

    for i in range(state):
        datas.led_state_index.appned([state[1],state[2],state[3],state[4]])

    # 0step 진행 상태 기록
    get_times = 0
    resensing = False
    datas.can_control = False


    datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
    for i in range(9):
        datas.cal_lux[i] = datas.II_illum[i]
    avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(datas.wait_illum, datas.wait_curr,
                                                                  get_times)

    while not datas.can_control:
        get_times += 1
        datas.blind_lock -= 1
        datas.isJust_lock -= 1
        datas.can_control = True
        cal_avg = (datas.cal_lux[0] + datas.cal_lux[1] * 2 + datas.cal_lux[2] + datas.cal_lux[3] * 2 + \
                   datas.cal_lux[4] * 4 + datas.cal_lux[5] * 2 + datas.cal_lux[6] + datas.cal_lux[7] * 2 +
                   datas.cal_lux[8]) / 16


        if ((datas.object_illum - datas.object_diff) <= cal_avg) & (
                cal_avg <= (datas.object_illum + datas.object_diff)):  # 평균조도가 매칭상태일때
            print("AVG Illum is Matched")
            controller.illum_match_needs(datas.cal_lux, cal_avg)
        elif (cal_avg < (datas.object_illum - datas.object_diff)):  # 평균조도가 낮을때
            # first = True
            print("AVG Illum is Low")
            controller.illum_before_needs(datas.cal_lux, cal_avg)
        elif ((datas.object_illum + datas.object_diff) < cal_avg):  # 평균조도가 높을때
            # first = True
            print("AVG Illum is High")
            controller.illum_after_needs(datas.cal_lux, cal_avg)

        datas.cant_cal=False
        ###### 계산 조도를 지점별로 확인
        datas.can_control = True
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

        ### 블라인드 deg 가 -70 이면서 cal_time이 500이면 그냥 한번 제어 ?
        print(
            'new check point datas.can_control(%s), datas.isJust_lock(%s), datas.cal_times(%s), datas.blind_deg(%s)' % (
                not datas.can_control, datas.isJust_lock <= 0, datas.cal_times >= 500, datas.blind_deg == -70))
        if (not datas.can_control) & (datas.isJust_lock <= 0) & (datas.cal_times >= 500) & (datas.blind_deg == -70):
            print('매칭은 안됬는데 블라인드 각도가 -70이면서 계산도 안되기에 한번 제어')
            datas.cal_times = 0
            datas.can_control = True
            datas.isJust = 3
            datas.cant_cal = True


        if datas.can_control:  ###### 조도가 만족했다면 계산조도로 전부 제어한 후 조도 재실측 후 실측값이 만족한지 테스트
            print("MATCH SUCCESS 또는 블라인드 제어함.")
            illum_controller.led_control_use_state_is_change(datas.led_control, datas.led_state)
            time.sleep(3)
            datas.acs_cct, datas.II_illum, datas.IC_curr = sensing.sensing_datas()
            for i in range(9):
                datas.II_illum[i] += datas.illum_add[i]
                resensing = True
            avg_cct, avg_illum, sum_curr, uniformity = sensing.need_value(datas.wait_illum, datas.wait_curr, get_times)

            for i in range(9):
                if (datas.II_illum[i] < (datas.object_illum - datas.object_diff)) | (
                        (datas.object_illum + datas.object_diff) < datas.II_illum[i]) | (
                        avg_illum < (datas.object_illum - (datas.object_diff / 2))) | (
                        avg_illum > (datas.object_illum + (datas.object_diff / 2))):
                    print(f"{i + 1} 지점 만족 x [{datas.II_illum[i]}]")
                    datas.can_control = False
                    print("#####  실측 오류 재 탐색 시작  #####")
                    break

        if resensing:
            for i in range(9):
                datas.cal_lux[i] = datas.II_illum[i]