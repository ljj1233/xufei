<template>
  <div class="interview-session">
    <div class="session-header">
      <h2>面试进行中</h2>
      <p>会话ID：{{ sessionId }}</p>
      <button @click="endSession" class="btn btn-danger">结束面试</button>
    </div>
    
    <!-- 评分结果弹窗 -->
    <el-dialog
      v-model="scoreDialogVisible"
      title="面试评分结果"
      width="500px"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      center
    >
      <div class="score-dialog-content" v-loading="scoreLoading">
        <template v-if="!scoreLoading && scoreResult">
          <div class="score-result">
            <el-progress type="dashboard" :percentage="scoreResult.overall_score * 10" :color="getScoreColor" :width="120">
              <template #default="{ percentage }">
                <span class="progress-value">{{ (percentage / 10).toFixed(1) }}</span>
                <span class="progress-label">总分</span>
              </template>
            </el-progress>
            
            <!-- 好评气球动画 -->
            <div v-if="scoreResult.overall_score >= 7" class="celebration-animation">
              <div v-for="n in 10" :key="n" class="balloon" :style="getRandomBalloonStyle()"></div>
            </div>
            
            <!-- 差评哭脸动画 -->
            <div v-if="scoreResult.overall_score < 5" class="sad-animation">
              <div class="sad-face">😢</div>
            </div>
          </div>
          
          <div class="score-detail">
            <div class="score-item">
              <span class="score-label">内容评分</span>
              <el-progress :percentage="scoreResult.content_score * 10" :color="getScoreColor" :show-text="false" />
              <span class="score-value">{{ scoreResult.content_score.toFixed(1) }}</span>
            </div>
            
            <div class="score-item">
              <span class="score-label">语音评分</span>
              <el-progress :percentage="scoreResult.speech_score * 10" :color="getScoreColor" :show-text="false" />
              <span class="score-value">{{ scoreResult.speech_score.toFixed(1) }}</span>
            </div>
            
            <div class="score-item">
              <span class="score-label">视觉评分</span>
              <el-progress :percentage="scoreResult.visual_score * 10" :color="getScoreColor" :show-text="false" />
              <span class="score-value">{{ scoreResult.visual_score.toFixed(1) }}</span>
            </div>
          </div>
          
          <div class="dialog-footer">
            <el-button @click="viewDetailReport">查看详细报告</el-button>
            <el-button type="primary" @click="closeScoreDialog">返回列表</el-button>
          </div>
        </template>
      </div>
    </el-dialog>
    <div class="session-main">
      <div class="video-section">
        <video ref="videoRef" autoplay muted playsinline width="320" height="240"></video>
        <div class="audio-waveform" v-if="audioLevel > 0">
          <div class="wave" :style="{width: audioLevel + '%'}"></div>
        </div>
        <button @click="toggleRecording" class="btn btn-primary">
          {{ isRecording ? '暂停采集' : '开始采集' }}
        </button>
      </div>
      <div class="feedback-section">
        <h3>实时反馈</h3>
        <div v-if="feedbackList.length === 0" class="feedback-empty">暂无反馈</div>
        <ul class="feedback-list">
          <li v-for="(item, idx) in feedbackList" :key="idx" :class="['feedback-item', item.severity]">
            <span class="feedback-time">{{ formatTime(item.session_time) }}</span>
            <span class="feedback-type">[{{ item.feedback_type === 'speech' ? '语音' : '视觉' }}]</span>
            <span class="feedback-message">{{ item.message }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { interviewSessionAPI } from '../api/interviewSession'
import { ElMessage } from 'element-plus'

export default {
  name: 'InterviewSessionView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const sessionId = route.params.id
    const videoRef = ref(null)
    const isRecording = ref(false)
    const audioLevel = ref(0)
    const feedbackList = ref([])
    const scoreDialogVisible = ref(false)
    const scoreLoading = ref(false)
    const scoreResult = ref(null)
    let mediaStream = null
    let audioContext = null
    let analyser = null
    let audioSource = null
    let audioInterval = null
    let videoInterval = null

    // 格式化时间
    const formatTime = (seconds) => {
      const min = Math.floor(seconds / 60)
      const sec = Math.floor(seconds % 60)
      return `${min}:${sec.toString().padStart(2, '0')}`
    }

    // 采集音视频流
    const startMedia = async () => {
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        if (videoRef.value) {
          videoRef.value.srcObject = mediaStream
        }
        // 音频分析
        audioContext = new (window.AudioContext || window.webkitAudioContext)()
        audioSource = audioContext.createMediaStreamSource(mediaStream)
        analyser = audioContext.createAnalyser()
        audioSource.connect(analyser)
        analyser.fftSize = 256
        // 定时上传音频片段
        audioInterval = setInterval(captureAndUploadAudio, 1500)
        // 定时上传视频帧
        videoInterval = setInterval(captureAndUploadVideo, 2000)
      } catch (e) {
        alert('无法获取摄像头/麦克风权限')
      }
    }

    // 停止采集
    const stopMedia = () => {
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop())
        mediaStream = null
      }
      if (audioInterval) clearInterval(audioInterval)
      if (videoInterval) clearInterval(videoInterval)
      if (audioContext) audioContext.close()
    }

    // 音频采集与上传
    const captureAndUploadAudio = async () => {
      if (!analyser) return
      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      analyser.getByteFrequencyData(dataArray)
      // 简单音量可视化
      const avg = dataArray.reduce((a, b) => a + b, 0) / bufferLength
      audioLevel.value = Math.min(100, Math.round((avg / 255) * 100))
      // 录制音频片段
      const mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' })
      let chunks = []
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const file = new File([blob], 'audio.webm', { type: 'audio/webm' })
        await interviewSessionAPI.uploadAudio(sessionId, file, Date.now() / 1000)
      }
      mediaRecorder.start()
      setTimeout(() => mediaRecorder.stop(), 1000)
    }

    // 视频帧采集与上传
    const captureAndUploadVideo = async () => {
      if (!videoRef.value) return
      const canvas = document.createElement('canvas')
      canvas.width = 320
      canvas.height = 240
      const ctx = canvas.getContext('2d')
      ctx.drawImage(videoRef.value, 0, 0, 320, 240)
      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'frame.jpg', { type: 'image/jpeg' })
        await interviewSessionAPI.uploadVideo(sessionId, file, Date.now() / 1000)
      }, 'image/jpeg', 0.8)
    }

    // 切换采集
    const toggleRecording = () => {
      if (isRecording.value) {
        stopMedia()
        isRecording.value = false
      } else {
        startMedia()
        isRecording.value = true
      }
    }

    // 结束面试
    const endSession = async () => {
      stopMedia()
      
      // 完成面试会话
      try {
        await interviewSessionAPI.completeSession(sessionId)
        
        // 显示评分结果弹窗
        showScoreDialog()
      } catch (error) {
        console.error('结束面试失败:', error)
        ElMessage.error('结束面试失败，请稍后重试')
        router.push('/practice-history')
      }
    }
    
    // 显示评分结果弹窗
    const showScoreDialog = async () => {
      scoreDialogVisible.value = true
      scoreLoading.value = true
      
      try {
        // 获取分析结果
        const result = await interviewSessionAPI.getAnalysis(sessionId)
        scoreResult.value = result
      } catch (error) {
        console.error('获取评分结果失败:', error)
        ElMessage.error('获取评分结果失败，请稍后查看详细报告')
        scoreResult.value = {
          overall_score: 0,
          content_score: 0,
          speech_score: 0,
          visual_score: 0
        }
      } finally {
        scoreLoading.value = false
      }
    }
    
    // 关闭评分结果弹窗
    const closeScoreDialog = () => {
      scoreDialogVisible.value = false
      router.push('/practice-history')
    }
    
    // 查看详细报告
    const viewDetailReport = () => {
      router.push(`/report/${sessionId}`)
    }
    
    // 获取评分颜色
    const getScoreColor = (percentage) => {
      if (percentage < 40) return '#F56C6C'
      if (percentage < 70) return '#E6A23C'
      return '#67C23A'
    }
    
    // 获取随机气球样式
    const getRandomBalloonStyle = () => {
      const colors = ['#ff5252', '#ffb142', '#34ace0', '#33d9b2', '#706fd3']
      const size = Math.floor(Math.random() * 30) + 30 // 30-60px
      const left = Math.floor(Math.random() * 80) + 10 // 10-90%
      const animationDuration = Math.floor(Math.random() * 5) + 5 // 5-10s
      const animationDelay = Math.random() * 3 // 0-3s
      
      return {
        backgroundColor: colors[Math.floor(Math.random() * colors.length)],
        width: `${size}px`,
        height: `${size}px`,
        left: `${left}%`,
        animationDuration: `${animationDuration}s`,
        animationDelay: `${animationDelay}s`
      }
    }

    // 拉取实时反馈
    const fetchFeedback = async () => {
      try {
        const res = await interviewSessionAPI.getRealTimeFeedback(sessionId)
        feedbackList.value = res.data || []
      } catch (e) {
        // ignore
      }
    }

    let feedbackTimer = null
    onMounted(() => {
      fetchFeedback()
      feedbackTimer = setInterval(fetchFeedback, 2000)
    })
    onUnmounted(() => {
      stopMedia()
      if (feedbackTimer) clearInterval(feedbackTimer)
    })

    return {
      sessionId,
      videoRef,
      isRecording,
      audioLevel,
      feedbackList,
      scoreDialogVisible,
      scoreLoading,
      scoreResult,
      toggleRecording,
      endSession,
      formatTime,
      getScoreColor,
      getRandomBalloonStyle,
      viewDetailReport,
      closeScoreDialog
    }
  }
}
</script>

