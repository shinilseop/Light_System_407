# 조도값 측정, DB에 누적

import numpy as np
# UDP로 받기, 게이트웨이 통해서.

class II:
    _instance = None
    def __init__(self):
        if not II._instance:
            self.intsain_illum = np.zeros(10)
            # self.intsain_illum[9] = -1
            print('__init__ method called but nothing is created')
            # print([self.acs_cct, self.acs_illum])
        else:
            print('instance already created:', self.getInstance())
            # print([self.acs_cct, self.acs_illum])

    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = II()
        return cls._instance

    def set_illum_data(self, i, illum):
        # print(i,"illum 보정 전 :", illum)
        illum = float(illum)
        ## 407호 신조명 Lux 보정식
        # if (i == 0):
        #     illum = (1.040515354 * illum) + 24.17166685
        # elif (i == 1):
        #     illum = (1.025634599 * illum) + 20.86421876
        # elif (i == 2):
        #     illum = (1.056061755 * illum) + 19.72742265
        # elif (i == 3):
        #     illum = (1.045506957 * illum) + 21.4890827
        # elif (i == 4):
        #     illum = (1.058832776 * illum) + 25.42244455
        # elif (i == 5):
        #     illum = (1.006302869 * illum) + 10.89799389
        # elif (i == 6):
        #     illum = (1.040166005 * illum) + 19.38300079
        # elif (i == 7):
        #     illum = (1.014115325 * illum) + 20.70973574
        # elif (i == 8):
        #     illum = (1.058069033 * illum) + 27.1574674

        ## 407호 신조명 Lux 보정식 절편 0
        if (i == 0):
            illum = (1.077570862 * illum)
        elif (i == 1):
            illum = (1.056764014 * illum)
        elif (i == 2):
            illum = (1.086594871 * illum)
        elif (i == 3):
            illum = (1.078442229 * illum)
        elif (i == 4):
            illum = (1.099274822 * illum)
        elif (i == 5):
            illum = (1.022055577 * illum)
        elif (i == 6):
            illum = (1.069537204 * illum)
        elif (i == 7):
            illum = (1.044708393 * illum)
        elif (i == 8):
            illum = (1.101657123 * illum)
        illum=round(illum, 2)
        # print(i,"illum 보정 후 :",illum)
        self.intsain_illum[i] = illum
        # print(intsain_illum[i])

    def get_illum_data(self):
        return self.intsain_illum


