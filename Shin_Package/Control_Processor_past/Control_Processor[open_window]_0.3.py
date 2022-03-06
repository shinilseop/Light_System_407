# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
import math

import pandas as pd
from datetime import datetime

from Core import switch
from NL_System import Base_Process as bp
import threading, time
from Core.arduino_color_sensor import acs
from Core.Intsain_Illum import II
from Core.Intsain_Curr import IC

import Shin_Package.others.shin_Intsain_LED as led

"""
버전 정보 
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
"""

# 제어조건(변형가능)
led_lock_range = 2  # LED 잠금시 잠굴 범위 값
similar_led_range = 1  # 방향성고려나 제어조도기준 선정할 때 영향도의 비슷한 범위를 위한 값
object_illum = 500
first_matched = False
save_folder = "1"
accel = 5 # 5도 나쁘지 않을것 같음 다만 방향성고려가 제어에 들어가야 될듯함.

# 저장 변수
df_record = []
led_state_case_limit = []
illum_add = []

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
# new led control index
led_control = [[0, 0, 0, 0], [0, 16, 0, 0], [0, 14, 6, 0], [0, 14, 7, 0], [0, 13, 9, 0], [0, 14, 8, 0], [0, 15, 7, 0],
               [0, 15, 8, 0], [0, 16, 8, 0], [0, 16, 9, 0], [0, 16, 10, 0], [0, 17, 9, 0], [0, 17, 10, 0],
               [0, 18, 11, 0], [0, 18, 12, 0], [0, 19, 11, 0], [0, 19, 12, 0], [0, 20, 11, 0], [0, 20, 12, 0],
               [0, 20, 13, 0], [0, 21, 13, 0], [0, 22, 13, 0], [0, 22, 14, 0], [0, 21, 15, 0], [0, 23, 14, 0],
               [0, 25, 13, 0], [0, 24, 14, 0], [0, 23, 15, 0], [0, 25, 14, 0], [0, 24, 15, 0], [0, 25, 15, 0],
               [0, 24, 16, 0], [0, 25, 16, 0], [0, 26, 16, 0], [0, 27, 16, 0], [0, 28, 15, 0], [0, 27, 17, 0],
               [0, 28, 16, 0], [0, 28, 17, 0], [0, 29, 16, 0], [0, 29, 17, 0], [0, 29, 18, 0], [0, 30, 17, 0],
               [0, 29, 19, 0], [0, 29, 20, 0], [0, 30, 18, 0], [0, 30, 19, 0], [0, 30, 20, 0], [0, 31, 19, 0],
               [0, 30, 21, 0], [0, 31, 20, 0], [0, 31, 21, 0], [0, 32, 20, 0], [0, 32, 21, 0], [0, 31, 23, 0],
               [0, 33, 20, 0], [0, 32, 23, 0], [0, 33, 21, 0], [0, 33, 22, 0], [0, 33, 23, 0], [0, 34, 22, 0],
               [0, 34, 23, 0], [0, 35, 22, 0], [0, 34, 24, 0], [0, 34, 25, 0], [0, 35, 24, 0], [0, 34, 26, 0],
               [0, 36, 23, 0], [0, 36, 24, 0], [0, 37, 23, 0], [0, 36, 25, 0], [0, 37, 24, 0], [0, 36, 26, 0],
               [0, 37, 25, 0], [0, 37, 26, 0], [0, 38, 25, 0], [0, 37, 27, 0], [0, 39, 24, 0], [0, 38, 26, 0],
               [0, 39, 25, 0], [0, 38, 27, 0], [0, 39, 26, 0], [0, 40, 25, 0], [0, 38, 28, 0], [0, 39, 27, 0],
               [0, 41, 25, 0], [0, 39, 28, 0], [0, 40, 27, 0], [0, 41, 26, 0], [0, 40, 28, 0], [0, 39, 30, 0],
               [0, 41, 28, 0], [0, 42, 27, 0], [0, 41, 29, 0], [0, 42, 28, 0], [0, 43, 27, 0], [0, 41, 30, 0],
               [0, 42, 29, 0], [0, 42, 30, 0], [0, 43, 29, 0], [0, 43, 30, 0], [0, 44, 29, 0], [0, 44, 30, 0],
               [0, 45, 29, 0], [0, 44, 31, 0], [0, 45, 30, 0], [0, 45, 31, 0], [0, 46, 30, 0], [0, 46, 31, 0],
               [0, 47, 30, 0], [0, 46, 32, 0], [0, 47, 31, 0], [0, 48, 30, 0], [0, 47, 32, 0], [0, 49, 30, 0],
               [0, 46, 34, 0], [0, 48, 32, 0], [0, 49, 31, 0], [0, 48, 33, 0], [0, 49, 32, 0], [0, 48, 34, 0],
               [0, 49, 33, 0], [0, 50, 32, 0], [0, 50, 33, 0], [0, 49, 34, 0], [0, 49, 35, 0], [0, 50, 34, 0],
               [0, 52, 34, 0], [0, 51, 34, 0], [0, 50, 36, 0], [0, 51, 35, 0], [0, 53, 33, 0], [0, 50, 37, 0],
               [0, 52, 35, 0], [0, 54, 33, 0], [0, 52, 36, 0], [0, 53, 35, 0], [0, 54, 34, 0], [0, 53, 36, 0],
               [0, 55, 34, 0], [0, 54, 36, 0], [0, 55, 35, 0], [0, 56, 34, 0], [0, 53, 38, 0], [0, 54, 37, 0],
               [0, 55, 36, 0], [0, 55, 37, 0], [0, 56, 36, 0], [0, 55, 38, 0], [0, 56, 37, 0], [0, 58, 35, 0],
               [0, 55, 39, 0], [0, 56, 38, 0], [0, 54, 41, 0], [0, 57, 38, 0], [0, 59, 36, 0], [0, 55, 41, 0],
               [0, 57, 39, 0], [0, 60, 36, 0], [0, 56, 41, 0], [0, 58, 39, 0], [0, 59, 38, 0], [0, 60, 37, 0],
               [0, 56, 42, 0], [0, 59, 39, 0], [0, 60, 38, 0], [0, 58, 41, 0], [0, 59, 40, 0], [0, 59, 41, 0],
               [0, 60, 40, 0], [0, 62, 38, 0], [0, 58, 43, 0], [0, 59, 42, 0], [0, 61, 40, 0], [0, 62, 39, 0],
               [0, 60, 42, 0], [0, 61, 41, 0], [0, 62, 40, 0], [0, 62, 41, 0], [0, 63, 40, 0], [0, 60, 44, 0],
               [0, 62, 42, 0], [0, 63, 41, 0], [0, 63, 42, 0], [0, 64, 41, 0], [0, 61, 45, 0], [0, 63, 43, 0],
               [0, 64, 42, 0], [0, 66, 40, 0], [0, 61, 46, 0], [0, 64, 43, 0], [0, 65, 42, 0], [0, 67, 40, 0],
               [0, 64, 44, 0], [0, 65, 43, 0], [0, 68, 40, 0], [0, 64, 45, 0], [0, 66, 43, 0], [0, 68, 41, 0],
               [0, 63, 47, 0], [0, 66, 44, 0], [0, 68, 42, 0], [0, 67, 44, 0], [0, 68, 43, 0], [0, 69, 42, 0],
               [0, 67, 45, 0], [0, 68, 44, 0], [0, 69, 43, 0], [0, 66, 47, 0], [0, 67, 46, 0], [0, 68, 45, 0],
               [0, 70, 43, 0], [0, 67, 47, 0], [0, 69, 45, 0], [0, 70, 44, 0], [0, 67, 48, 0], [0, 69, 46, 0],
               [0, 71, 44, 0], [0, 68, 48, 0], [0, 69, 47, 0], [0, 70, 46, 0], [0, 72, 44, 0], [0, 69, 48, 0],
               [0, 70, 47, 0], [0, 71, 46, 0], [0, 70, 48, 0], [0, 71, 47, 0], [0, 69, 50, 0], [0, 70, 49, 0],
               [0, 72, 47, 0], [0, 69, 51, 0], [0, 73, 47, 0]]
