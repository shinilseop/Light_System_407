import math
import time

import numpy as np

import Shin_Package.Open_Processor_NL.Open_Processor_NL_03.datas as datas
import Shin_Package.Open_Processor_NL.Open_Processor_NL_03.led_controll as led
import Shin_Package.Open_Processor_NL.Open_Processor_NL_03.led_selecter as selecter
import Shin_Package.Open_Processor_NL.Open_Processor_NL_03.blind as blind


# 잠금 초기화 하는 함수[조명 업,다운, 센서]


def locking_init_led():
    print("Locking Initializing LED")
    for i in range(len(datas.led_up_lock)):
        datas.led_up_lock[i] = 0
        datas.led_down_lock[i] = 0


# 잠금 초기화 하는 함수[조명 업,다운, 센서]
def locking_init_sensor():
    print("Locking Initializing SENSOR")
    for i in range(len(datas.sensor_up_lock)):
        datas.sensor_up_lock[i] = 0
        datas.sensor_down_lock[i] = 0


# LED 제어
# def control_led(led_num, control_step):
#     # locking_init_led()
#     led_lock_minus()
#     led.set_LED(led_num, datas.led_control[control_step][0], datas.led_control[control_step][1],
#                 datas.led_control[control_step][2],
#                 datas.led_control[control_step][3])
# 시뮬레이션 용도
def control_led(led_num, control_step, mode):
    # locking_init_led()
    led_lock_minus()
    print('change  ', datas.led_state[led_num], control_step)
    if mode == "up":
        change_lux = datas.led_control_lux[datas.led_state[led_num] + control_step] - datas.led_control_lux[
            datas.led_state[led_num]]
    if mode == "down":
        change_lux = datas.led_control_lux[datas.led_state[led_num] - control_step] - datas.led_control_lux[
            datas.led_state[led_num]]
    for i in range(len(datas.led_influ[led_num])):
        print("%s : %s + %s" % (i + 1, datas.cal_lux[i], change_lux * datas.led_influ[led_num][i]))
        datas.cal_lux[i] += change_lux * datas.led_influ[led_num][i]
    datas.led_is_change[led_num] = True
    # for i in range(len(datas.led_ind_inf[led_num])):
    #     datas.
    # led.set_LED(led_num, datas.led_control[control_step][0], datas.led_control[control_step][1],
    #             datas.led_control[control_step][2], datas.led_control[control_step][3])


# 평균조도가 작은경우
def illum_before_needs(II_illum, avg_illum):
    # blind_is_lock = False
    # for i in range(len(datas.blind_lock)):
    #     if datas.blind_lock:
    #         blind_is_lock = True
    #         break

    ### 블라인드 제어 불가능 상태일 때
    if ((not datas.more_illum_use_blind) | (datas.blind_lock > 0)):
        target = 99999
        min_sensor = -1

        # 최소 지점 선정
        for i in range(9):
            if II_illum[i] < target:
                if datas.sensor_up_lock[i] == 0:
                    min_sensor = i
                    target = II_illum[min_sensor]

        print('SELECT %s Position' % (min_sensor + 1))
        control_step = math.ceil(abs(datas.object_illum - II_illum[min_sensor]) / datas.accel)
        print("control_step cal :", datas.object_illum, II_illum[min_sensor], datas.accel)

        if min_sensor == -1:
            locking_init_led()
            # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
            if (avg_illum > 500):
                led_setting_based_on_influence_sum(False)
            else:
                led_setting_based_on_influence_sum(True)
            # exit()

        led_up(min_sensor, datas.sensor_influence_sum_part[min_sensor],
               datas.sensor_influence_sum_value_part[min_sensor],
               control_step)

        return 'led'
    ### 블라인드 제어 가능일 때
    else:
        blind.blind_open()

        return 'blind'


