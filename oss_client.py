import oss2
from config import Config
import uuid
import os

class OSSClient:
    def __init__(self):
        self.auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)
    
    def upload_file(self, file_path, object_name=None):
        """上传文件到OSS"""
        if not object_name:
            object_name = f"recordings/{uuid.uuid4()}_{os.path.basename(file_path)}"
        
        try:
            result = self.bucket.put_object_from_file(object_name, file_path)
            if result.status == 200:
                return {
                    "success": True,
                    "object_name": object_name,
                    "url": f"https://{Config.OSS_BUCKET_NAME}.{Config.OSS_ENDPOINT.replace('https://', '')}/{object_name}"
                }
            else:
                return {"success": False, "error": "Upload failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_presigned_url(self, object_name, expiration=3600):
        """生成预签名URL"""
        try:
            url = self.bucket.sign_url('GET', object_name, expiration)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_file(self, object_name, local_path):
        """下载文件"""
        try:
            self.bucket.get_object_to_file(object_name, local_path)
            return {"success": True, "local_path": local_path}
        except Exception as e:
            return {"success": False, "error": str(e)}