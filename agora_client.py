import requests
import json
import time
from config import Config
import base64

class AgoraClient:
    def __init__(self):
        self.app_id = Config.AGORA_APP_ID
        self.app_certificate = Config.AGORA_APP_CERTIFICATE
        self.customer_id = Config.CUSTOMER_ID
        self.customer_certificate = Config.CUSTOMER_CERTIFICATE
        self.base_url = "https://api.agora.io/v1/apps"
        
    def get_headers(self):
        """获取认证头部"""
        credentials = f"{self.app_id}:{self.app_certificate}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        }
    
    def _generate_auth_header(self):
        """生成HTTP基本认证头[citation:6]"""
        credentials = f"{self.customer_id}:{self.customer_certificate}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Content-Type": "application/json","Authorization": f"Basic {encoded_credentials}"}

    def acquire_recording_resource(self, channel_name, uid="100"):
        """获取录制资源"""
        url = f"{self.base_url}/{self.app_id}/cloud_recording/acquire"
        
        payload = {
            "cname": channel_name,
            "uid": uid,
            "clientRequest": {
                "resourceExpiredHour": 24,
                "scene": 0
            }
        }
        
        response = requests.post(url, headers=self._generate_auth_header(), json=payload)
        return response.json()
    
    def start_recording(self, resource_id, channel_name, uid, token):  
        access_key = Config.OSS_ACCESS_KEY_ID
        secret_key = Config.OSS_ACCESS_KEY_SECRET
        bucket = Config.OSS_BUCKET_NAME

        # 阿里云OSS存储配置
        storage_config = {
            "vendor": 2,  # 阿里云
            "region": 7,  # 香港
            "bucket": bucket,  # 替换为实际bucket
            "accessKey": access_key,  # 替换为实际access key
            "secretKey": secret_key   # 替换为实际secret key
        }

        """开始录制"""
        url = f"{self.base_url}/{self.app_id}/cloud_recording/resourceid/{resource_id}/mode/mix/start"
        
        payload = {
            "cname": channel_name,
            "uid": str(uid),
            "clientRequest": {
                "token": token,
                "recordingConfig": {
                        "channelType": 0,  # 通信模式
                        "streamTypes": 2,  # 录制音频
                        "audioProfile": 1,  # 标准音质
                        "maxIdleTime": 30,  # 最大空闲时间
                        "transcodingConfig": {
                          "height": 640,
                          "width": 360,
                          "bitrate": 500,
                          "fps": 15,
                          "mixedVideoLayout": 1,
                          "backgroundColor": "#FF0000"
                        },
                    },
                     "recordingFileConfig": {
                      "avFileType": [
                        "hls",
                        "mp4"
                      ]
                    },
                "storageConfig": storage_config
            }
        }
        
        response = requests.post(url, headers=self._generate_auth_header(), json=payload)
        return response.json()
    
    def stop_recording(self, resource_id, sid, channel_name, uid):
        """停止录制"""
        url = f"{self.base_url}/{self.app_id}/cloud_recording/resourceid/{resource_id}/sid/{sid}/mode/mix/stop"
        
        payload = {
            "cname": channel_name,
            "uid": uid,
            "clientRequest": {}
        }
        
        response = requests.post(url, headers=self._generate_auth_header(), json=payload)
        return response.json()
    
    def query_recording(self, resource_id, sid):
        """查询录制状态"""
        url = f"{self.base_url}/{self.app_id}/cloud_recording/resourceid/{resource_id}/sid/{sid}/mode/mix/query"
        
        response = requests.get(url, headers=self._generate_auth_header())
        return response.json()