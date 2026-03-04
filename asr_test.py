import json
import _thread as thread

import websocket
import hashlib
import hmac
import base64
from datetime import datetime

from websocket import WebSocketApp

CONFIG = {
    # 请求地址
    'hostUrl': "wss://iat-api.xfyun.cn/v2/iat",
    'host': "iat-api.xfyun.cn",

    'appid': "********",
    'apiSecret': "********************************",
    'apiKey': "********************************",

    'file': "./16k_10.pcm",  # 请填写您的音频文件路径
    'uri': "/v2/iat",
    'highWaterMark': 1280
}

STATUS_FIRST_FRAME = "STATUS_FIRST_FRAME"
STATUS_CONTINUE_FRAME = "STATUS_CONTINUE_FRAME"
STATUS_LAST_FRAME = "STATUS_LAST_FRAME"
FRAME = {
    "STATUS_FIRST_FRAME": 0,
    "STATUS_CONTINUE_FRAME": 1,
    "STATUS_LAST_FRAME": 2
}

# 获取当前时间 RFC1123格式
date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
status = FRAME[STATUS_FIRST_FRAME]
# 记录本次识别用sid
currentSid = ""
iatResult = []


def getAuthStr(date, config):
    signature_origin = f"host: {config['host']}\ndate: {date}\nGET {config['uri']} HTTP/1.1"
    signature_sha = hmac.new(config['apiSecret'].encode(), signature_origin.encode(), hashlib.sha256)
    signature = base64.b64encode(signature_sha.digest()).decode()
    authorization_origin = f'api_key="{config["apiKey"]}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    auth_str = base64.b64encode(authorization_origin.encode()).decode()
    return auth_str


def send(data, config, ws):
    frame = ""
    global status
    frame_data_section = {
        "status": status,
        "format": "audio/L16;rate=16000",
        "audio": data,
        "encoding": "raw"
    }

    if status == FRAME[STATUS_FIRST_FRAME]:
        frame = {
            "common": {
                "app_id": config["appid"]
            },
            "business": {
                "language": "zh_cn",
                "domain": "iat",
                "accent": "mandarin",
                "dwa": "wpgs"  # 可选参数，动态修正
            },
            "data": frame_data_section
        }
        status = FRAME[STATUS_CONTINUE_FRAME]
    elif status == FRAME[STATUS_CONTINUE_FRAME] or status == FRAME[STATUS_LAST_FRAME]:
        frame = {
            "data": frame_data_section
        }

    ws.send(json.dumps(frame))


wssURL = CONFIG['hostUrl'] + "?authorization=" + getAuthStr(date, CONFIG) + "&date=" + date + "&host=" + CONFIG['host']


class Test(object):
    def __init__(self):
        super(Test, self).__init__()
        self.url = "ws://echo.websocket.org/"
        self.ws = None

    def on_open(self):
        print("####### on_open #######")
        print("websocket connect!")

    def on_message(self, message):
        print("####### on_message #######")
        print("message：%s" % message)

    def on_error(self, error):
        print("####### on_error #######")
        print("error：%s" % error)

    def on_close(self):
        print("####### on_close #######")

    def send(self, data):
        send(data, CONFIG, self.ws)

    def start(self):
        websocket.enableTrace(True)  # 开启运行状态追踪。debug 的时候最好打开他，便于追踪定位问题。

        self.ws = WebSocketApp(self.url,
                               on_open=self.on_open,
                               on_message=self.on_message,
                               on_error=self.on_error,
                               on_close=self.on_close)
        # self.ws.on_open = self.on_open  # 也可以先创建对象再这样指定回调函数。run_forever 之前指定回调函数即可。

        self.ws.run_forever()
