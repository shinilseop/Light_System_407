import Shin_Package.Open_Processor_NL.Open_Processor_NL_02.datas as datas

def select_control_led(sensor, influence_rank, isLow):
    # 높힐 LED 선정 (잠금 X, 제어 상태 최고 X) 영향도가 해당 센서에 가장 높은 조명 중 총영향도가 높은순서 or
    # 낮출 LED 선정 (잠금 X, 제어 상태 최저 X) 영향도가 해당 센서에 가장 높은 조명 중 총영향도가 낮은순서
    for i in range(len(influence_rank)):
        if (isLow) & (datas.led_state[influence_rank[i]] != len(datas.led_control) - 1) & (
                datas.led_up_lock[influence_rank[i]] == 0):
            control_led_idx = influence_rank[i]
            control_led_rank = i
            print("SELECT UP LED NUM : %s" % control_led_idx)
            break
        elif (not isLow) & (datas.led_state[influence_rank[i]] != 1) & (
                datas.led_down_lock[influence_rank[i]] == 0):
            control_led_idx = influence_rank[i]
            control_led_rank = i
            print("SELECT DOWN LED NUM : %s" % control_led_idx)
            break
        else:
            print("%s is Can't Control LED[(Locked) or (State is Max or Min)]." % influence_rank[i])

        # 만약 해당 센서에 모든 조명이 제어가 불가능하다면 센서잠금.
        if (i == len(influence_rank) - 1):
            if isLow:
                print("Sensor Up Lock")
                datas.sensor_up_lock[sensor] = 1
                datas.sensor_up_lock_cnt[0] += 1
                datas.has_control_before[0]=False
            else:
                print("Sensor Down Lock")
                datas.sensor_down_lock[sensor] = 1
                datas.sensor_down_lock_cnt[0] += 1
                datas.has_control_before[0]=False

            return -1, -1

    return control_led_idx, control_led_rank


# 만약 유사한 영향도를 가진 조명이 존재한다면 해당 조명과 제어상태를 비교하여 높은 조명을 우선적으로 다운
# 수정 사항 : 잠금 검사가 존재 하지 않아서 잠금검사 실시
def find_similar_influence(sensor, now_rank, influence_rank, influence_value, isLow):
    control_led_idx = influence_rank[now_rank]
    control_led_rank = now_rank

    for j in range(control_led_rank + 1, len(influence_rank)):
        if (influence_value[control_led_rank] - datas.similar_led_range <=
            influence_value[j]) & (
                influence_value[j] <=
                influence_value[control_led_rank] + datas.similar_led_range):

            if (isLow):
                if (datas.led_state[influence_rank[control_led_rank]] > datas.led_state[
                    influence_rank[j]]) & (
                        datas.led_state[influence_rank[control_led_rank]] < len(datas.led_control) - 1) & (
                        datas.led_up_lock[influence_rank[j]] == 0):
                    control_led_idx = influence_rank[j]
                    control_led_rank = j
                    print("CHANGE(SIMILAR) LED NUM : %s" % control_led_idx)
            else:
                if (datas.led_state[influence_rank[control_led_rank]] < datas.led_state[
                    influence_rank[j]]) & (
                        datas.led_state[influence_rank[control_led_rank]] > 1) & (
                        datas.led_down_lock[influence_rank[j]] == 0):
                    control_led_idx = influence_rank[j]
                    control_led_rank = j
                    print("CHANGE(SIMILAR) LED NUM : %s" % control_led_idx)

    return control_led_idx, control_led_rank