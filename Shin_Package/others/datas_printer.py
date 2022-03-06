import pandas as pd

path = 'D:\\BunkerBuster\\Desktop\\shin_excel\\신조명 관련'

influ_df = pd.read_csv(f'{path}\\led_influ.csv')
print(influ_df)

col_list = influ_df.columns
for i in range(len(influ_df)):
    print('[', end='')
    for col in col_list:
        if col==col_list[len(col_list)-1]:
            print('%s],'%influ_df[col][i], end='')
        else:
            print('%s, ' % influ_df[col][i], end='')
    print()