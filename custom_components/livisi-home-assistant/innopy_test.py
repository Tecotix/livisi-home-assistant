from innopy.innopy_client import InnopyClient
import pickle
import json
json_token = '{"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkxQajZ1bjFQMFh6blNuYnZXSXgxTHJFemJmUSJ9.eyJjbGllbnRfaWQiOiIyNDYzNTc0OCIsInN1YiI6ImZrcmVicyIsImRldmljZSI6IjkxNDEwMTAxNjgyNCIsImNsaWVudF9wZXJtaXNzaW9ucyI6IkRGRiIsInN0b3JlX2FjY291bnQiOiJma3JlYnNAbnVjbGkuZGUiLCJ0ZW5hbnQiOiJSV0UiLCJ1c2VyX3Blcm1pc3Npb25zIjoiRkZGRkZGRkZGRkZGRkZGRiIsInNlc3Npb24iOiJkZWYyZDUxZGFiNWY0MjE0ODFiNGI5YjVkYjhlZWY1NyIsImlzcyI6IlNtYXJ0SG9tZUFQSSIsImF1ZCI6ImFsbCIsImV4cCI6MTUyNTA5NjU1MywibmJmIjoxNTI0OTIzNzUzfQ.Zx0b807uvR6Bq_q2HVdxz3am_GoV7u6GUebFBBewjyhA0ahWZmRM0K3Yn8LPQQ_I2I0ClZy_PrPCzM5VH_lAD45Gi5bLCpxlDWuq1-vdBfU9DBFQ6VU5yQW_qH1UGb6ccRWfs3GgpneRFbZ2alK2oFRnyx9a9hCnOQ8g4tg3REmXnG_uvktH5qiUmyg4KFwE-rEruUQz9QZhPIx_GNAul5vcqkFbcA8V9A30uYDK7wV5i6W1NsLXCff03uv7NHWLkpSUEgSGOsipYq4_9nRyVTAP-UFpn4ubW_euGU4wREiYLT85IPS-PV--4gSgm_Go6vm0CFB7PX_A4t2oCxgRBA", "token_type": "Bearer", "expires_in": 172800, "refresh_token": "79281c817ebe43c4b862abfb3fceaeb9", "expires_at": 1525096597.1986635}'
import json
token = json.loads(json_token)
innopy = InnopyClient(token)
t = innopy.thermostats
from innopy.innopy_constants import *

#disconnect_evt = '{"Properties": [{"name": "Reason", "value": "SessionExpired"}], "desc": "/desc/event/Disconnect", "timestamp": "2018-05-01T22:10:35.2825559Z", "type": "/event/Disconnect"}'
#from websocket import create_connection

#ws = create_connection(API_URL_EVENTS.replace("{token}",innopy.token["access_token"]))
#innopy._handle_event(disconnect_evt, None)
#innopy.subscribe_events()
import asyncio
#print(innopy._innogy_event_handler)
asyncio.get_event_loop().run_until_complete(innopy._innogy_event_handler())
import time
while True:
    print("loop")
    time.sleep(2)
print()