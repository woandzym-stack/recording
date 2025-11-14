from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import time
import os
from agora_client import AgoraClient
from oss_client import OSSClient
import uuid
from flask import send_from_directory
from config import Config
from rtc_token.RtcTokenBuilder2 import *

app = Flask(__name__)
CORS(app)

# 内存存储（生产环境请使用数据库）
rooms = {}
recordings = {}
agora_client = AgoraClient()
oss_client = OSSClient()


@app.route('/')
def serve_frontend():
    return send_file('static/index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/v1/rooms', methods=['POST'])
def create_room():
    """创建房间"""
    data = request.json
    room_name = data.get('roomName', 'default_room')
    
    room_id = str(uuid.uuid4())
    rooms[room_id] = {
        'id': room_id,
        'name': room_name,
        'created_at': time.time(),
        'members': [],
        'is_recording': False
    }
    
    return jsonify({
        'success': True,
        'roomId': room_id,
        'roomName': room_name
    })

@app.route('/api/v1/rooms/<room_id>/join', methods=['POST'])
def join_room(room_id):
    """加入房间"""

    if room_id not in rooms:
        return jsonify({'success': False, 'error': 'Room not found'}), 404
    
    data = request.json
    user_id = data.get('userId', str(uuid.uuid4()))
    user_name = data.get('userName', 'Anonymous')
    
    user_info = {
        'userId': user_id,
        'userName': user_name,
        'joinedAt': time.time()
    }
    
    rooms[room_id]['members'].append(user_info)

    #获取room_id对应的room_name
    room_name = rooms[room_id]['name']
    
    return jsonify({
        'success': True,
        'roomId': room_id,
        'user': user_info,
        'token': generate_agora_token(room_name, user_id)  # 实际使用时需要生成Agora token
    })

@app.route('/api/v1/rooms/<room_id>/record/start', methods=['POST'])
def start_recording(room_id):
    """开始录制"""
    if room_id not in rooms:
        return jsonify({'success': False, 'error': 'Room not found'}), 404
    
    if rooms[room_id]['is_recording']:
        return jsonify({'success': False, 'error': 'Recording already started'}), 400
    
    #获取roomName
    room_name = rooms[room_id]['name']

    
    
    # 获取录制资源
    acquire_result = agora_client.acquire_recording_resource(room_name)
    if 'resourceId' not in acquire_result:
        return jsonify({'success': False, 'error': 'Failed to acquire recording resource'}), 500
    
    resource_id = acquire_result['resourceId']
    token = generate_agora_token(room_name, "100")
    
    # 开始录制
    start_result = agora_client.start_recording(
        resource_id=resource_id,
        channel_name=room_name,
        uid="100",  # 录制服务UID
        token=token
    )
    
    if 'sid' not in start_result:
        return jsonify({'success': False, 'error': 'Failed to start recording'}), 500
    
    sid = start_result['sid']
    recording_id = str(uuid.uuid4())
    
    recordings[recording_id] = {
        'id': recording_id,
        'roomId': room_id,
        'resourceId': resource_id,
        'sid': sid,
        'startedAt': time.time(),
        'status': 'recording',
        'fileList': []
    }
    
    rooms[room_id]['is_recording'] = True
    rooms[room_id]['currentRecording'] = recording_id
    
    return jsonify({
        'success': True,
        'recordingId': recording_id,
        'resourceId': resource_id,
        'sid': sid
    })

@app.route('/api/v1/rooms/<room_id>/record/stop', methods=['POST'])
def stop_recording(room_id):
    """停止录制"""
    if room_id not in rooms:
        return jsonify({'success': False, 'error': 'Room not found'}), 404
    
    if not rooms[room_id]['is_recording']:
        return jsonify({'success': False, 'error': 'No active recording'}), 400
    
    recording_id = rooms[room_id]['currentRecording']
    recording = recordings[recording_id]

    #获取room_name
    room_name = rooms[room_id]['name']
    
    stop_result = agora_client.stop_recording(
        resource_id=recording['resourceId'],
        sid=recording['sid'],
        channel_name=room_name,
        uid="100"
    )
    
    if stop_result.get('code') is not None:
        return jsonify({'success': False, 'error': 'Failed to stop recording'}), 500
    
    # 更新录制状态
    recording['status'] = 'stopped'
    recording['stoppedAt'] = time.time()


    mp4_files = list(filter(
      lambda file: file.get('fileName', '').endswith('.mp4'),
      stop_result.get('serverResponse', {}).get('fileList', [])
    ))

    
    recording['fileList'] = mp4_files

    # recording['fileList'] = stop_result.get('serverResponse', {}).get('fileList', [])
    
    rooms[room_id]['is_recording'] = False
    # del rooms[room_id]['currentRecording']
    
    return jsonify({
        'success': True,
        'recordingId': recording_id,
        'fileList': recording['fileList']
    })

@app.route('/api/v1/recordings/<recording_id>', methods=['GET'])
def get_recording(recording_id):
    """获取录制文件"""
    if recording_id not in recordings:
        return jsonify({'success': False, 'error': 'Recording not found'}), 404
    
    recording = recordings[recording_id]

    # 这里应该从OSS获取文件URL
    # 假设fileList中包含了OSS的文件信息
    file_urls = []
    for file_info in recording.get('fileList', []):
        # 生成预签名URL
        presigned_url = oss_client.generate_presigned_url(file_info.get('fileName'))
        if presigned_url['success']:
            file_urls.append({
                'filename': file_info.get('filename'),
                'url': presigned_url['url']
            })
    return jsonify({
        'success': True,
        'recording': recording,
        'files': file_urls
    })

@app.route('/api/v1/rooms', methods=['GET'])
def list_rooms():
    """获取房间列表"""
    return jsonify({
        'success': True,
        'rooms': list(rooms.values())
    })

@app.route('/api/v1/recordings', methods=['GET'])
def list_recordings():
    """获取录制列表"""
    return jsonify({
        'success': True,
        'recordings': list(recordings.values())
    })

def generate_agora_token(channel_name, uid):
    
    app_id = Config.AGORA_APP_ID
    app_certificate = Config.AGORA_APP_CERTIFICATE

    # Token 的有效时间，单位秒
    token_expiration_in_seconds = 3600
    # 所有的权限的有效时间，单位秒，声网建议你将该参数和 Token 的有效时间设为一致
    privilege_expiration_in_seconds = 3600

    token = RtcTokenBuilder.build_token_with_uid(app_id, app_certificate, channel_name, uid, Role_Publisher,
                                                 token_expiration_in_seconds, privilege_expiration_in_seconds)
    return token

if __name__ == '__main__':
    if not os.path.exists('recordings'):
        os.makedirs('recordings')
    app.run(debug=True, host='0.0.0.0', port=5000)