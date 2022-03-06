# 전력량 측정, DB에 누적
import numpy as np
# UDP로 받기, 게이트웨이 통해서.

class IC:
    _instance = None
    def __init__(self):
        if not IC._instance:
            self.intsain_curr = np.zeros(10)
            print('__init__ method called but nothing is created')
            # print([self.acs_cct, self.acs_illum])
        else:
            print('instance already created:', self.getInstance())
            # print([self.acs_cct, self.acs_illum])

    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = IC()
        return cls._instance

    def set_curr_data(self, i, curr):
        self.intsain_curr[i] = curr
        # print(intsain_curr[i])

    def get_curr_data(self):
        return self.intsain_curr






