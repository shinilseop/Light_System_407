import pandas as pd
from pymongo import MongoClient

def load_last1_cct():
    client = MongoClient('mongodb://210.102.142.14:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')
    filter = {
    }
    project = {
        'datetime': 1,
        'data.results.CCT': 1,
        'data.results.Photometric': 1

    }
    sort = list({
                    'datetime': -1
                }.items())
    limit = 1

    result = client['nl_witlab']['cas'].find(
        filter=filter,
        projection=project,
        sort=sort,
        limit=limit
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
            if isinstance(dic[key], str) or isinstance(dic[key], int):
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


def mongodb_to_df(dic_list, table):
    if table == 'mongo_cas':
        main_key = 'data'
    elif table == 'mongo_cas_ird':
        main_key = 'sp_ird'

    # path = os.getcwd() + '/../' + table + '.csv'
    val_table = []
    df = pd.DataFrame()
    count = 0
    for dic in dic_list:
        val_table = []
        count = count + 1

        data_dic = dic[main_key]
        key_val = make_row_key_val(data_dic)
        val_table.append(key_val[1])
        keys = key_val[0]

        val_table[0].append(dic['datetime'])
        keys.append('datetime')

        if count == 1:
            df = pd.DataFrame(val_table, columns=keys)
        else:
            temp_df = pd.DataFrame(val_table, columns=keys)
            df = df.append(temp_df)
    # print(table+"_df load success!")
    return df