import pandas as pd

def process():
    ori_path = "Z:\\0. 연구원 자료\\가덕현_자료\\407호\\보정실험\\20210820\\"

    log_df = pd.read_csv(ori_path+"cct_2.csv")
    # illum_df = pd.read_csv(ori_path+"illum.csv")
    cct_df = pd.read_csv(ori_path+"jaz.csv")
    # log_df['datetime'] = pd.to_datetime(log_df['datetime'])

    log_df['jaz_cct'] = log_df.apply(lambda x: 0, axis=1)
    # log_df['jaz_illum'] = log_df.apply(lambda x: 0, axis=1)

    for i in range(len(log_df)):
        flag_time = float(log_df.loc[i,"datetime"])
        for j in range(len(cct_df)-1):
            cct_time_1 = float(cct_df.loc[j, "datetime"])
            cct_time_2 = float(cct_df.loc[j+1, "datetime"])
            if cct_time_1<=flag_time:
                if flag_time <cct_time_2:
                    log_df.loc[i, "jaz_cct"] = cct_df.loc[j, "CCT"]
                    print("색온도",i)
                    break

        # for j in range(len(illum_df)-1):
        #     illum_time_1 = float(illum_df.loc[j, "Timestamp"])
        #     illum_time_2 = float(illum_df.loc[j+1, "Timestamp"])
        #     if illum_time_1<flag_time:
        #         if flag_time <illum_time_2:
        #             log_df.loc[i, "jaz_illum"] = illum_df.loc[j, "illum"]
        #             print("조도",i)
        #             break

    log_df.to_csv(ori_path+"marge.csv")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
from string import ascii_uppercase


# import my data
def process2():
    ori_path = "Z:\\0. 연구원 자료\\가덕현_자료\\407호\\보정실험\\20210820\\"
    df = pd.read_csv(ori_path + "marge.csv")

    xdata = df["cct_" + str(2)]
    ydata = df["jaz_cct"]

    # define polynomial function
    def func(X, A, B):
        # unpacking the multi-dim. array column-wise, that's why the transpose
        x = X
        return (A * x) + B

    # fit the polynomial function to the 3d data
    popt, _ = curve_fit(func, xdata, ydata)

    # print coefficients of the polynomial function, i.e., A, B, C, D, E and F
    print(str(2) + "번 센서 보정식 : ")
    for a, b in zip(popt, ascii_uppercase):
        print(f"{b} = {a:.10f}")

    # for i in range(1,10):
    #     temp = df[df['task_type']=="diff_test_point_"+str(i)]
    #     temp = temp[["task_type","cct_"+str(i), "jaz"]]
    #     temp.to_csv("diff_test_point_"+str(i)+".csv")
    #
    #
    #     xdata = temp["cct_"+str(i)]
    #     ydata = temp["jaz_cct"]
    #
    #     # define polynomial function
    #     def func(X, A, B):
    #         # unpacking the multi-dim. array column-wise, that's why the transpose
    #         x = X
    #         return (A * x) + B
    #     # fit the polynomial function to the 3d data
    #     popt, _ = curve_fit(func, xdata, ydata)
    #
    #     # print coefficients of the polynomial function, i.e., A, B, C, D, E and F
    #     print(str(i)+"번 센서 보정식 : ")
    #     for a, b in zip(popt, ascii_uppercase):
    #         print(f"{b} = {a:.10f}")


def process3():
    jaz_cct = pd.read_csv("Z:\\0. 연구원 자료\\가덕현_자료\\407호\\보정실험\\20210820\\jaz_cct.csv")
    jaz_cct['datetime'] = pd.to_datetime(jaz_cct['datetime'])
    jaz_cct.to_csv("Z:\\0. 연구원 자료\\가덕현_자료\\407호\\보정실험\\20210820\\jaz.csv")

if __name__ == '__main__':
    # process()
    process2()
    # process3()
