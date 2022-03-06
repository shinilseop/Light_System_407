# 색온도 센서 데이터 받고 API로도 보내고
import numpy as np
# rest 프로토콜 사용

class acs:
    _instance = None
    def __init__(self):
        if not acs._instance:
            self.acs_cct = np.zeros(10)
            self.acs_illum = np.zeros(10)
            print('__init__ method called but nothing is created')
            # print([self.acs_cct, self.acs_illum])
        else:
            print('instance already created:', self.getInstance())
            # print([self.acs_cct, self.acs_illum])

    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = acs()
        return cls._instance


    def set_sensor_data(self, num, illum, cct):
        # global acs_cct
        # global acs_iluum

        self.acs_cct[num - 1] = cct
        self.acs_illum[num - 1] = illum
        # for i in range(1, 10):
        #     print(i, self.acs_cct[i - 1], self.acs_illum[i - 1])

    def get_sensor_data(self):
        # global acs_cct
        # global acs_iluum
        # for i in range(1, 10):
        #     print(i, self.acs_cct[i - 1], self.acs_illum[i - 1])
        return [self.acs_cct, self.acs_illum]