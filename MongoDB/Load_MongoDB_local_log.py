import pandas as pd
from pymongo import MongoClient
from Core import Intsain_LED_rev as ILED
from bson import ObjectId

def load_last1_cct():
    # Requires the PyMongo package.
    # https://api.mongodb.com/python/current

    client = MongoClient('mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')
    filter = {}

    sort = list({
                    '_id': -1
                }.items())

    result = client['Log_base_control_list']['task_test'].find(
        filter=filter,
        sort=sort
    )

    dic_list = []
    dic = dict()
    for i in result:
        dic = i
        dic_list.append(dic)

    return dic_list

def load_cct_id(_id):
    # Requires the PyMongo package.
    # https://api.mongodb.com/python/current

    client = MongoClient('mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')
    filter = {
        '_id': ObjectId(_id)
    }

    sort = list({
                    '_id': -1
                }.items())

    result = client['Log_base_control_list']['task_test'].find(
        filter=filter,
        sort=sort
    )

    dic_list = []
    dic = dict()
    for i in result:
        dic = i
        dic_list.append(dic)

    return dic_list

def load_mongo_task(task_type):
    # Requires the PyMongo package.
    # https://api.mongodb.com/python/current

    client = MongoClient('mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')
    filter = {
        'task_type': task_type
    }

    sort = list({
                    '_id': -1
                }.items())

    result = client['Log_base_control_list']['task_test'].find(
        filter=filter,
        sort=sort
    )

    dic_list = []
    dic = dict()
    for i in result:
        dic = i
        dic_list.append(dic)

    return dic_list


def make_row_key_val(dic):
    # 지하 4층 높이의 dic이 있다고 가정하면 지하 3층에서 지하 4층의 dic[4층 keys]가 str인지 판별하고 맞으면 key와 val을 저장, 아니면 재귀하도록 짜야할듯.

    keyrow = []
    valrow = []
    # 1차 시도시 자가 검진
    if isinstance(dic, str) or isinstance(dic, float) or isinstance(dic, int):
        keyrow.append("1차 키 미확인")
        valrow.append(dic)
        # print([keyrow, valrow])
        return[keyrow, valrow]

    elif isinstance(dic, dict):
        key_list = list(dic.keys())
        key_list = sorted(key_list, key=str.lower)

        for key in key_list:
            if isinstance(dic[key], str) or isinstance(dic[key], int): #or dic[key] is None:
                keyrow.append(key)
                valrow.append(dic[key])
            elif isinstance(dic[key], float):
                keyrow.append(key)
                valrow.append(format(dic[key],"40.20f"))

            else:
                key_val = make_row_key_val(dic[key])
                if isinstance(key_val,list):
                    for temp_key in key_val[0]:
                        keyrow.append(temp_key)
                    for temp_val in key_val[1]:
                        valrow.append(temp_val)

        return [keyrow, valrow]


def mongodb_to_df(dic_list,main_key):
    # main_key = 'LED_State', 'sensing_data', 'result'
    # path = os.getcwd() + '/../' + table + '.csv'
    val_table = []
    df = pd.DataFrame()
    count = 0
    for dic in dic_list:
        val_table = []
        count = count + 1

        data_dic = dic
        # data_dic = dic[main_key]
        key_val = make_row_key_val(data_dic)
        val_table.append(key_val[1])
        keys = key_val[0]

        val_table[0].append(dic['_id'])
        keys.append('_id')

        if count == 1:
            df = pd.DataFrame(val_table, columns=keys)
        else:
            temp_df = pd.DataFrame(val_table, columns=keys)
            # print(count)
            # print(df)
            # print(temp_df)
            df = df.append(temp_df)
    # print(table+"_df load success!")
    return df