# 평균조도가 만족될때
def illum_match_needs(II_illum, avg_illum):
    # 목표조도로부터 절댓값 차이가 가장 큰지점 채택
    diff_max_sensor = -1
    diff_value = 0

    for i in range(9):
        # print("SENSOR STATE : UP[%s], DOWN[%s]" % (datas.sensor_up_lock[i], datas.sensor_down_lock[i]))
        if ((datas.sensor_up_lock[i] == 0) & (II_illum[i] - datas.object_illum < 0)) | (
                (datas.sensor_down_lock[i] == 0) & (II_illum[i] - datas.object_illum > 0)):
            if abs(datas.object_illum - II_illum[i]) > abs(diff_value):
                diff_max_sensor = i
                diff_value = II_illum[i] - datas.object_illum

    print('SELECT %s Position diff=%s' % (diff_max_sensor + 1, diff_value))

    if diff_max_sensor == -1:
        locking_init_led()
        # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
        if (avg_illum > 500):
            led_setting_based_on_influence_sum(False)
        else:
            led_setting_based_on_influence_sum(True)
        # exit()

    control_step = math.ceil(abs(datas.object_illum - II_illum[diff_max_sensor]) / datas.accel)

    # 평균조도와 지점 조도의 차이가 양수인 경우 조도가 초과하므로 하향점등 후 해당 조명 상향점등 잠금
    if diff_value >= 0:
        ### 지점의 바운더리 내에 선택 가능 조명이 잠금 상태도 아니면서 최소단계가 아니어서 제어 가능한 경우가 있다면 조명 제어를 우선적으로 하기 위한 flag 판단
        # position_led_can_control = False
        # for i in range(len(datas.sensor_influence_all[diff_max_sensor])):
        #     if (datas.led_state[datas.sensor_influence_all[diff_max_sensor][i]] > 1) & (datas.led_down_lock[datas.sensor_influence_all[diff_max_sensor][i]] == 0):
        #         position_led_can_control = True
        #         break
        # if position_led_can_control:

        ### 블라인드 제어 불가능 상태일 때
        if (datas.cal_times <= datas.blind_up_limit) | (datas.blind_deg == -70):
            # 조명 선정 및 제어
            _direction = dir_finder(False, diff_max_sensor, II_illum)
            if _direction == -1:
                control_led = led_down(diff_max_sensor, datas.sensor_influence_all[diff_max_sensor],
                                       datas.sensor_influence_value_all[diff_max_sensor], control_step)
            else:
                inf_led = datas.dir_inf[diff_max_sensor]['ind'][_direction]
                inf_value = datas.dir_inf[diff_max_sensor]['ind'][_direction + '_inf']
                control_led = led_down(diff_max_sensor, inf_led, inf_value, control_step)

            print("LOCKING STATE : %sLED[%s]" % (control_led, datas.led_up_lock[control_led]))
            if datas.led_up_lock[control_led] == 0:
                print("Up Locking : %s LED [%s -> %s]" % (
                    control_led, datas.led_up_lock[control_led], datas.led_up_lock[control_led] + datas.lock_step))
                datas.led_up_lock[control_led] += datas.lock_step

            # 잠금 시작
            # if control_led != -1:
            #     print("Up Locking : %s" % control_led)
            #     if datas.led_up_lock[control_led]==0:
            #         datas.led_up_lock[control_led] += datas.lock_step
            #     print('LED Up Lock try')
            return 'led'
        else:
            print("블라인드 제어로 인한 계산조도 초기화.")
            for i in range(1, len(datas.led_is_change)):
                datas.led_is_change[i] = False
                datas.led_state[i] = datas.ori_led_state[i]
                if i < 9:
                    datas.cal_lux[i] = datas.II_illum[i]
            blind.blind_close()
            datas.blind_act_close = True

            return 'blind'

    # 평균조도와 지점 조도의 차이가 음수인 경우 조도가 부족하므로 상향점등 후 해당 조명 하향점등 잠금
    else:
        # blind_is_lock = False
        # for i in range(len(datas.blind_lock)):
        #     if datas.blind_lock:
        #         blind_is_lock = True
        #         break

        ### 블라인드 제어 불가능 상태일 때
        if ((not datas.more_illum_use_blind) | (datas.blind_lock > 0) | (datas.blind_deg == 0)):
            # 조명 선정 및 제어
            _direction = dir_finder(True, diff_max_sensor, II_illum)
            if _direction == -1:
                control_led = led_up(diff_max_sensor, datas.sensor_influence_all[diff_max_sensor],
                                     datas.sensor_influence_value_all[diff_max_sensor], control_step)
            else:
                inf_led = datas.dir_inf[diff_max_sensor]['ind'][_direction]
                inf_value = datas.dir_inf[diff_max_sensor]['ind'][_direction + '_inf']
                control_led = led_up(diff_max_sensor, inf_led, inf_value, control_step)

            print("LOCKING STATE : %sLED[%s]" % (control_led, datas.led_down_lock[control_led]))
            if datas.led_down_lock[control_led] == 0:
                print("Down Locking : %s LED [%s -> %s]" % (
                    control_led, datas.led_down_lock[control_led], datas.led_down_lock[control_led] + datas.lock_step))
                datas.led_down_lock[control_led] += datas.lock_step

            # 잠금 시작
            # if control_led != -1:
            #     print("Down Locking : %s" % control_led)
            #     if datas.led_down_lock[control_led]==0:
            #         datas.led_down_lock[control_led] += datas.lock_step
            #     print('LED Down Lock try')
            return 'led'
        else:
            blind.blind_open()

            return 'blind'


