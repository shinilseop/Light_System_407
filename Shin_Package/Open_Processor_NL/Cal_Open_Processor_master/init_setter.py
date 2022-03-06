import pandas as pd

import Shin_Package.Open_Processor_NL.Cal_Open_Processor_master.datas as datas

def dir_inf_make():
    for i in range(len(datas.dir_inf_temp)):
        datas.dir_inf.append({'ind': {}})
        for key, value in datas.dir_inf_temp[i]['ind'].items():
            led_list = []
            inf_list = []
            result_df = pd.DataFrame()
            for value_2 in datas.dir_inf_temp[i]['ind'][key]:
                # print(value_2)
                # print(inf_df['ind'][i].loc[inf_df['ind'][i]['led']==value_2])
                # print((inf_df['ind'][i].loc[inf_df['ind'][i]['led']==value_2]['led'].tolist()[0]))
                result_df = result_df.append(
                    {'led': datas.inf_df['ind'][i].loc[datas.inf_df['ind'][i]['led'] == value_2]['led'].tolist()[0],
                     'value': datas.inf_df['ind'][i].loc[datas.inf_df['ind'][i]['led'] == value_2]['value'].tolist()[0]},
                    ignore_index=True)
            result_df = result_df.sort_values(by=['value'], axis=0, ascending=False)
            datas.dir_inf[i]['ind'][key] = [int(x) for x in result_df['led'].tolist()]
            datas.dir_inf[i]['ind'][key + '_inf'] = result_df['value'].tolist()
            print(datas.dir_inf_temp[i]['ind'][key])

    return datas.dir_inf


def reverse_maker(origin, reverse):
    for i in range(len(origin)):
        reverse.append(list())
        for j in range(len(origin[i]) - 1, -1, -1):
            # print(i, j)
            reverse[i].append(origin[i][j])