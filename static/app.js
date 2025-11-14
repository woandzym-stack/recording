class AgoraRecordingApp {
  constructor() {
      this.client = null;
      this.localAudioTrack = null;
      this.currentRoom = null;
      this.selectedRoomId = null;
      this.selectedRoomData = null;
      this.isJoined = false;
      this.isRecording = false;
      this.recordingId = null;
      
      this.apiBaseUrl = 'http://localhost:5000/api/v1';
      this.logElement = document.getElementById('log');
      
      // 强制设置日志区域左对齐
      this.logElement.style.textAlign = 'left';
      this.logElement.style.whiteSpace = 'pre-wrap';
      
      this.init();
  }

  init() {
      this.log('🚀 系统初始化完成');
      this.log('📡 连接到服务器: ' + this.apiBaseUrl);
      this.loadRooms();
      this.loadRecordings();
      
      // // 定期刷新房间和录制列表
      // setInterval(() => {
      //     this.loadRooms();
      //     this.loadRecordings();
      // }, 5000);
  }

  log(message) {
      const timestamp = new Date().toLocaleTimeString();
      const logEntry = `[${timestamp}] ${message}\n`;
      this.logElement.innerHTML += logEntry;
      this.logElement.scrollTop = this.logElement.scrollHeight;
  }

  async createRoom() {
      const roomName = document.getElementById('roomName').value;
      if (!roomName) {
          alert('请输入房间名称');
          return;
      }

      try {
          this.log(`🆕 正在创建房间: ${roomName}`);
          const response = await fetch(`${this.apiBaseUrl}/rooms`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ roomName })
          });

          const data = await response.json();
          
          if (data.success) {
              this.log(`✅ 房间创建成功: ${data.roomName}`);
              this.log(`🆔 房间ID: ${data.roomId}`);
              this.loadRooms();
              document.getElementById('joinRoomBtn').disabled = false;
              
              // 自动选中新创建的房间
              this.selectRoom(data.roomId);
          } else {
              this.log(`❌ 房间创建失败: ${data.error}`);
          }
      } catch (error) {
          this.log(`❌ 创建房间错误: ${error.message}`);
      }
  }

  selectRoom(roomId) {
      // 移除所有房间的选中状态
      document.querySelectorAll('.room-item').forEach(item => {
          item.classList.remove('selected');
      });
      
      // 添加当前房间的选中状态
      const selectedRoom = document.querySelector(`[data-room-id="${roomId}"]`);
      if (selectedRoom) {
          selectedRoom.classList.add('selected');
          this.selectedRoomId = roomId;
          
          // 更新选中房间信息显示
          const roomName = selectedRoom.querySelector('strong').textContent;
          // const membersCount = selectedRoom.querySelector('.members-count').textContent;
          
          // document.getElementById('selectedRoomInfo').style.display = 'block';
          // document.getElementById('selectedRoomName').textContent = roomName;
          // document.getElementById('selectedRoomId').textContent = roomId;
          // document.getElementById('selectedRoomMembers').textContent = membersCount;
          
          this.selectedRoomData = {
              id: roomId,
              name: roomName
          };
          
          this.log(`🎯 选中房间: ${roomName} (${roomId})`);
          //
          document.getElementById('joinRoomBtn').disabled = false;
      }else {
          this.selectedRoomId = null;
          this.selectedRoomData = null;
          // document.getElementById('selectedRoomInfo').style.display = 'none';
      }
  }

  async joinRoom() {
      if (!this.selectedRoomId) {
          alert('请先选择一个房间');
          return;
      }

      const roomId = this.selectedRoomId;
      const userName = document.getElementById('userName').value || '匿名用户';

      try {
          this.log(this.selectedRoomData);
          const roomName = this.selectedRoomData.name;
          this.log(`🚪 正在加入房间: ${roomName}`);
          this.log(`👤 用户名称: ${userName}`);
          
          const response = await fetch(`${this.apiBaseUrl}/rooms/${roomId}/join`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ roomName, userId: '1001' })
          });

          const data = await response.json();
          
          if (data.success) {
              this.currentRoom = roomId;
              this.isJoined = true;
              this.updateUI();
              this.log(`✅ 成功加入房间: ${this.selectedRoomData.name}`);
              
              // 加入Agora频道
              await this.joinAgoraChannel(roomName, data.token);
          } else {
              this.log(`❌ 加入房间失败: ${data.error}`);
          }
      } catch (error) {
          this.log(`❌ 加入房间错误: ${error.message}`);
      }
  }

  async joinAgoraChannel(channelName, token) {
    try {
        // 初始化Agora客户端
        this.client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
        
        // 监听用户加入
        this.client.on("user-published", async (user, mediaType) => {
            await this.client.subscribe(user, mediaType);
            this.log(`用户 ${user.uid} 加入频道`);

            if (mediaType === "audio") {
                const remoteAudioTrack = user.audioTrack;
                remoteAudioTrack.play();
            }
        });

        // 监听用户离开
        this.client.on("user-left", (user) => {
            this.log(`用户 ${user.uid} 离开频道`);
        });

        const appId = "0e6463cfa74f4553a2d525a8f4e201fa"; // 替换为您的App ID
        const uid = await this.client.join(appId, channelName, token, 1001);
        
        // 创建并发布本地音频轨道
        this.localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
        await this.client.publish([this.localAudioTrack]);
        
        this.log(`成功加入Agora频道: ${channelName}, UID: ${uid}`);
    } catch (error) {
        this.log(`加入Agora频道错误: ${error.message}`);
    }
  }

  async leaveRoom() {
      if (this.client) {
          // 离开Agora频道
          await this.client.leave();
          this.client = null;
      }

      if (this.localAudioTrack) {
          this.localAudioTrack.close();
          this.localAudioTrack = null;
      }

      this.log(`🚪 离开房间: ${this.selectedRoomData.name}`);

      this.currentRoom = null;
      this.isJoined = false;
      this.updateUI();
      this.log('🔇 语音通话已结束');
  }

  async startRecording() {
      if (!this.currentRoom) {
          alert('请先加入房间');
          return;
      }

      try {
          this.log(`⏺️ 开始录制房间: ${this.selectedRoomData.name}`);
          const response = await fetch(`${this.apiBaseUrl}/rooms/${this.currentRoom}/record/start`, {
              method: 'POST'
          });

          const data = await response.json();
          
          if (data.success) {
              this.isRecording = true;
              this.recordingId = data.recordingId;
              this.updateUI();
              this.log(`✅ 录制开始成功: ${data.recordingId}`);
              this.log(`📹 正在录制: ${this.selectedRoomData.name}`);
          } else {
              this.log(`❌ 开始录制失败: ${data.error}`);
          }
      } catch (error) {
          this.log(`❌ 开始录制错误: ${error.message}`);
      }
  }

  async stopRecording() {
      if (!this.currentRoom || !this.isRecording) {
          return;
      }

      try {
          this.log(`⏹️ 停止录制房间: ${this.selectedRoomData.name}`);
          const response = await fetch(`${this.apiBaseUrl}/rooms/${this.currentRoom}/record/stop`, {
              method: 'POST'
          });

          const data = await response.json();

          if (data.success) {
              this.isRecording = false;
              this.recordingId = null;
              this.updateUI();
              this.log(`✅ 停止录制成功: ${data.recordingId}`);
              this.log(`💾 录制文件保存中...`);
              this.loadRecordings();
          } else {
              this.log(`❌ 停止录制失败: ${data.error}`);
          }
      } catch (error) {
          this.log(`❌ 停止录制错误: ${error.message}`);
      }
  }

  async loadRooms() {
      try {
          const response = await fetch(`${this.apiBaseUrl}/rooms`);
          const data = await response.json();
          
          if (data.success) {
              this.renderRoomList(data.rooms);
          }
      } catch (error) {
          console.error('加载房间列表错误:', error);
      }
  }

  async loadRecordings() {
      try {
          const response = await fetch(`${this.apiBaseUrl}/recordings`);
          const data = await response.json();
          
          // this.log("调用recordings的结果"+JSON.stringify(data));
          if (data.success) {
              this.renderRecordingList(data.recordings);
          }
      } catch (error) {
          console.error('加载录制列表错误:', error);
      }
  }

  renderRoomList(rooms) {
      const roomList = document.getElementById('roomList');
      roomList.innerHTML = '';

      if (rooms.length === 0) {
          roomList.innerHTML = '<div class="room-item">暂无房间，请创建新房间</div>';
          return;
      }

      rooms.forEach(room => {
          const roomItem = document.createElement('div');
          roomItem.className = 'room-item';
          roomItem.dataset.roomId = room.id;
          roomItem.innerHTML = `
              <strong>${room.name}</strong><br>
              <small>ID: ${room.id.slice(0, 8)}...</small><br>
              <small> | 创建: ${new Date(room.created_at * 1000).toLocaleTimeString()}</small>
          `;
          
          // 添加点击事件
          roomItem.addEventListener('click', () => {
              this.selectRoom(room.id);
          });
          
          roomList.appendChild(roomItem);
      });

      // 如果之前有选中的房间，恢复选中状态
      if (this.selectedRoomId) {
          const previouslySelected = document.querySelector(`[data-room-id="${this.selectedRoomId}"]`);
          if (previouslySelected) {
              previouslySelected.classList.add('selected');
          }
      }
  }

  renderRecordingList(recordings) {
      const recordingList = document.getElementById('recordingList');
      recordingList.innerHTML = '';

      if (recordings.length === 0) {
          recordingList.innerHTML = '<div class="recording-item">暂无录制文件</div>';
          return;
      }

      recordings.forEach(recording => {
          const recordingItem = document.createElement('div');
          recordingItem.className = 'recording-item';
          recordingItem.innerHTML = `
              <strong>录制 ${recording.id.slice(0, 8)}</strong><br>
              <small>状态: ${recording.status}</small><br>
              <small>开始: ${new Date(recording.startedAt * 1000).toLocaleString()}</small>
              <button onclick="app.downloadRecording('${recording.id}')" style="margin-top: 8px; padding: 5px 10px; font-size: 0.9rem;">下载</button>
          `;
          recordingList.appendChild(recordingItem);
      });
  }

  async downloadRecording(recordingId) {
      try {
          this.log(`📥 下载录制文件: ${recordingId}`);
          const response = await fetch(`${this.apiBaseUrl}/recordings/${recordingId}`);
          const data = await response.json();
          
          if (data.success && data.files && data.files.length > 0) {
              data.files.forEach(file => {
                  window.open(file.url, '_blank');
              });
              this.log(`✅ 开始下载录制文件: ${recordingId}`);
          } else {
              this.log(`❌ 无法获取录制文件: ${recordingId}`);
          }
      } catch (error) {
          this.log(`❌ 下载录制文件错误: ${error.message}`);
      }
  }

  updateUI() {
      // 更新房间状态
      const roomStatus = document.getElementById('roomStatus');
      if (this.isJoined) {
          roomStatus.textContent = `已加入房间: ${this.selectedRoomData ? this.selectedRoomData.name : this.currentRoom}`;
          roomStatus.className = 'status recording';
      } else {
          roomStatus.textContent = '未加入房间';
          roomStatus.className = 'status idle';
          document.getElementById('leaveRoomBtn').disabled = true;
      }


      // 更新录制状态
      const recordStatus = document.getElementById('recordStatus');
      if (this.isRecording) {
          recordStatus.textContent = `正在录制: ${this.selectedRoomData ? this.selectedRoomData.name : '未知房间'}`;
          recordStatus.className = 'status recording';
      } else {
          recordStatus.textContent = '录制未开始';
          recordStatus.className = 'status idle';
      }

      // 更新按钮状态
      document.getElementById('joinRoomBtn').disabled = this.isJoined || !this.selectedRoomId;
      document.getElementById('leaveRoomBtn').disabled = !this.isJoined;
      document.getElementById('startRecordBtn').disabled = !this.isJoined || this.isRecording;
      document.getElementById('stopRecordBtn').disabled = !this.isJoined || !this.isRecording;
  }
}

// 创建应用实例
const app = new AgoraRecordingApp();

// 全局函数供HTML调用
function createRoom() { app.createRoom(); }
function joinRoom() { app.joinRoom(); }
function leaveRoom() { app.leaveRoom(); }
function startRecording() { app.startRecording(); }
function stopRecording() { app.stopRecording(); }