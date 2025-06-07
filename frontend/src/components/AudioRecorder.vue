<!-- 
  音频录制组件
  
  用于录制音频并提供播放、上传功能
  可在完整面试模式和快速练习模式中复用
-->
<template>
  <div class="audio-recorder">
    <!-- 录音按钮 -->
    <div class="record-controls">
      <el-button 
        :type="isRecording ? 'danger' : 'primary'" 
        :icon="isRecording ? 'el-icon-video-pause' : 'el-icon-microphone'" 
        @click="toggleRecording"
        :disabled="isPlaying"
      >
        {{ isRecording ? '停止录音' : '开始录音' }}
      </el-button>
      
      <!-- 录音计时器 -->
      <div v-if="isRecording || recordingDuration > 0" class="recording-timer">
        {{ formatTime(recordingDuration) }}
      </div>
    </div>
    
    <!-- 音频波形可视化 -->
    <div v-if="isRecording" class="audio-waveform">
      <div class="wave" :style="{width: audioLevel + '%'}"></div>
    </div>
    
    <!-- 录音完成后的播放控件 -->
    <div v-if="audioUrl" class="playback-controls">
      <audio 
        ref="audioPlayer" 
        :src="audioUrl" 
        controls 
        @play="isPlaying = true" 
        @pause="isPlaying = false"
        @ended="isPlaying = false"
      ></audio>
      
      <!-- 重新录制按钮 -->
      <el-button 
        type="text" 
        icon="el-icon-refresh-right" 
        @click="resetRecording"
        :disabled="isRecording || isPlaying"
      >
        重新录制
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

// 定义组件属性
const props = defineProps({
  mode: {
    type: String,
    default: 'single', // 'single'单次录制模式或'continuous'连续录制模式
    validator: (value) => ['single', 'continuous'].includes(value)
  },
  sessionId: {
    type: [String, Number],
    default: null
  },
  questionId: {
    type: [String, Number],
    default: null
  },
  positionId: {
    type: [String, Number],
    default: null
  },
  maxDuration: {
    type: Number,
    default: 300 // 默认最大录制时长为5分钟
  }
})

// 定义事件
const emit = defineEmits([
  'on-record-start',
  'on-record-stop',
  'on-audio-blob',
  'on-upload-success',
  'on-upload-error'
])

// 内部状态
const isRecording = ref(false)
const isPlaying = ref(false)
const recordingDuration = ref(0)
const audioLevel = ref(0)
const audioUrl = ref(null)
const audioBlob = ref(null)
const audioPlayer = ref(null)

let mediaStream = null
let mediaRecorder = null
let audioChunks = []
let audioContext = null
let analyser = null
let durationTimer = null
let visualizationTimer = null