led_control_lux = [0, 24, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36, 37, 38, 43, 44, 45, 46, 48, 49, 51, 53, 55, 56, 57,
                   58, 59, 60, 61, 62, 63, 64, 66, 67, 68, 70, 71, 72, 73, 74, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86,
                   88, 89, 91, 92, 93, 94, 96, 97, 98, 100, 101, 103, 104, 105, 107, 108, 109, 110, 112, 113, 114, 115,
                   116, 117, 118, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 132, 133, 134, 135, 137, 138,
                   139, 141, 142, 143, 144, 145, 148, 149, 151, 152, 154, 155, 157, 158, 161, 162, 164, 166, 167, 168,
                   169, 170, 171, 173, 174, 175, 177, 178, 180, 181, 182, 184, 185, 186, 187, 189, 190, 193, 194, 195,
                   196, 197, 198, 200, 201, 202, 203, 204, 206, 207, 208, 209, 210, 211, 213, 214, 216, 217, 218, 219,
                   220, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 240, 241,
                   242, 243, 244, 245, 246, 247, 249, 250, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263,
                   264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284,
                   285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 299, 300, 301, 302, 303, 304, 306]

# init LED state
led_state_0 = [0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0]
led_state = [0,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]

led_down_lock = [0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0]

led_up_lock = [0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0]

sensor_lock = [0, 0, 0,
               0, 0, 0,
               0, 0, 0]

sensor_down_lock = [0, 0, 0,
                    0, 0, 0,
                    0, 0, 0]
sensor_up_lock = [0, 0, 0,
                  0, 0, 0,
                  0, 0, 0]
sensor_down_lock_cnt = [0]
sensor_up_lock_cnt = [0]

sensor_lock_cnt = [0]

# led inflence
sensor_influence_all = [[8, 2, 7, 9, 1, 3, 14, 15, 13],
                        [4, 3, 9, 10, 8, 5, 11, 2, 15, 16],
                        [5, 11, 12, 6, 10, 4, 17, 16, 18],
                        [14, 8, 20, 15, 13, 7, 19, 21, 9],
                        [15, 16, 9, 22, 21, 10, 14, 17, 8, 11, 20],
                        [17, 11, 23, 16, 18, 24, 22, 10, 12],
                        [20, 26, 19, 21, 27, 25, 14, 13, 15],
                        [28, 27, 21, 22, 23, 20, 29, 26, 15, 16],
                        [23, 29, 24, 28, 22, 30, 17, 16, 18]]
sensor_influence_value_all = [[94.5, 94.4, 58.3, 58.2, 58.1, 58.0, 29.4, 24.2, 24.1],
                              [76.7, 76.6, 76.6, 76.5, 38.1, 38.0, 38.0, 37.9, 26.8, 26.8],
                              [94.4, 94.4, 58.2, 58.1, 58.1, 58.0, 29.4, 24.2, 24.2],
                              [94.5, 62.1, 62.1, 58.1, 58.1, 41.2, 41.2, 41.2, 41.1],
                              [88.9, 88.3, 54.6, 54.4, 54.1, 54.0, 34.4, 34.4, 25.9, 25.8, 24.5],
                              [94.6, 62.2, 62.2, 58.2, 58.1, 41.3, 41.2, 41.1, 41.1],
                              [94.8, 94.3, 58.1, 58.1, 58.1, 58.0, 29.6, 24.2, 24.2],
                              [76.7, 76.6, 76.5, 76.5, 38.1, 38.1, 38.0, 37.9, 26.8, 26.8],
                              [94.7, 94.3, 58.2, 58.2, 58.0, 58.0, 29.5, 24.2, 24.2]]

sensor_influence_individual_part = [[8, 2, 7, 1],
                                    [4, 3, 9, 10],
                                    [5, 11, 12, 6],
                                    [14, 13],
                                    [15, 16],
                                    [17, 18],
                                    [20, 26, 19, 25],
                                    [28, 27, 21, 22],
                                    [23, 29, 24, 30]]
sensor_influence_value_individual_part = [[94.5, 94.4, 58.3, 58.1],
                                          [76.7, 76.6, 76.6, 76.5],
                                          [94.4, 94.4, 58.2, 58.1],
                                          [94.5, 58.1],
                                          [88.9, 88.3],
                                          [94.6, 58.1],
                                          [94.8, 94.3, 58.1, 58.0],
                                          [76.7, 76.6, 76.5, 76.5],
                                          [94.7, 94.3, 58.2, 58.0]]
sensor_influence_sum_part = [[8, 2, 7, 1],
                             [10, 9, 3, 4],
                             [11, 5, 12, 6],
                             [14, 13],
                             [15, 16],
                             [17, 18],
                             [20, 26, 19, 25],
                             [22, 21, 28, 27],
                             [23, 29, 24, 30]]
