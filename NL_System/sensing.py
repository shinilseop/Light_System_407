# 암막, 자연광 색온도, 실시간, cas, 필요조도, 색온도 재현
import pandas as pd
from MongoDB import Load_MongoDB as LMDB
from NL_System import Base_Process as bp
from Core import Intsain_LED as ILED
import numpy as np
import threading, time
from Core.arduino_color_sensor import acs
from Core.Intsain_Illum import II
from Core.Intsain_Curr import IC

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def load_NL_CCT_mongo():
    step_data = LMDB.load_last1_cct()
    step_df = LMDB.mongodb_to_df(step_data, 'mongo_cas')
    step_df = step_df.reset_index(drop=True)
    return step_df

def process():
    # 싱글톤 데이터 센터 로드.
    acs1 = acs.getInstance()
    II1 = II.getInstance()
    IC1 = IC.getInstance()


    # 센싱부 실행
    base = threading.Thread(target=bp.process)
    base.start()

    while True:
        acs_cct = acs1.get_sensor_data()[0][:10]
        II_illum = II1.get_illum_data()[:10]
        IC_curr = IC1.get_curr_data()[:10]

        data_pd = pd.DataFrame(acs_cct, columns=['cct'])
        for i in range(10):
            data_pd.loc[i, 'illum'] = II_illum[i]
            data_pd.loc[i, 'curr'] = IC_curr[i]
        #
        print("\n\n\t\t측정데이터")
        print(data_pd)
        # 1분주기로 반복.(카스 재측정시간)
        time.sleep(1)



if __name__ == '__main__':
    process()