def mongodb_to_df_LED(dic_list,main_key,i):
    # main_key = 'LED_State', 'sensing_data', 'result'
    # path = os.getcwd() + '/../' + table + '.csv'
    val_table = []
    df = pd.DataFrame()
    count = 0
    for dic in dic_list:
        val_table = []
        count = count + 1
        data_dic = dic[main_key][str(i)]
        key_val = make_row_key_val(data_dic)
        val_table.append(key_val[1])
        keys = key_val[0]

        val_table[0].append(dic['_id'])
        keys.append('_id')

        if count == 1:
            df = pd.DataFrame(val_table, columns=keys)
        else:
            temp_df = pd.DataFrame(val_table, columns=keys)
            df = df.append(temp_df)
    # print(table+"_df load success!")
    # print(df)
    return df

if __name__ == '__main__':
    task_type = "step_1_diff_cal_illum_newLED"
    step_data = load_mongo_task(task_type)
    step_df = mongodb_to_df(step_data,'result')
    step_df = step_df.reset_index(drop=True)
    # print(step_df['avg_cct'])
    step_df.to_csv('./log_'+task_type+'.csv')

def process(main_key):
    # step_data = load_last1_cct()

    task_type = "step_1_diff_cal_illum_newLED"
    step_data = load_mongo_task(task_type)
    step_df = mongodb_to_df(step_data, main_key)
    step_df = step_df.reset_index(drop=True)
    return step_df

def update_state_illum(ch, updown):
    if ch == 0:
        return 0
    else:
        re = ch + updown
        if re < 0:
            return 0
        else:
            return re

def get_LED_state(main_key,_id,control_index,nonfirst):
    step_data = load_cct_id(_id)

    for i in range(30):
        temp = mongodb_to_df_LED(step_data, main_key,i)
        # 이거 자체에 딜레이가 많이 먹음.

        temp = temp.reset_index(drop=True)

        ch1 = int(float(temp.loc[0,'ch1'].replace(" ", "")))
        ch2 = int(float(temp.loc[0,'ch2'].replace(" ", "")))
        ch3 = int(float(temp.loc[0,'ch3'].replace(" ", "")))
        ch4 = int(float(temp.loc[0,'ch4'].replace(" ", "")))

        if nonfirst is False:
            temp_index = ch1 + ch2 + ch3 + ch4
            cut1 = int((control_index[i] - temp_index) * (ch1 / temp_index))
            cut2 = int((control_index[i] - temp_index) * (ch2 / temp_index))
            cut3 = int((control_index[i] - temp_index) * (ch3 / temp_index))
            cut4 = int((control_index[i] - temp_index) * (ch4 / temp_index))

            ch1 = update_state_illum(ch1, cut1)
            ch2 = update_state_illum(ch2, cut2)
            ch3 = update_state_illum(ch3, cut3)
            ch4 = update_state_illum(ch4, cut4)
        # print(i+1,ch1, ch2, ch3, ch4)
        ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)
    return 0


def get_LED_state2(main_key,_id,control_index):
    step_data = load_cct_id(_id)

    for i in range(30):
        temp = mongodb_to_df_LED(step_data, main_key,i)
        # 이거 자체에 딜레이가 많이 먹음.

        temp = temp.reset_index(drop=True)

        ch1 = int(float(temp.loc[0,'ch1'].replace(" ", "")))
        ch2 = int(float(temp.loc[0,'ch2'].replace(" ", "")))
        ch3 = int(float(temp.loc[0,'ch3'].replace(" ", "")))
        ch4 = int(float(temp.loc[0,'ch4'].replace(" ", "")))


        temp_index = ch1 + ch2 + ch3 + ch4
        cut1 = int((control_index[i] - temp_index) * (ch1 / temp_index))
        cut2 = int((control_index[i] - temp_index) * (ch2 / temp_index))
        cut3 = int((control_index[i] - temp_index) * (ch3 / temp_index))
        cut4 = int((control_index[i] - temp_index) * (ch4 / temp_index))

        ch1 = update_state_illum(ch1, cut1)
        ch2 = update_state_illum(ch2, cut2)
        ch3 = update_state_illum(ch3, cut3)
        ch4 = update_state_illum(ch4, cut4)


        # print(i+1,ch1, ch2, ch3, ch4)
        ILED.set_LED(i + 1, ch1, ch2, ch3, ch4)
    return 0