<style scoped>
.interview-session {
  padding: 2rem;
  background: #f8f9fa;
  min-height: 100vh;
}
.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}
.session-main {
  display: flex;
  gap: 2rem;
}
.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.audio-waveform {
  width: 100%;
  height: 8px;
  background: #eee;
  border-radius: 4px;
  margin: 0.5rem 0 1rem 0;
  overflow: hidden;
}
.wave {
  height: 100%;
  background: linear-gradient(90deg, #4f8cff, #6fd6ff);
  transition: width 0.2s;
}
.feedback-section {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  min-height: 320px;
}
.feedback-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.feedback-item {
  margin-bottom: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: #f4f8ff;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.feedback-item.success { background: #e6ffed; }
.feedback-item.warning { background: #fffbe6; }
.feedback-item.info { background: #e6f7ff; }
.feedback-item.danger { background: #fff1f0; }
.feedback-time {
  color: #888;
  font-size: 0.9em;
  margin-right: 0.5em;
}
.feedback-type {
  font-weight: bold;
  margin-right: 0.5em;
}
.feedback-message {
  flex: 1;
}
.feedback-empty {
  color: #aaa;
  text-align: center;
  margin-top: 2em;
}

/* 评分结果弹窗样式 */
.score-dialog-content {
  padding: 20px 0;
  min-height: 300px;
}

.score-result {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  margin-bottom: 30px;
}

.progress-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.progress-label {
  display: block;
  font-size: 14px;
  color: #909399;
}

.score-detail {
  margin: 0 auto;
  max-width: 400px;
}

.score-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.score-label {
  width: 80px;
  text-align: right;
  margin-right: 15px;
  color: #606266;
}

.score-value {
  width: 40px;
  text-align: right;
  margin-left: 10px;
  font-weight: bold;
  color: #303133;
}

.score-item .el-progress {
  flex: 1;
}

.dialog-footer {
  margin-top: 30px;
  text-align: center;
}

/* 气球动画 */
.celebration-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.balloon {
  position: absolute;
  bottom: -50px;
  border-radius: 50%;
  animation: float-up linear forwards;
}

@keyframes float-up {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-300px) rotate(360deg);
    opacity: 0;
  }
}

/* 哭脸动画 */
.sad-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  z-index: 10;
}

.sad-face {
  font-size: 60px;
  animation: sad-bounce 2s ease-in-out infinite;
}

@keyframes sad-bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}
</style>