sensor_influence_value_sum_part = [[253.8, 181.8, 140.4, 105.5],
                                   [286.6, 286.3, 208.1, 207.5],
                                   [253.9, 181.6, 140.9, 105.5],
                                   [238.1, 140.0],
                                   [289.9, 289.3],
                                   [238.1, 140.7],
                                   [252.4, 181.6, 141.2, 105.0],
                                   [285.9, 285.6, 207.7, 207.5],
                                   [252.7, 181.4, 141.5, 105.1]]

sensor_influence_sum_part_reverse = [[1, 7, 2, 8],
                                     [4, 3, 9, 10],
                                     [6, 12, 5, 11],
                                     [13, 14],
                                     [16, 15],
                                     [18, 17],
                                     [25, 19, 26, 20],
                                     [27, 28, 21, 22],
                                     [30, 24, 29, 23]]
sensor_influence_value_sum_part_reverse = [[105.5, 140.4, 181.8, 253.8],
                                           [207.5, 208.1, 286.3, 286.6],
                                           [105.5, 140.9, 181.6, 253.9],
                                           [140.0, 238.1],
                                           [289.3, 289.9],
                                           [140.7, 238.1],
                                           [105.0, 141.2, 181.6, 252.4],
                                           [285.9, 285.6, 207.7, 207.5],
                                           [105.1, 141.5, 181.4, 252.7]]
#######################new sum part
sensor_influence_sum_part_reverse = [[1, 7, 2, 3, 8, 9],
                                     [4, 3, 9, 10],
                                     [6, 12, 5, 4, 11, 10],
                                     [13, 14, 20, 8, 15],
                                     [21, 22, 9, 10, 16, 15],
                                     [18, 17, 23, 11, 16],
                                     [25, 19, 26, 27, 20, 21],
                                     [27, 28, 21, 22],
                                     [30, 24, 29, 28, 23, 22]]
sensor_influence_value_sum_part_reverse = [[105.5, 140.4, 181.8, 208.1, 253.8, 286.3],
                                           [207.5, 208.1, 286.3, 286.6],
                                           [105.5, 140.9, 181.6, 207.5, 253.9, 286.6],
                                           [140.0, 238.1, 252.4, 253.8, 289.9],
                                           [285.6, 285.9, 286.3, 286.6, 289.3, 289.9],
                                           [140.7, 238.1, 252.7, 253.9, 289.3],
                                           [105.0, 141.2, 181.6, 207.5, 252.4, 285.6],
                                           [285.9, 285.6, 207.7, 207.5],
                                           [105.1, 141.5, 181.4, 207.7, 252.7, 285.9]]


sensor_influence_sum_all = [[15, 9, 8, 14, 3, 2, 7, 13, 1],
                            [15, 16, 10, 9, 11, 8, 3, 4, 2, 5],
                            [16, 10, 11, 17, 4, 5, 12, 18, 6],
                            [15, 9, 21, 8, 20, 14, 19, 7, 13],
                            [15, 16, 10, 9, 22, 21, 11, 8, 23, 20, 17, 14],
                            [16, 10, 22, 11, 23, 17, 24, 12, 18],
                            [15, 21, 20, 14, 27, 26, 19, 13, 25],
                            [15, 16, 22, 21, 23, 20, 28, 27, 26, 29],
                            [16, 22, 23, 17, 28, 29, 24, 18, 30]]
sensor_influence_value_sum_all = [
    [289.8907749, 286.3490037, 253.8269373, 238.0903321, 208.1389668, 181.7594834, 140.4187454, 140.0373432,
     105.4903321],
    [289.8907749, 289.3086347, 286.6149815, 286.3490037, 253.857048, 253.8269373, 208.1389668, 207.5430258, 181.7594834,
     181.6352768],
    [289.3086347, 286.6149815, 253.857048, 238.1442804, 207.5430258, 181.6352768, 140.921845, 140.7148339, 105.500369],
    [289.8907749, 286.3490037, 285.6037638, 253.8269373, 252.4343173, 238.0903321, 141.2405166, 140.4187454,
     140.0373432],
    [289.8907749, 289.3086347, 286.6149815, 286.3490037, 285.9199262, 285.6037638, 253.857048, 253.8269373, 252.7416974,
     252.4343173, 238.1442804, 238.0903321],
    [289.3086347, 286.6149815, 285.9199262, 253.857048, 252.7416974, 238.1442804, 141.5391144, 140.921845, 140.7148339],
    [289.8907749, 285.6037638, 252.4343173, 238.0903321, 207.4828044, 181.6390406, 141.2405166, 140.0373432,
     105.0349077],
    [289.8907749, 289.3086347, 285.9199262, 285.6037638, 252.7416974, 252.4343173, 207.701107, 207.4828044, 181.6390406,
     181.4069373],
    [289.3086347, 285.9199262, 252.7416974, 238.1442804, 207.701107, 181.4069373, 141.5391144, 140.7148339,
     105.0562362]]

sersor_influence_sum_all_reverse = []
sersor_influence_value_sum_all_reverse = []

sensor_influence_sum = [15, 16, 10, 9, 22, 21, 11, 8, 23, 20, 17, 14, 3, 28, 4, 27, 2, 26, 5, 29, 24, 19, 24, 19, 12,
                        18, 7, 13, 6, 1, 30, 25]
sensor_influence_value_sum = [2.898907749, 2.893086347, 2.866149815, 2.863490037, 2.859199262, 2.856037638, 2.53857048,
                              2.538269373, 2.527416974, 2.524343173,
                              2.381442804, 2.380903321, 2.081389668, 2.07701107, 2.075430258, 2.074828044, 1.817594834,
                              1.816390406, 1.816352768, 1.814069373,
                              1.415391144, 1.412405166, 1.40921845, 1.407148339, 1.404187454, 1.400373432, 1.05500369,
                              1.054903321, 1.050562362, 1.050349077]
def illum_thread(illum_add):
    time.sleep(60)
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

    for i in range(10):
        #밤에서 일출에서 오전으로
        print('CHANGE ILLUM %s'%(datetime.now()))
        illum_add[0] += 10
        illum_add[1] += 20
        illum_add[2] += 20
        illum_add[4] += 10
        illum_add[5] += 20
        illum_add[8] += 10
        time.sleep(60)


def start_data_center():
    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()


