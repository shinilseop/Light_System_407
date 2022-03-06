import uvicorn
from API import API_Server_sec as api
if __name__ == '__main__':

    uvicorn.run(api, host="192.168.100.100" ,port=80)
