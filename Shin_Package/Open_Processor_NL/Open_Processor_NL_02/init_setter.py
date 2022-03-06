import pandas as pd
import numpy as np

import Shin_Package.Open_Processor_NL.Open_Processor_NL_02.datas as datas

def dir_inf_make():
    for i in range(len(datas.sensor_influence_all)):
        datas.inf_df['ind'].append(
            pd.DataFrame([x for x in zip(datas.sensor_influence_all[i], datas.sensor_influence_value_all[i])],
                         columns=['led', 'value']))
        datas.inf_df['ind'][i] = datas.inf_df['ind'][i].sort_values(by=['value'], axis=0, ascending=False)

    print('dir 영향도 제작중...')
    for i in range(len(datas.dir_inf_temp)):
        datas.dir_inf.append({'ind': {}})
        for key, value in datas.dir_inf_temp[i]['ind'].items():
            led_list = []
            inf_list = []
            result_df = pd.DataFrame()
            for value_2 in datas.dir_inf_temp[i]['ind'][key]:
                result_df = result_df.append(
                    {'led': datas.inf_df['ind'][i].loc[datas.inf_df['ind'][i]['led'] == value_2]['led'].tolist()[0],
                     'value': datas.inf_df['ind'][i].loc[datas.inf_df['ind'][i]['led'] == value_2]['value'].tolist()[0]},
                    ignore_index=True)
            result_df = result_df.sort_values(by=['value'], axis=0, ascending=False)
            datas.dir_inf[i]['ind'][key] = [int(x) for x in result_df['led'].tolist()]
            datas.dir_inf[i]['ind'][key + '_inf'] = result_df['value'].tolist()
            # print(result_df)
            # print(datas.dir_inf_temp[i]['ind'][key])

    print('dir 영향도 제작완료!')
    return datas.dir_inf


def reverse_maker(origin, reverse):
    print('reverse maker ...')
    for i in range(len(origin)):
        reverse.append(list())
        for j in range(len(origin[i]) - 1, -1, -1):
            # print(i, j)
            reverse[i].append(origin[i][j])
    print('reverse maker !')

def sensor_influence_individual_make():
    print('individual 영향도 제작중...')
    # datas.sensor_influence_threshold
    # datas.sensor_influence_all
    # datas.sensor_influence_value_all
    for i in range(9):
        led_list = []
        influ_list = []
        for j in range(1, len(datas.led_influ)):
            # print(i,j)
            if datas.led_influ[j][i] > datas.sensor_influence_threshold:
                led_list.append(j)
                influ_list.append(round(datas.led_influ[j][i]*100, 2))
        sorted_index = np.argsort(influ_list)[::-1]
        led_list = [led_list[idx] for idx in sorted_index]
        influ_list = [influ_list[idx] for idx in sorted_index]
        # print('sorted ',sorted_index)
        # print('='*15,(i+1),len(led_list),'='*15)
        # print(led_list)
        # print(influ_list)

        ### 예외 처리 P6 지점에 대해 29, 30번 조명이 15.5% 이상의 영향도를 가지고 있어서 제외해야함. boundary 판별에 들어가면 안됨.
        if(i==5):
            remove_idx = np.argwhere((np.array(led_list)==29)|(np.array(led_list)==30)).reshape(-1)[::-1]
            # print(remove_idx)
            for idx in remove_idx:
                del led_list[idx]
                del influ_list[idx]
            # print('remove idx')
            # print(led_list)
            # print(influ_list)

        datas.sensor_influence_all.append(led_list)
        datas.sensor_influence_value_all.append(influ_list)
    print('individual 영향도 제작완료!')

def sensor_influence_sum_make():
    print('sum 영향도 제작중...')
    # sensor_influence_sum_part
    # sensor_influence_sum_value_part
    # sensor_influence_sum_part_reverse
    # sensor_influence_sum_part_value_reverse
    led_sum_influ = [0]
    for i in range(1, 31):
        influ_sum = 0
        for j in range(len(datas.led_influ[i])):
            # print(i, j)
            # print(datas.led_influ[i][j])
            influ_sum += datas.led_influ[i][j]
        led_sum_influ.append(influ_sum)
    # print(led_sum_influ)
    # print(len(led_sum_influ))

    for i in range(9):
        led_list = []
        influ_list = []
        for j in range(1, len(datas.led_influ)):
            if (3<=i)&(i<=5):
                if (datas.led_influ[j][i] > datas.sensor_sum_middle_threshold):
                    led_list.append(j)
                    influ_list.append(round(led_sum_influ[j]*100, 2))
            else:
                if datas.led_influ[j][i] > datas.sensor_sum_other_threshold:
                    led_list.append(j)
                    influ_list.append(round(led_sum_influ[j]*100, 2))

        sorted_index = np.argsort(influ_list)
        led_list = [led_list[idx] for idx in sorted_index]
        influ_list = [influ_list[idx] for idx in sorted_index]
        datas.sensor_influence_sum_part_reverse.append(led_list)
        datas.sensor_influence_sum_value_part_reverse.append(influ_list)


        sorted_index = np.argsort(influ_list)[::-1]
        led_list = [led_list[idx] for idx in sorted_index]
        influ_list = [influ_list[idx] for idx in sorted_index]
        datas.sensor_influence_sum_part.append(led_list)
        datas.sensor_influence_sum_value_part.append(influ_list)

    print('sum 영향도 제작완료!')
    # print(datas.sensor_influence_sum_part_reverse)
    # print(datas.sensor_influence_sum_value_part_reverse)
    # print(datas.sensor_influence_sum_part)
    # print(datas.sensor_influence_sum_value_part)

if __name__=='__main__':
    sensor_influence_individual_make()
    sensor_influence_sum_make()
    dir_inf_make()