// 格式化时间为分钟:秒
const formatTime = (seconds) => {
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}:${sec.toString().padStart(2, '0')}`
}

// 开始/停止录音
const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

// 开始录音
const startRecording = async () => {
  try {
    console.log('开始录音...')
    
    // 重置状态
    resetRecording()
    
    // 获取音频流
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    // 创建音频分析器
    setupAudioAnalyzer(mediaStream)
    
    // 创建媒体录制器
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' })
    
    // 收集音频数据
    audioChunks = []
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data)
      }
    }
    
    // 录制完成处理
    mediaRecorder.onstop = () => {
      console.log('录音已停止')
      // 创建音频Blob
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      audioBlob.value = blob
      
      // 创建音频URL
      if (audioUrl.value) {
        URL.revokeObjectURL(audioUrl.value)
      }
      audioUrl.value = URL.createObjectURL(blob)
      
      // 如果是单次录制模式，通知父组件
      if (props.mode === 'single') {
        emit('on-audio-blob', blob)
      }
      
      // 如果是连续录制模式，自动上传
      if (props.mode === 'continuous' && props.sessionId) {
        uploadAudio(blob)
      }
      
      // 触发录制停止事件
      emit('on-record-stop', {
        duration: recordingDuration.value,
        blob: blob
      })
    }
    
    // 开始录制
    mediaRecorder.start()
    isRecording.value = true
    
    // 开始计时
    startTimer()
    
    // 触发录制开始事件
    emit('on-record-start')
    
    // 如果设置了最大录制时长，则定时停止
    if (props.maxDuration > 0) {
      setTimeout(() => {
        if (isRecording.value) {
          console.log(`已达到最大录制时长${props.maxDuration}秒，自动停止录音`)
          stopRecording()
        }
      }, props.maxDuration * 1000)
    }
    
  } catch (err) {
    console.error('录音失败:', err)
    ElMessage.error('无法访问麦克风，请检查权限设置')
  }
}

// 停止录音
const stopRecording = () => {
  if (!isRecording.value || !mediaRecorder) return
  
  console.log('停止录音...')
  
  // 停止录制
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  
  // 停止音频流
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
  }
  
  // 停止计时
  stopTimer()
  
  // 更新状态
  isRecording.value = false
}

// 重置录音
const resetRecording = () => {
  console.log('重置录音...')
  
  // 停止当前录音
  if (isRecording.value) {
    stopRecording()
  }
  
  // 重置播放器
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    isPlaying.value = false
  }
  
  // 释放资源
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
  
  // 重置状态
  recordingDuration.value = 0
  audioLevel.value = 0
  audioUrl.value = null
  audioBlob.value = null
  audioChunks = []
}

// 设置音频分析器
const setupAudioAnalyzer = (stream) => {
  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    analyser = audioContext.createAnalyser()
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)
    analyser.fftSize = 256
    
    // 开始可视化
    startVisualization()
  } catch (err) {
    console.error('音频分析器设置失败:', err)
  }
}

// 开始计时
const startTimer = () => {
  // 清除可能存在的旧计时器
  stopTimer()
  
  // 创建新计时器
  durationTimer = setInterval(() => {
    recordingDuration.value += 1
  }, 1000)
}

// 停止计时
const stopTimer = () => {
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
  
  if (visualizationTimer) {
    clearInterval(visualizationTimer)
    visualizationTimer = null
  }
}

// 开始音频可视化
const startVisualization = () => {
  if (!analyser) return
  
  visualizationTimer = setInterval(() => {
    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteFrequencyData(dataArray)
    
    // 计算平均音量
    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
    audioLevel.value = Math.min(100, Math.round((average / 255) * 100))
  }, 100)
}

// 上传音频
const uploadAudio = async (blob) => {
  if (!blob || (!props.sessionId && !props.questionId)) return
  
  try {
    console.log('上传音频...')
    
    // 创建表单数据
    const formData = new FormData()
    formData.append('file', new File([blob], 'audio.webm', { type: 'audio/webm' }))
    
    let url = ''
    
    // 根据模式决定上传端点
    if (props.mode === 'continuous' && props.sessionId) {
      // 完整面试模式
      url = `/api/interview-sessions/${props.sessionId}/upload-audio`
    } else if (props.mode === 'single' && props.questionId && props.positionId) {
      // 快速练习模式
      url = '/api/practice/upload_audio'
      formData.append('question_id', props.questionId)
      formData.append('position_id', props.positionId)
    } else {
      throw new Error('缺少必要的上传参数')
    }
    
    // 发送请求
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    })
    
    // 处理响应
    if (response.ok) {
      const result = await response.json()
      console.log('音频上传成功:', result)
      emit('on-upload-success', result)
    } else {
      const error = await response.json()
      console.error('音频上传失败:', error)
      emit('on-upload-error', error)
      ElMessage.error('音频上传失败: ' + (error.detail || '未知错误'))
    }
  } catch (err) {
    console.error('音频上传过程出错:', err)
    emit('on-upload-error', { detail: err.message })
    ElMessage.error('音频上传出错: ' + err.message)
  }
}

// 在组件卸载时清理资源
onUnmounted(() => {
  resetRecording()
  stopTimer()
  
  if (audioContext) {
    audioContext.close().catch(err => console.error('关闭音频上下文失败:', err))
  }
  
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
})

// 暴露方法给父组件
defineExpose({
  startRecording,
  stopRecording,
  resetRecording,
  uploadAudio
})
</script>

<style scoped>
.audio-recorder {
  margin: 15px 0;
  padding: 10px;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.record-controls {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.recording-timer {
  margin-left: 15px;
  font-size: 18px;
  font-weight: bold;
  color: #606266;
}

.audio-waveform {
  height: 20px;
  background-color: #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.wave {
  height: 100%;
  background-color: #409eff;
  transition: width 0.1s ease;
}

.playback-controls {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.playback-controls audio {
  width: 100%;
  margin-bottom: 10px;
}
</style> 