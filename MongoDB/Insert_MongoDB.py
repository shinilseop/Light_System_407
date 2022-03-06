import pandas as pd
from pymongo import MongoClient
import json
import datetime

def insert_DB(body):

    myclient = MongoClient("mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
    mydb = myclient["Log_base_control_list"]
    mycol = mydb["30LED_Full_Ctrl"]

    mydic = json.loads(body)
    x = mycol.insert_one(mydic)


def insert_DB2(body):
    myclient = MongoClient("mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
    mydb = myclient["Log_base_control_list"]
    mycol = mydb["500lux_ver2"]

    mydic = json.loads(body)
    x = mycol.insert_one(mydic)

def insert_DB_task(body):
    myclient = MongoClient("mongodb://localhost:27018/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
    mydb = myclient["Log_base_control_list"]
    mycol = mydb["task_test"]

    mydic = json.loads(body)
    x = mycol.insert_one(mydic)

def Log_2_Mongo(LED_state, data_pd, result):
    LED_state_json = LED_state.to_json(orient= 'index')
    # print(LED_state_json)
    sensing_json = data_pd.to_json(orient= 'columns')
    # print(sensing_json)
    result_json = result.to_json(orient= 'records')
    # print(result_json)

    # LED_state_str = json.dumps(LED_state_json,indent=4)
    # sensing_str = json.dumps(sensing_json,indent=4)
    result_str = json.dumps(result_json,indent=4)
    result_str = result_str.replace("\\","").replace("[","").replace("]","")
    result_str = result_str[1:len(result_str)-1]
    now = str(datetime.datetime.now()).split(".")[0]
    body = '{"datetime": "' + now + '", "LED_State" : ' + LED_state_json + ', "sensing_data" : ' + sensing_json + ', "result" : ' + result_str + '}'
    # body = '{ "LED_State" : '+LED_state_json+', "sensing_data" : '+sensing_json+', "result" : '+result_str+'}'
    print(body)


    insert_DB(body)
    return 0


def Log_2_Mongo2(LED_state, data_pd, result):
    LED_state_json = LED_state.to_json(orient= 'index')
    # print(LED_state_json)
    sensing_json = data_pd.to_json(orient= 'columns')
    # print(sensing_json)
    result_json = result.to_json(orient= 'records')
    # print(result_json)

    # LED_state_str = json.dumps(LED_state_json,indent=4)
    # sensing_str = json.dumps(sensing_json,indent=4)
    result_str = json.dumps(result_json,indent=4)
    result_str = result_str.replace("\\","").replace("[","").replace("]","")
    result_str = result_str[1:len(result_str)-1]
    now = str(datetime.datetime.now()).split(".")[0]
    body = '{"datetime": "'+ now +'", "LED_State" : '+LED_state_json+', "sensing_data" : '+sensing_json+', "result" : '+result_str+'}'
    print(body)


    insert_DB2(body)
    return 0

def Log_2_Mongo_tasktype(LED_state, data_pd, result,tasktype):
    LED_state_json = LED_state.to_json(orient= 'index')
    # print(LED_state_json)
    sensing_json = data_pd.to_json(orient= 'columns')
    # print(sensing_json)
    result_json = result.to_json(orient= 'records')
    # print(result_json)

    # LED_state_str = json.dumps(LED_state_json,indent=4)
    # sensing_str = json.dumps(sensing_json,indent=4)
    result_str = json.dumps(result_json,indent=4)
    result_str = result_str.replace("\\","").replace("[","").replace("]","")
    result_str = result_str[1:len(result_str)-1]
    now = str(datetime.datetime.now()).split(".")[0]
    body = '{"datetime": "'+ now +'", "task_type": "'+ tasktype +'", "LED_State" : '+LED_state_json+', "sensing_data" : '+sensing_json+', "result" : '+result_str+'}'
    print(body)


    insert_DB_task(body)
    return 0