# 평균조도가 초과될 때
def illum_after_needs(II_illum, avg_illum):
    if (datas.cal_times <= datas.blind_up_limit) | (datas.blind_deg == -70):
        target = 0
        max_sensor = -1

        # 최고 지점 선정
        for i in range(9):
            if II_illum[i] > target:
                if datas.sensor_down_lock[i] == 0:
                    max_sensor = i
                    target = II_illum[max_sensor]

        print('SELECT %s Position' % (max_sensor + 1))
        control_step = math.ceil(abs(datas.object_illum - II_illum[max_sensor]) / datas.accel)

        if max_sensor == -1:
            locking_init_led()
            # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
            if (avg_illum > 500):
                led_setting_based_on_influence_sum(False)
            else:
                led_setting_based_on_influence_sum(True)
            # exit()
        else:
            led_down(max_sensor, datas.sensor_influence_sum_part_reverse[max_sensor],
                     datas.sensor_influence_sum_value_part_reverse[max_sensor], control_step)

        return 'led'
    else:
        print("블라인드 제어로 인한 계산조도 초기화.")
        for i in range(1, len(datas.led_is_change)):
            datas.led_is_change[i] = False
            datas.led_state[i] = datas.ori_led_state[i]
            if i < 9:
                datas.cal_lux[i] = datas.II_illum[i]
        print("FINISH")
        blind.blind_close()
        datas.blind_act_close = True

        return 'blind'


def dir_finder(is_Low, select, II_illum):
    # return -1

    move_dir = ''
    if is_Low:  # 낮아서 높힐때
        target_illum = 50000
    else:  # 높아서 낮출때
        target_illum = 0

    square_ii = np.array(II_illum).reshape(3, 3)
    x, y = select % 3, select // 3

    # 바로 인접한 영역(대각선 제외)만 체크해서 방향 결정
    for i in datas.movement[select]['x']:
        lr = int(x + i)
        ud = int(y)
        if (i == 0):
            continue
        move_dir_temp = datas.direction['lr'][i]
        print("DIR FINDER :select", select, ", move_dir_temp", move_dir_temp)
        if is_Low:
            if target_illum > square_ii[ud][lr]:
                for k in datas.dir_inf[select]['ind'][move_dir_temp]:
                    if datas.led_state[int(k)] != 1:
                        target_illum = square_ii[ud][lr]
                        move_dir = move_dir_temp
                        break
        else:
            if target_illum < square_ii[ud][lr]:
                for k in datas.dir_inf[select]['ind'][move_dir_temp]:
                    if datas.led_state[int(k)] != len(datas.led_control_lux):
                        target_illum = square_ii[ud][lr]
                        move_dir = move_dir_temp
                        break

    for i in datas.movement[select]['y']:
        lr = int(x)
        ud = int(y + i)
        # print(lr, ud)
        if (i == 0):
            continue
        move_dir_temp = datas.direction['ud'][i]
        if is_Low:
            if target_illum > square_ii[ud][lr]:
                for k in datas.dir_inf[select]['ind'][move_dir_temp]:
                    if datas.led_state[int(k)] != 1:
                        target_illum = square_ii[ud][lr]
                        move_dir = move_dir_temp
                        break
        else:
            if target_illum < square_ii[ud][lr]:
                for k in datas.dir_inf[select]['ind'][move_dir_temp]:
                    if datas.led_state[int(k)] != len(datas.led_control_lux):
                        target_illum = square_ii[ud][lr]
                        move_dir = move_dir_temp
                        break

    if (move_dir == ''):
        return -1
    inf_led = datas.dir_inf[select]['ind'][move_dir]
    inf_value = datas.dir_inf[select]['ind'][move_dir + '_inf']

    ###### 바운더리에 제어할 수 있는 조명이 없을때. --> 블라인드 제어
    for i in range(len(inf_led)):
        # print("LED NUM:",inf_led[i],", led_state:",datas.led_state[inf_led[i]],", is_low:",is_Low,", uplock:",datas.led_up_lock[inf_led[i]],", downlock:",datas.led_down_lock[inf_led[i]])
        # print("%s, %s, %s"%(((datas.led_state[inf_led[i]]) != 1),(is_Low & (datas.led_up_lock[inf_led[i]] == 0)),((not is_Low) & (datas.led_down_lock[inf_led[i]] == 0))))
        if ((datas.led_state[inf_led[i]]) != 1) & \
                ((is_Low & (datas.led_up_lock[inf_led[i]] == 0)) |
                 ((not is_Low) & (datas.led_down_lock[inf_led[i]] == 0))):
            # print("Find Direction " + str(move_dir))
            break
        if (i == len(inf_led) - 1):
            # print("Find Direction But There is no controllable LED")
            return -1

    print('DIRECTION ', move_dir, target_illum)
    return move_dir