def process(start, case_num):
    locking_init()

    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()

    # 초기 변수 설정
    first_matched = True
    first = True
    get_times = 0
    wait_curr = 0
    wait_illum = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    time.sleep(5)

    # 센서 데이터 값 초기화
    for i in range(1, 10):
        acs1.set_sensor_data(i, 0, 0)
        II1.set_illum_data(i - 1, 0)
        IC1.set_curr_data(i - 1, 0)
    data_flag = True
    data_count = 0

    # 데이터 받기 (초기화 한 후에 모든 데이터가 다 들어올때 까지 대기)
    # 색온도는 초기값 설정을 안하기 때문에 여기서는 체크 x
    while data_flag:
        data_flag = False

        II_illum = II1.get_illum_data()[:9]
        IC_curr = IC1.get_curr_data()[:10]

        print(II_illum)
        print(IC_curr)

        # 조도 9개 체크
        for i in II_illum:
            if i == 0:
                print(i)
                data_flag = True
                continue

        # 소비전력 9개 체크
        for i in IC_curr:
            if i == 0:
                data_flag = True
                continue

        if data_count > 30:
            break
        else:
            time.sleep(0.5)
            data_count = data_count + 1

    # 초기값 설정 시작
    II_illum = II1.get_illum_data()[:9]
    IC_curr = IC1.get_curr_data()[:10]
    sum_curr = 0
    min_illum = 99999
    # 단위구역이 연속하는경우 KS C 7612 기준 평균 계산법
    sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[5] * 2 + \
                II_illum[6] + II_illum[7] * 2 + II_illum[8]
    avg_illum = sum_illum / 16
    # 초기 대기 조도 설정
    for i in range(9):
        sum_curr += IC_curr[i]
        if (min_illum > II_illum[i]):
            min_illum = II_illum[i]
    print("10\t\t-1\t\t-1\t\t" + str(IC_curr[9]))
    # 대기전력 설정
    sum_curr += IC_curr[9]

    # 대기전력 및 대기조도 출력 및 led 초기 제어
    if sum_curr > 0:
        wait_curr = round(sum_curr, 2)
        print("대기전력 : %s" % wait_curr)
        print("대기조도")
        for i in range(9):
            wait_illum[i] = II_illum[i]
            print(str(i + 1) + " wait illum : " + str(wait_illum[i]))
        led_control_use_state(led_control, led_state)
        time.sleep(5)

    isFinish = True

    illum_add_thread = threading.Thread(target=illum_thread, args=(illum_add,))
    illum_add_thread.start()

    # 제어 시작
    while isFinish:
        """
        센서 데이터의 일관성을 위해 값을 0으로 초기화 하고
        모든 데이터가 받을때까지 검사하다가 받는 순간 알고리즘 시작
        """

        # 센서 데이터 초기화
        for i in range(1, 10):
            acs1.set_sensor_data(i, 0, 0)
            II1.set_illum_data(i - 1, 0)
            IC1.set_curr_data(i - 1, 0)
        data_flag = True
        data_count = 0
        while data_flag:
            data_flag = False

            # 값 불러옴
            acs_cct = acs1.get_sensor_data()[0][:9]
            II_illum = II1.get_illum_data()[:9]
            IC_curr = IC1.get_curr_data()[:10]

            # CCT 체크
            for i in acs_cct:
                if i == 0:
                    data_flag = True
                    continue

            # 조도 체크
            for i in II_illum:
                if i == 0:
                    data_flag = True
                    continue

            # 소비 전력 체크
            for i in IC_curr:
                if i == 0:
                    data_flag = True
                    continue

            # 만약 100번 카운트 하는동안 받지 못하면 릴레이를 한번 온오프 시작
            if data_count > 100:
                switch.onnoff()
                data_count = 0
            else:
                time.sleep(0.5)
                data_count = data_count + 1

        # 문제없으면 받아와서 알고리즘 실행
        acs_cct = acs1.get_sensor_data()[0][:9]
        II_illum = II1.get_illum_data()[:9]
        IC_curr = IC1.get_curr_data()[:10]

        ###############################################################################
        # 센서값에 정오조도 더함
        # noon_lux=[1640.54,738.45,1320.48,310.36,329.14,565.44,179.00,202.07,164.87] # 블라인드 100% 오픈
        # noon_lux=[497.99,222.99,371.25,118.34,124.12,171.46,79.65,90.43,76.15]
        # noon_lux=[316.32,138.80,242.88,60.83,65.54,91.94,41.24,45.21,39.11] # 1250cm, 90도
        # noon_lux=[298.24,132.78,233.07,54.99,59.87,84.62,35.40,39.68,33.08] # 1300cm, 90도
        # noon_lux=[283.60,122.47,210.18,52.06,55.15,76.40,32.89,35.99,30.50] # 1350cm, 90도
        # noon_lux=[283.60,123.33,218.36,51.09,55.15,78.22,32.89,35.99,30.50] # 1400cm, 90도
        for i in range(9):
            II_illum[i] += illum_add[i]
        ###############################################################################

        # 필요 변수 설정
        sum_cct = 0.0  # CCT 합산용
        sum_curr = -wait_curr  # 소비전력 합산용
        min_illum = 10000  # 균제도 계산을 위한 변수
        uniformity = 0.0  # 균제도 용

        # 대기조도 제외
        for i in range(9):
            II_illum[i] -= wait_illum[i]

        # 단위구역이 연속하는경우 KS C 7612 기준 평균 계산법
        sum_illum = II_illum[0] + II_illum[1] * 2 + II_illum[2] + II_illum[3] * 2 + II_illum[4] * 4 + II_illum[5] * 2 + \
                    II_illum[6] + II_illum[7] * 2 + II_illum[8]

        # 센서값 데이터프레임으로 통합 및 필요한 값 계산 및 출력
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
        sum_curr = round(sum_curr, 2)
        if (avg_illum != 0):
            uniformity = round(min_illum / avg_illum, 7)
        print(
            "Avg_CCT\t\t%s\t\tAvg_Ill\t\t%s\t\tSum_Curr\t\t%s\t\tUniformity\t\t%s" % (
                str(avg_cct)[:7], str(avg_illum)[:8], str(sum_curr), str(uniformity)))

        # 500보다 미만 -> 상승하러 & 500 이상 -> 낮추러 (gettimes는 처음 시작할때 처음 상태 때문에 설정)
        # 처음이 아니라면
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

        if (sensor_up_lock_cnt[0] == 9) & (sensor_down_lock_cnt[0] == 9):
            print("All LED LOCK")
            break
        get_times += 1
        save_flag=False
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
                save_data(start, df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_success_E%s_U%s" % (int(sum_curr), uniformity), True)
            else:
                save_data(start, df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_E%s_U%s" % (int(sum_curr), uniformity), False)

            # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
            # if (avg_illum > 500):
            #     led_setting_based_on_influence_sum(False)
            # else:
            #     led_setting_based_on_influence_sum(True)
        else:
            if (avg_illum < 490):
                first=True
                print("AVG Illum is Low")
                illum_before_needs(II_illum, avg_illum)
            elif (490 <= avg_illum) & (avg_illum <= 510):
                print("AVG Illum is Matched")
                # 처음 평균조도를 만족한 순간이라면
                # 잠금 상태를 한번 초기화 하고 시작
                # 조도가 극한으로 높은 상황에서 만족상태를 달성할때까지 보면
                # 조명을 24[첫단계]로 끄는 경우 때문에
                # 지점을 잠궈버리는 경우가 많음

                # 480<= 지점별 조도 <= 520 안에 모든 지점이 만족한다면 스텝별 저장이름에 success를 추가해서 저장
                save_flag = True
                for i in range(9):
                    if (II_illum[i] < 480) | (520 < II_illum[i]):
                        save_flag = False
                        break

                if first_matched:
                    first_matched = False
                    locking_init()

                # if(not save_flag):
                #     illum_match_needs(II_illum, avg_illum)
                illum_match_needs(II_illum, avg_illum)
            elif (510 < avg_illum):
                first=True
                print("AVG Illum is High")
                illum_after_needs(II_illum, avg_illum)


            # 기준을 만족하는 경우랑 일반의 경우 step 별로 저장
            if (490 <= avg_illum) & (avg_illum <= 510) & save_flag:
                time.sleep(1)
                # 값 불러옴
                acs_cct = acs1.get_sensor_data()[0][:9]
                II_illum = II1.get_illum_data()[:9]
                IC_curr = IC1.get_curr_data()[:10]
                save_data(start, df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_success_E%s_U%s" % (int(sum_curr), uniformity), True)
            else:
                save_data(start, df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity,
                          get_times,
                          "_E%s_U%s" % (int(sum_curr), uniformity), False)

        # 현재 데이터 상태 출력
        print_control_lux()
        # print_led_locking_state(led_up_lock, "UP")
        # print_led_locking_state(led_down_lock, "DOWN")
        # print_sensor_locking_state()
        print_natural_light_state()
        # time.sleep(5)
        # if (get_times >= led_state_case_limit[case_num]):
        #     isFinish = False
        #     break


# 잠금 초기화 하는 함수[조명 업,다운, 센서]
def locking_init():
    print("Locking Initializing")
    for i in range(len(led_up_lock)):
        led_up_lock[i] = 0
        led_down_lock[i] = 0
        if i < len(sensor_up_lock):
            sensor_up_lock[i] = 0
            sensor_down_lock[i] = 0


# 스텝별로 제어 상태, 센서 값 저장하는 함수
def save_data(start, df_record, acs_cct, II_illum, IC_curr, avg_cct, avg_illum, sum_curr, uniformity, get_times,
              save_name,
              isPrint):
    step_end = datetime.now()
    led_num_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                    25, 26, 27, 28, 29, 30]
    df_record.append(pd.DataFrame(led_num_list, columns=['led']))
    for idx in range(1, len(led_state)):
        df_record[len(df_record) - 1].loc[idx - 1, 'control'] = led_control_lux[led_state[idx]]
        if (idx < 10):
            df_record[len(df_record) - 1].loc[idx - 1, 'cct'] = acs_cct[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'illum'] = II_illum[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = IC_curr[idx - 1]
            df_record[len(df_record) - 1].loc[idx - 1, 'natural_light'] = illum_add[idx - 1]
        elif (idx < 11):
            df_record[len(df_record) - 1].loc[idx - 1, 'curr'] = IC_curr[idx - 1]
    df_record[len(df_record) - 1].loc[10, 'cct'] = avg_cct
    df_record[len(df_record) - 1].loc[10, 'illum'] = avg_illum
    df_record[len(df_record) - 1].loc[10, 'curr'] = sum_curr
    df_record[len(df_record) - 1].loc[0, 'uniformity'] = uniformity
    df_record[len(df_record) - 1].loc[0, 'start'] = start
    df_record[len(df_record) - 1].loc[0, 'end'] = step_end
    df_record[len(df_record) - 1].loc[0, 'diff_time'] = step_end - start

    if (isPrint):
        print('=' * 20)
        # print(df_record[len(df_record) - 1])
        print('====save_success====')
        print('=' * 20)

    df_record[len(df_record) - 1].to_csv(
        "D:\\BunkerBuster\\Desktop\\shin_excel\\24시작\\new_index\\%s\\[%s]_step%s.csv" % (
            save_folder, get_times - 1, save_name))
    print(start, "->", step_end)


# 현재 컨트롤 lux 상태 출력
def print_control_lux():
    print("Control Lux")
    for idx in range(1, len(led_state)):
        print("%s\t" % led_control_lux[led_state[idx]], end='')
        if idx % 6 == 0:
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
    for idx in range(len(sensor_up_lock)):
        print("%s\t" % sensor_up_lock[idx], end='')
        if idx % 3 == 2:
            print()
    print("Sensor Down Locking State")
    for idx in range(len(sensor_down_lock)):
        print("%s\t" % sensor_down_lock[idx], end='')
        if idx % 3 == 2:
            print()
    print()

def print_natural_light_state():
    for i in range(len(illum_add)):
        print(illum_add[i], ' ', end='')
        if (i % 3 == 2):
            print()


# LED 제어
def control_led(led_num, control_step):
    locking_init()
    led.set_LED(led_num, led_control[control_step][0], led_control[control_step][1], led_control[control_step][2],
                led_control[control_step][3])


# 평균조도가 작은경우
def illum_before_needs(II_illum, avg_illum):
    target = 99999
    min_sensor = -1

    # 최소 지점 선정
    for i in range(9):
        if II_illum[i] < target:
            if sensor_up_lock[i] != 1:
                min_sensor = i
                target = II_illum[min_sensor]

    print('SELECT %s Position' % (min_sensor + 1))
    control_step = math.ceil(abs(object_illum - II_illum[min_sensor]) / accel)

    if min_sensor == -1:
        locking_init()
        # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
        if (avg_illum > 500):
            led_setting_based_on_influence_sum(False)
        else:
            led_setting_based_on_influence_sum(True)
        # exit()

    led_up(min_sensor, sensor_influence_sum_part, sensor_influence_value_sum_part, control_step)


# 평균조도가 만족될떄
def illum_match_needs(II_illum, avg_illum):
    diff_max_sensor = -1
    diff_value = 0

    # 목표조도로부터 절댓값 차이가 가장 큰지점 채택
    for i in range(9):
        if (sensor_up_lock[i] != 1 & (II_illum[i] - object_illum < 0)) | (
                sensor_down_lock[i] != 1 & (II_illum[i] - object_illum > 0)):
            if abs(object_illum - II_illum[i]) > abs(diff_value):
                diff_max_sensor = i
                diff_value = II_illum[i] - object_illum

    print('SELECT %s Position' % (diff_max_sensor + 1))

    if diff_max_sensor == -1:
        locking_init()
        # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
        if (avg_illum > 500):
            led_setting_based_on_influence_sum(False)
        else:
            led_setting_based_on_influence_sum(True)
        # exit()

    control_step = math.ceil(abs(object_illum - II_illum[diff_max_sensor]) / accel)

    # 평균조도와 지점 조도의 차이가 양수인 경우 조도가 초과하므로 하향점등 후 해당 조명 상향점등 잠금
    if diff_value >= 0:
        # 조명 선정 및 제어
        control_led = led_down(diff_max_sensor, sensor_influence_all, sensor_influence_value_all, control_step)

        # 잠금 시작
        if control_led != -1:
            print("Up Locking : %s" % control_led)
            led_up_lock[control_led] = 1

    # 평균조도와 지점 조도의 차이가 음수인 경우 조도가 부족하므로 상향점등 후 해당 조명 하향점등 잠금
    else:
        # 조명 선정 및 제어
        control_led = led_up(diff_max_sensor, sensor_influence_all, sensor_influence_value_all, control_step)

        # 잠금 시작
        if control_led != -1:
            print("Down Locking : %s" % control_led)
            led_down_lock[control_led] = 1


# 평균조도가 초과될 때
def illum_after_needs(II_illum, avg_illum):
    target = 0
    max_sensor = -1

    # 최고 지점 선정
    for i in range(9):
        if II_illum[i] > target:
            if sensor_down_lock[i] != 1:
                max_sensor = i
                target = II_illum[max_sensor]

    print('SELECT %s Position' % (max_sensor + 1))
    control_step = math.ceil(abs(object_illum - II_illum[max_sensor]) / accel)

    if max_sensor == -1:
        locking_init()
        # 현재 제어상태를 총영향도에 기반한 제어상태로 변경
        if (avg_illum > 500):
            led_setting_based_on_influence_sum(False)
        else:
            led_setting_based_on_influence_sum(True)
        # exit()
    else:
        led_down(max_sensor, sensor_influence_sum_part_reverse, sensor_influence_value_sum_part_reverse, control_step)


# 낮출 조명을 선정하는 단계 영향도는 이전 제어하는 함수에서 설정해준다.
def led_down(max_sensor, influence_rank, influence_value, control_step=1):
    # 잠금 및 제어가능 점검
    control_led_idx, control_led_rank = select_control_led(max_sensor, influence_rank, False)
    if (control_led_idx == -1):
        print("Can't Control LED near by %s Sensor." % (max_sensor + 1))
        return -1
    # 유사한 영향도를 가진 조명의 제어 상태 비교
    control_led_idx, control_led_rank = find_similar_influence(max_sensor, control_led_rank, influence_rank,
                                                               influence_value, False)

    ################################0.6################################
    if (led_state[control_led_idx] - control_step < 1):
        print("CHANGE CONTROL STEP [%s] -> [%s] (CAUSE : %s LED STATE = %s" % (
            control_step, led_state[control_led_idx] - 1, control_led_idx, led_state[control_led_idx]))
        control_step = led_state[control_led_idx] - 1
    ###################################################################

    # 선정 LED n단계 다운
    print("SENSOR[%s] LED[%s] DOWN %s->%s [%s STEP]" % (
        (max_sensor + 1), control_led_idx, led_control_lux[led_state[control_led_idx]],
        led_control_lux[led_state[control_led_idx] - control_step], control_step))
    led_state[control_led_idx] -= control_step
    control_led(control_led_idx, led_state[control_led_idx])

    return control_led_idx


def led_up(min_sensor, influence_rank, influence_value, control_step=1):
    # 제어할 LED 선정
    # 잠금 및 제어가능 점검
    control_led_idx, control_led_rank = select_control_led(min_sensor, influence_rank, True)
    if (control_led_idx == -1):
        print("Can't Control LED near by %s Sensor." % (min_sensor + 1))
        return -1
    # 유사한 영향도를 가진 조명의 제어 상태 비교
    control_led_idx, control_led_rank = find_similar_influence(min_sensor, control_led_rank, influence_rank,
                                                               influence_value, True)

    ################################0.6################################
    if (led_state[control_led_idx] + control_step >= len(led_control)):
        print("CHANGE CONTROL STEP [%s] -> [%s] (CAUSE : %s LED STATE = %s" % (
            control_step, len(led_control) - led_state[control_led_idx] - 1, control_led_idx,
            led_state[control_led_idx]))
        control_step = len(led_control) - led_state[control_led_idx] - 1
    ###################################################################

    # 선정 LED 한단계 상승
    print("SENSOR[%s] LED[%s] UP %s->%s [%s STEP]" % (
        (min_sensor + 1), control_led_idx, led_control_lux[led_state[control_led_idx]],
        led_control_lux[led_state[control_led_idx] + control_step], control_step))
    led_state[control_led_idx] += control_step
    control_led(control_led_idx, led_state[control_led_idx])

    return control_led_idx


def select_control_led(sensor, influence_rank, isLow):
    # 높힐 LED 선정 (잠금 X, 제어 상태 최고 X) 영향도가 해당 센서에 가장 높은 조명 중 총영향도가 높은순서 or
    # 낮출 LED 선정 (잠금 X, 제어 상태 최저 X) 영향도가 해당 센서에 가장 높은 조명 중 총영향도가 높은순서
    for i in range(0, len(influence_rank[sensor])):
        if (isLow) & (led_state[influence_rank[sensor][i]] != len(led_control) - 1) & (
                led_up_lock[influence_rank[sensor][i]] == 0):
            control_led_idx = influence_rank[sensor][i]
            control_led_rank = i
            print("SELECT UP LED NUM : %s" % control_led_idx)
            break
        elif (not isLow) & (led_state[influence_rank[sensor][i]] != 1) & (
                led_down_lock[influence_rank[sensor][i]] == 0):
            control_led_idx = influence_rank[sensor][i]
            control_led_rank = i
            print("SELECT DOWN LED NUM : %s" % control_led_idx)
            break
        else:
            print("%s is Locked LED." % influence_rank[sensor][i])

        # 만약 해당 센서에 모든 조명이 제어가 불가능하다면 센서잠금.
        if (i == len(influence_rank[sensor]) - 1):
            if isLow:
                print("Sensor Up Lock")
                sensor_up_lock[sensor] = 1
                sensor_up_lock_cnt[0] += 1
            else:
                print("Sensor Down Lock")
                sensor_down_lock[sensor] = 1
                sensor_down_lock_cnt[0] += 1

            return -1, -1

    return control_led_idx, control_led_rank


# 만약 유사한 영향도를 가진 조명이 존재한다면 해당 조명과 제어상태를 비교하여 높은 조명을 우선적으로 다운
# 수정 사항 : 잠금 검사가 존재 하지 않아서 잠금검사 실시
def find_similar_influence(sensor, now_rank, influence_rank, influence_value, isLow):
    control_led_idx = influence_rank[sensor][now_rank]
    control_led_rank = now_rank

    for j in range(control_led_rank + 1, len(influence_rank[sensor])):
        if (influence_value[sensor][control_led_rank] - similar_led_range <=
            influence_value[sensor][j]) & (
                influence_value[sensor][j] <=
                influence_value[sensor][control_led_rank] + similar_led_range):

            if (isLow):
                if (led_state[influence_rank[sensor][control_led_rank]] > led_state[
                    influence_rank[sensor][j]]) & (
                        led_state[influence_rank[sensor][control_led_rank]] < len(led_control) - 1) & (
                        led_up_lock[influence_rank[sensor][j]] == 0):
                    control_led_idx = influence_rank[sensor][j]
                    control_led_rank = j
                    print("CHANGE(SIMILAR) LED NUM : %s" % control_led_idx)
            else:
                if (led_state[influence_rank[sensor][control_led_rank]] < led_state[
                    influence_rank[sensor][j]]) & (
                        led_state[influence_rank[sensor][control_led_rank]] > 1) & (
                        led_down_lock[influence_rank[sensor][j]] == 0):
                    control_led_idx = influence_rank[sensor][j]
                    control_led_rank = j
                    print("CHANGE(SIMILAR) LED NUM : %s" % control_led_idx)

    return control_led_idx, control_led_rank


# led 잠금
def led_locking(led_lock_list, led_lock):
    print("Locking : ", end='')
    for led_num in led_lock_list:
        led_lock[led_num] = 1
        print(led_num, "", end='')
    print()


# [0.2]
# 조도 만족시키기 전 제어상태를 확인하고 총 영향도에 기반한 제어상태로 돌리기
# 1. 총 영향도가 가장 높은 조명으로 제어단계를 전부 변경
# 2. 만약 조명이 최고 수치라 올릴 수 없다면 다음 조명으로 변경. 반복
def led_setting_based_on_influence_sum(isLow):
    return
    print("First Step Setting")
    print_control_lux()

    for j in range(len(sensor_influence_sum_part)):
        target_led_rank = 0
        print("%s Location Sensor Start" % str(j + 1))
        for i in range(1, len(sensor_influence_sum_part[j])):
            while led_state[sensor_influence_sum_part[j][i]] > 1:
                # 높힐거랑 낮출거랑 같으면 멈춤
                if target_led_rank == i:
                    break
                # 제어 해야되는데 최대치면 다음 영향도로 변경
                if led_state[sensor_influence_sum_part[j][target_led_rank]] == len(led_control) - 1:
                    print("Can't Control LED [%s]" % sensor_influence_sum_part[j][target_led_rank])
                    target_led_rank += 1
                    print("Next Control Target LED [%s]" % sensor_influence_sum_part[j][target_led_rank])
                    continue
                print("LED %s [ UP ] : [%s] STEP -> [%s] STEP" % (
                    sensor_influence_sum_part[j][target_led_rank],
                    led_state[sensor_influence_sum_part[j][target_led_rank]],
                    led_state[sensor_influence_sum_part[j][target_led_rank]] + 1))
                print("LED %s [DOWN] : [%s] STEP -> [%s] STEP" % (
                    sensor_influence_sum_part[j][i], led_state[sensor_influence_sum_part[j][i]],
                    led_state[sensor_influence_sum_part[j][i]] - 1))

                led_state[sensor_influence_sum_part[j][target_led_rank]] += 1
                led_state[sensor_influence_sum_part[j][i]] -= 1
                control_led(sensor_influence_sum_part[j][target_led_rank],
                            led_state[sensor_influence_sum_part[j][target_led_rank]])
                control_led(sensor_influence_sum_part[j][i], led_state[sensor_influence_sum_part[j][i]])
    print("Influence Sum Setting Step 1 Finish")
    print_control_lux()

    for i in range(len(sensor_influence_sum_part)):
        print("%s Location Sensor Start" % str(i + 1))
        for j in range(0, len(sensor_influence_sum_part[i])):
            canControl = True
            if (j < len(sensor_influence_sum_part[i]) - 1):
                while canControl:
                    for k in range(j + 1, len(sensor_influence_sum_part[i])):
                        print("Try Control... %s %s" % (j, k))
                        print(
                            "Control Index  %s %s" % (sensor_influence_sum_part[i][j], sensor_influence_sum_part[i][k]))
                        print("influence cmp %s <= %s <= %s" % (
                            str(sensor_influence_value_sum_part[i][j] - similar_led_range),
                            sensor_influence_value_sum_part[i][k],
                            str(sensor_influence_value_sum_part[i][j] + similar_led_range)))
                        print("State cmp %s > %s" % (
                            led_state[sensor_influence_sum_part[i][j]], led_state[sensor_influence_sum_part[i][k]]))
                        if ((sensor_influence_value_sum_part[i][j] - similar_led_range) <=
                            sensor_influence_value_sum_part[i][
                                k]) & (
                                sensor_influence_value_sum_part[i][k] <= (sensor_influence_value_sum_part[i][
                                                                              j] + similar_led_range)) & (
                                led_state[sensor_influence_sum_part[i][j]] > led_state[
                            sensor_influence_sum_part[i][k]]):
                            print("GIVE 1 STEP LED %s[%s] -> LED %s[%s]" % (
                                sensor_influence_sum_part[i][j], led_state[sensor_influence_sum_part[i][j]],
                                sensor_influence_sum_part[i][k], led_state[sensor_influence_sum_part[i][k]]))
                            led_state[sensor_influence_sum_part[i][k]] += 1
                            led_state[sensor_influence_sum_part[i][j]] -= 1
                            control_led(sensor_influence_sum_part[i][k],
                                        led_state[sensor_influence_sum_part[i][k]])
                            control_led(sensor_influence_sum_part[i][j],
                                        led_state[sensor_influence_sum_part[i][j]])
                            break
                        if (k == len(sensor_influence_sum_part[i]) - 1):
                            canControl = False

    print("Influence Sum Setting Step 2 Finish")
    print_control_lux()


def led_control_use_state(led_control, control_state):
    print("LED SETTING...")
    # print(control_state)
    # print(led_control)
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


def reverse_maker(origin, reverse):
    for i in range(len(origin)):
        reverse.append(list())
        for j in range(len(origin[i]) - 1, -1, -1):
            print(i, j)
            reverse[i].append(origin[i][j])


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
# led_state = [0,
#              5, 5, 5, 5, 5, 5,
#              1, 4, 4, 4, 4, 1,
#              1, 1, 3, 3, 1, 1,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1]

# 498에서 시작
# led_state = [0,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22]

# 가상 자연광 교수님 버전 1
# led_state = [0,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1]
# # 가상 자연광 교수님 버전 1-2
# led_state = [0,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22]
# # 가상 자연광 교수님 버전 1-3
# led_state = [0,
#              1, 1, 1, 1, 22, 22,
#              1, 1, 1, 1, 22, 22,
#              1, 1, 1, 1, 22, 22,
#              1, 1, 1, 1, 22, 22,
#              1, 1, 1, 1, 22, 22]
# # 가상 자연광 교수님 버전 1-4
# led_state = [0,
#              22, 22, 1, 1, 1, 1,
#              22, 22, 1, 1, 1, 1,
#              22, 22, 1, 1, 1, 1,
#              22, 22, 1, 1, 1, 1,
#              22, 22, 1, 1, 1, 1]
# # 가상 자연광 교수님 버전 1-5
led_state = [0,
             22, 22, 22, 22, 22, 22,
             22, 22, 22, 22, 1, 1,
             22, 22, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]
# # 가상 자연광 교수님 버전 1-6
led_state = [0,
             22, 22, 22, 22, 22, 22,
             1, 1, 22, 22, 22, 22,
             1, 1, 1, 1, 22, 22,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]
# # 가상 자연광 교수님 버전 1-7
led_state = [0,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 22, 22,
             1, 1, 22, 22, 22, 22,
             22, 22, 22, 22, 22, 22]
led_state_case = [
    [0,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1],
    [0,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230],
    [0,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1],
    [0,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 1, 1,
     230, 230, 230, 230, 230, 230,
     230, 230, 230, 230, 230, 230]]
led_state_case_limit = [160,1000,600,600]
illum_adder = []
# 가상 자연광 교수님 버전 1
# led_state = [0,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1,
#              1, 1, 1, 1, 1, 1]
# # 가상 자연광 교수님 버전 2
# led_state = [0,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22,
#              1, 1, 1, 1, 1, 1,
#              22, 22, 22, 22, 22, 22,
#              22, 22, 22, 22, 22, 22]
# 가상 자연광 교수님 버전 3
# led_state = [0,
#              4, 4, 4, 4, 4, 4,
#              4, 4, 4, 4, 4, 4,
#              4, 1, 1, 1, 1, 4,
#              4, 4, 4, 4, 4, 4,
#              4, 4, 4, 4, 4, 4]

# 테스트용
# led_state = [0,
#              1,1,1,1,1,1,
#              1,10,3,3,11,1,
#              1,1,1,1,1,1,
#              1,10,3,3,12,1,
#              1,1,1,1,1,1]
# 테스트용2
# led_state = [0,
#              1,1,1,1,1,1,
#              1,22,4,5,21,1,
#              1,1,1,1,1,1,
#              1,5,1,1,6,1,
#              1,5,1,1,5,1]

led_state_66_passive = [0,
                        1, 5, 1, 4, 12, 1,
                        2, 8, 3, 1, 1, 1,
                        1, 1, 3, 3, 4, 1,
                        1, 9, 1, 2, 11, 1,
                        1, 3, 1, 6, 1, 1]

led_state = [0,
             1, 4, 1, 2, 5, 1,
             1, 9, 4, 4, 7, 1,
             1, 1, 1, 1, 1, 1,
             1, 9, 3, 3, 8, 2,
             1, 4, 1, 2, 8, 2]
led_max_state = [0,
                 1, 4, 1, 2, 5, 1,
                 1, 9, 4, 4, 7, 1,
                 1, 1, 1, 1, 1, 1,
                 1, 9, 3, 3, 8, 2,
                 1, 4, 1, 2, 8, 2]

led_state_lux=[0,
               24, 51, 24, 28, 104, 24,
               24, 236, 72, 73, 173, 24,
               24, 24, 24, 24, 24, 24,
               24, 230, 68, 66, 170, 24,
               24, 43, 28, 29, 127, 24]
led_state = [0,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1]
illum_add = [100, 200, 200,
             0, 100, 200,
             0, 0, 100]
illum_add = [0, 0, 0,
             0, 0, 0,
             0, 0, 0]


if __name__ == '__main__':
    # receive_thread_udp=threading.Thread(target=udp.udp_receive())
    # receive_thread_udp.start()
    timer_data = pd.DataFrame(columns=['start', 'end', 'diff'])
    start_data_center()

    # influence_maker
    reverse_maker(sensor_influence_sum_all, sersor_influence_sum_all_reverse)
    print(sersor_influence_sum_all_reverse)
    reverse_maker(sensor_influence_value_sum_all, sersor_influence_value_sum_all_reverse)
    print(sersor_influence_value_sum_all_reverse)

    for i in range(1, len(led_state_lux)):
        for j in range(len(led_control_lux)):
            if led_state_lux[i] == led_control_lux[j]:
                led_state[i]=j
    # print(led_state)


    # for i in range(1, len(led_state_case)):
    #     save_folder = str(i + 1)
    #     led_state = led_state_case[i]
    #
    #     start = datetime.now()
    #     print('START :', start)
    #
    #     # init led
    #     led_control_use_state(led_control, led_state_0)
    #
    #     # start
    #     process(start, i)
    #
    #     end = datetime.now()
    #     print('END :', end)
    #     print('걸린시간 :', (end - start))
    #     timer_data.loc[i] = {'start': start, 'end': end, 'diff': (end - start)}

    save_folder=str(0)
    start=datetime.now()
    print('START :',start)
    # init led
    led_control_use_state(led_control, led_state_0)
    # start
    process(start, 0)
    end=datetime.now()
    print('END :',end)
    print('걸린시간 :',(end-start))
    timer_data.loc[0]={'start':start,'end':end,'diff':(end-start)}

    timer_data.to_csv("D:\\BunkerBuster\\Desktop\\shin_excel\\24시작\\new_index\\timer.csv")
    print(timer_data)
    print("timer save")
