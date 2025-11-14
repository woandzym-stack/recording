import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Agora配置
    AGORA_APP_ID = os.getenv('AGORA_APP_ID', 'your_agora_app_id')
    AGORA_APP_CERTIFICATE = os.getenv('AGORA_APP_CERTIFICATE', 'your_agora_app_certificate')
    CUSTOMER_ID = os.getenv('CUSTOMER_ID', 'your_customer_id')
    CUSTOMER_CERTIFICATE = os.getenv('CUSTOMER_CERTIFICATE', 'your_customer_certificate')
    
    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', 'your_oss_access_key_id')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', 'your_oss_access_key_secret')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'your_bucket_name')
    
    # 服务器配置
    SERVER_BASE_URL = os.getenv('SERVER_BASE_URL', 'http://localhost:5000')