# 낮출 조명을 선정하는 단계 영향도는 이전 제어하는 함수에서 설정해준다.
def led_down(max_sensor, influence_rank, influence_value, control_step=1):
    # 잠금 및 제어가능 점검
    control_led_idx, control_led_rank = selecter.select_control_led(max_sensor, influence_rank, False)
    if (control_led_idx == -1):
        print("Can't Control LED near by %s Sensor." % (max_sensor + 1))

        return -1
    # 유사한 영향도를 가진 조명의 제어 상태 비교
    control_led_idx, control_led_rank = selecter.find_similar_influence(max_sensor, control_led_rank, influence_rank,
                                                                        influence_value, False)

    ################################0.6################################
    if (datas.led_state[control_led_idx] - control_step < 1):
        print("CHANGE CONTROL STEP [%s] -> [%s] (CAUSE : %s LED STATE = %s" % (
            control_step, datas.led_state[control_led_idx] - 1, control_led_idx, datas.led_state[control_led_idx]))
        control_step = datas.led_state[control_led_idx] - 1
    ###################################################################

    # 선정 LED n단계 다운
    print("SENSOR[%s] LED[%s] DOWN %s->%s [%s STEP]" % (
        (max_sensor + 1), control_led_idx, datas.led_control_lux[datas.led_state[control_led_idx]],
        datas.led_control_lux[datas.led_state[control_led_idx] - control_step], control_step))
    control_led(control_led_idx, control_step, 'down')
    datas.led_state[control_led_idx] -= control_step

    # 상승이 잠겨져 있다면 낮추면서 상승시킬 껀덕지가 나왔기에 잠금 해제
    if datas.sensor_up_lock[max_sensor] == 1:
        datas.sensor_up_lock[max_sensor] = 0
        print("%s sensor down unlock" % max_sensor)

    return control_led_idx


def led_up(min_sensor, influence_rank, influence_value, control_step=1):
    # 제어할 LED 선정
    # 잠금 및 제어가능 점검
    control_led_idx, control_led_rank = selecter.select_control_led(min_sensor, influence_rank, True)
    if (control_led_idx == -1):
        print("Can't Control LED near by %s Sensor." % (min_sensor + 1))
        return -1
    # 유사한 영향도를 가진 조명의 제어 상태 비교
    control_led_idx, control_led_rank = selecter.find_similar_influence(min_sensor, control_led_rank, influence_rank,
                                                                        influence_value, True)
    #
    #     ################################0.6################################
    #     if (datas.led_state[control_led_idx] + control_step >= len(datas.led_control)):
    #         print("CHANGE CONTROL STEP [%s] -> [%s] (CAUSE : %s LED STATE = %s" % (
    #             control_step, len(datas.led_control) - datas.led_state[control_led_idx] - 1, control_led_idx,
    #             datas.led_state[control_led_idx]))
    #         control_step = len(datas.led_control) - datas.led_state[control_led_idx] - 1
    #     ###################################################################
    #
    #     # 선정 LED 한단계 상승
    if (datas.led_state[control_led_idx] + control_step) >= len(datas.led_control):
        print("Control step 조정 : %s -> %s" % (
        control_step, len(datas.led_control) - datas.led_state[control_led_idx] - 1))
        control_step = len(datas.led_control) - datas.led_state[control_led_idx] - 1
    print("CHECK ", datas.led_state[control_led_idx], control_step)
    print("SENSOR[%s] LED[%s] UP %s->%s [%s STEP]" % (
        (min_sensor + 1), control_led_idx, datas.led_control_lux[datas.led_state[control_led_idx]],
        datas.led_control_lux[datas.led_state[control_led_idx] + control_step], control_step))
    control_led(control_led_idx, control_step, 'up')
    datas.led_state[control_led_idx] += control_step

    # 하락이 잠겨져 있다면 상승하면서 낮출 껀덕지가 나왔기에 잠금 해제
    if datas.sensor_down_lock[min_sensor] == 1:
        datas.sensor_down_lock[min_sensor] = 0
        print("%s sensor down unlock" % min_sensor)

    return control_led_idx


