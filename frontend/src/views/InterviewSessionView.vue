<template>
  <div class="interview-session">
    <div class="session-header">
      <h2>面试进行中</h2>
      <p>会话ID：{{ sessionId }}</p>
      <button @click="endSession" class="btn btn-danger">结束面试</button>
    </div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { interviewSessionAPI } from '../api/interviewSession'

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
    const endSession = () => {
      stopMedia()
      router.push('/practice-history')
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
      toggleRecording,
      endSession,
      formatTime
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
</style>