# led 잠금
def led_locking(led_lock_list, led_lock):
    print("Locking : ", end='')
    for led_num in led_lock_list:
        datas.led_lock[led_num] = 1
        print(led_num, "", end='')
    print()


# 스텝이 진행될때
# (조명이 제어됬을때 마다 실행하는데 잠금이 0 까지 떨어져서 해제됬을때 센서 잠금을 확인하고
# 잠긴 부분이 있으면 해당 센서의 제어 범위를 확인하고 포함되는 조명이면 잠금 해제)
def led_lock_minus():
    for i in range(len(datas.led_down_lock)):
        if datas.led_down_lock[i] > 0:
            datas.led_down_lock[i] -= 1
            if datas.led_down_lock[i] == 0:
                for j in range(len(datas.sensor_down_lock)):
                    if (datas.sensor_down_lock[j] != 0):
                        for k in range(len(datas.sensor_influence_all[j])):
                            if datas.sensor_influence_all[j][k] == i:
                                datas.sensor_down_lock[j] = 0
        if datas.led_up_lock[i] > 0:
            datas.led_up_lock[i] -= 1
            if datas.led_up_lock[i] == 0:
                for j in range(len(datas.sensor_up_lock)):
                    if (datas.sensor_up_lock[j] != 0):
                        for k in range(len(datas.sensor_influence_all[j])):
                            if datas.sensor_influence_all[j][k] == i:
                                datas.sensor_up_lock[j] = 0


# [0.2]
# 조도 만족시키기 전 제어상태를 확인하고 총 영향도에 기반한 제어상태로 돌리기
# 1. 총 영향도가 가장 높은 조명으로 제어단계를 전부 변경
# 2. 만약 조명이 최고 수치라 올릴 수 없다면 다음 조명으로 변경. 반복
def led_setting_based_on_influence_sum(isLow):
    return


#     print("First Step Setting")
#     printer.print_control_lux()
#
#     for j in range(len(datas.sensor_influence_sum_part)):
#         target_led_rank = 0
#         print("%s Location Sensor Start" % str(j + 1))
#         for i in range(1, len(datas.sensor_influence_sum_part[j])):
#             while datas.led_state[datas.sensor_influence_sum_part[j][i]] > 1:
#                 # 높힐거랑 낮출거랑 같으면 멈춤
#                 if target_led_rank == i:
#                     break
#                 # 제어 해야되는데 최대치면 다음 영향도로 변경
#                 if datas.led_state[datas.sensor_influence_sum_part[j][target_led_rank]] == len(datas.led_control) - 1:
#                     print("Can't Control LED [%s]" % datas.sensor_influence_sum_part[j][target_led_rank])
#                     target_led_rank += 1
#                     print("Next Control Target LED [%s]" % datas.sensor_influence_sum_part[j][target_led_rank])
#                     continue
#                 print("LED %s [ UP ] : [%s] STEP -> [%s] STEP" % (
#                     datas.sensor_influence_sum_part[j][target_led_rank],
#                     datas.led_state[datas.sensor_influence_sum_part[j][target_led_rank]],
#                     datas.led_state[datas.sensor_influence_sum_part[j][target_led_rank]] + 1))
#                 print("LED %s [DOWN] : [%s] STEP -> [%s] STEP" % (
#                     datas.sensor_influence_sum_part[j][i], datas.led_state[datas.sensor_influence_sum_part[j][i]],
#                     datas.led_state[datas.sensor_influence_sum_part[j][i]] - 1))
#
#                 datas.led_state[datas.sensor_influence_sum_part[j][target_led_rank]] += 1
#                 datas.led_state[datas.sensor_influence_sum_part[j][i]] -= 1
#                 control_led(datas.sensor_influence_sum_part[j][target_led_rank],
#                             datas.led_state[datas.sensor_influence_sum_part[j][target_led_rank]])
#                 control_led(datas.sensor_influence_sum_part[j][i],
#                             datas.led_state[datas.sensor_influence_sum_part[j][i]])
#     print("Influence Sum Setting Step 1 Finish")
#     printer.print_control_lux()
#
#     for i in range(len(datas.sensor_influence_sum_part)):
#         print("%s Location Sensor Start" % str(i + 1))
#         for j in range(0, len(datas.sensor_influence_sum_part[i])):
#             canControl = True
#             if (j < len(datas.sensor_influence_sum_part[i]) - 1):
#                 while canControl:
#                     for k in range(j + 1, len(datas.sensor_influence_sum_part[i])):
#                         print("Try Control... %s %s" % (j, k))
#                         print(
#                             "Control Index  %s %s" % (
#                                 datas.sensor_influence_sum_part[i][j], datas.sensor_influence_sum_part[i][k]))
#                         print("influence cmp %s <= %s <= %s" % (
#                             str(datas.sensor_influence_value_sum_part[i][j] - datas.similar_led_range),
#                             datas.sensor_influence_value_sum_part[i][k],
#                             str(datas.sensor_influence_value_sum_part[i][j] + datas.similar_led_range)))
#                         print("State cmp %s > %s" % (
#                             datas.led_state[datas.sensor_influence_sum_part[i][j]],
#                             datas.led_state[datas.sensor_influence_sum_part[i][k]]))
#                         if ((datas.sensor_influence_value_sum_part[i][j] - datas.similar_led_range) <=
#                             datas.sensor_influence_value_sum_part[i][
#                                 k]) & (
#                                 datas.sensor_influence_value_sum_part[i][k] <= (
#                                 datas.sensor_influence_value_sum_part[i][
#                                     j] + datas.similar_led_range)) & (
#                                 datas.led_state[datas.sensor_influence_sum_part[i][j]] > datas.led_state[
#                             datas.sensor_influence_sum_part[i][k]]):
#                             print("GIVE 1 STEP LED %s[%s] -> LED %s[%s]" % (
#                                 datas.sensor_influence_sum_part[i][j],
#                                 datas.led_state[datas.sensor_influence_sum_part[i][j]],
#                                 datas.sensor_influence_sum_part[i][k],
#                                 datas.led_state[datas.sensor_influence_sum_part[i][k]]))
#                             datas.led_state[datas.sensor_influence_sum_part[i][k]] += 1
#                             datas.led_state[datas.sensor_influence_sum_part[i][j]] -= 1
#                             control_led(datas.sensor_influence_sum_part[i][k],
#                                         datas.led_state[datas.sensor_influence_sum_part[i][k]])
#                             control_led(datas.sensor_influence_sum_part[i][j],
#                                         datas.led_state[datas.sensor_influence_sum_part[i][j]])
#                             break
#                         if (k == len(datas.sensor_influence_sum_part[i]) - 1):
#                             canControl = False
#
#     print("Influence Sum Setting Step 2 Finish")
#     printer.print_control_lux()


def led_control_use_state(led_control, control_state):
    print("LED SETTING...")
    # print(control_state)
    # print(led_control)
    for idx in range(1, len(control_state)):
        ch1 = led_control[control_state[idx]][0]
        ch2 = led_control[control_state[idx]][1]
        ch3 = led_control[control_state[idx]][2]
        ch4 = led_control[control_state[idx]][3]
        print(f"LED {idx}: {ch1} {ch2} {ch3} {ch4}")
        led.set_LED(idx, ch1, ch2, ch3, ch4)
        time.sleep(0.2)
        # print("[" + str(idx) + "]:" + str(led_state[idx]) + "\t", end='')
        # if (idx != 0) & (idx % 6 == 0):
        #     print()
    print("FINISH")


def led_control_use_state_is_change(led_control, control_state):
    print("LED SETTING...")
    # print(control_state)
    # print(led_control)
    for idx in range(1, len(control_state)):
        if datas.led_is_change[idx] == True:
            ch1 = led_control[control_state[idx]][0]
            ch2 = led_control[control_state[idx]][1]
            ch3 = led_control[control_state[idx]][2]
            ch4 = led_control[control_state[idx]][3]
            print(f"LED {idx}: {ch1} {ch2} {ch3} {ch4}")
            led.set_LED(idx, ch1, ch2, ch3, ch4)
            time.sleep(0.2)
            # print("[" + str(idx) + "]:" + str(led_state[idx]) + "\t", end='')
            # if (idx != 0) & (idx % 6 == 0):
            #     print()
    for i in range(1, len(datas.led_is_change)):
        datas.led_is_change[i] = False
    print("FINISH")
