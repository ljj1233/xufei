import axios from 'axios'
import { useUserStore } from '../stores/user'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 面试会话API
export const interviewSessionAPI = {
  // 创建面试会话
  createSession: async (sessionData) => {
    const response = await api.post('/interview-sessions/', sessionData)
    return response.data
  },

  // 获取面试会话列表
  getSessions: async (params = {}) => {
    const response = await api.get('/interview-sessions/', { params })
    return response.data
  },

  // 获取面试会话详情
  getSession: async (sessionId) => {
    const response = await api.get(`/interview-sessions/${sessionId}`)
    return response.data
  },

  // 开始面试会话
  startSession: async (sessionId) => {
    const response = await api.post(`/interview-sessions/${sessionId}/start`)
    return response.data
  },

  // 完成面试会话
  completeSession: async (sessionId) => {
    const response = await api.post(`/interview-sessions/${sessionId}/complete`)
    return response.data
  },

  // 暂停面试会话
  pauseSession: async (sessionId) => {
    const response = await api.post(`/interview-sessions/${sessionId}/pause`)
    return response.data
  },

  // 恢复面试会话
  resumeSession: async (sessionId) => {
    const response = await api.post(`/interview-sessions/${sessionId}/resume`)
    return response.data
  },

  // 删除面试会话
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/interview-sessions/${sessionId}`)
    return response.data
  },

  // 获取面试问题列表
  getQuestions: async (sessionId) => {
    const response = await api.get(`/interview-sessions/${sessionId}/questions`)
    return response.data
  },

  // 提交问题回答
  submitAnswer: async (sessionId, questionId, answerData) => {
    const response = await api.post(
      `/interview-sessions/${sessionId}/questions/${questionId}/answer`,
      answerData
    )
    return response.data
  },

  // 获取会话分析结果
  getAnalysis: async (sessionId) => {
    const response = await api.get(`/interview-sessions/${sessionId}/analysis`)
    return response.data
  },

  // 获取实时反馈记录
  getFeedback: async (sessionId, params = {}) => {
    const response = await api.get(`/interview-sessions/${sessionId}/feedback`, { params })
    return response.data
  },

  // 获取面试报告
  getReport: async (sessionId) => {
    const response = await api.get(`/interview-sessions/${sessionId}/report`)
    return response.data
  },

  // 获取用户统计数据
  getUserStats: async () => {
    const response = await api.get('/interview-sessions/stats')
    return response.data
  },

  // 提交实时数据（用于实时分析）
  submitRealTimeData: async (sessionId, data) => {
    const response = await api.post(`/interview-sessions/${sessionId}/realtime-data`, data)
    return response.data
  }
}

// WebSocket连接管理
export class InterviewWebSocket {
  constructor(sessionId, onMessage, onError, onClose) {
    this.sessionId = sessionId
    this.onMessage = onMessage
    this.onError = onError
    this.onClose = onClose
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
  }

  connect() {
    try {
      const userStore = useUserStore()
      const wsUrl = `ws://localhost:8000/api/v1/interview-sessions/${this.sessionId}/ws?token=${userStore.token}`
      
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
        this.reconnectAttempts = 0
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        if (this.onError) {
          this.onError(error)
        }
      }
      
      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭', event.code, event.reason)
        if (this.onClose) {
          this.onClose(event)
        }
        
        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts && !event.wasClean) {
          setTimeout(() => {
            this.reconnectAttempts++
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
            this.connect()
          }, this.reconnectInterval)
        }
      }
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
      if (this.onError) {
        this.onError(error)
      }
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  close() {
    if (this.ws) {
      this.ws.close(1000, '正常关闭')
    }
  }

  getReadyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }
}

// 音频录制工具类
export class AudioRecorder {
  constructor() {
    this.mediaRecorder = null
    this.audioChunks = []
    this.stream = null
    this.isRecording = false
  }

  async startRecording() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      this.audioChunks = []
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.start(1000) // 每秒收集一次数据
      this.isRecording = true
      
      return true
    } catch (error) {
      console.error('启动录音失败:', error)
      throw error
    }
  }

  stopRecording() {
    return new Promise((resolve) => {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
          this.isRecording = false
          
          // 停止所有音频轨道
          if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop())
          }
          
          resolve(audioBlob)
        }
        
        this.mediaRecorder.stop()
      } else {
        resolve(null)
      }
    })
  }

  pauseRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.pause()
    }
  }

  resumeRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.resume()
    }
  }
}

// 视频录制工具类
export class VideoRecorder {
  constructor() {
    this.mediaRecorder = null
    this.videoChunks = []
    this.stream = null
    this.isRecording = false
  }

  async startRecording() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: true
      })
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'video/webm;codecs=vp9,opus'
      })
      
      this.videoChunks = []
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.videoChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.start(1000)
      this.isRecording = true
      
      return this.stream
    } catch (error) {
      console.error('启动视频录制失败:', error)
      throw error
    }
  }

  stopRecording() {
    return new Promise((resolve) => {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.onstop = () => {
          const videoBlob = new Blob(this.videoChunks, { type: 'video/webm' })
          this.isRecording = false
          
          if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop())
          }
          
          resolve(videoBlob)
        }
        
        this.mediaRecorder.stop()
      } else {
        resolve(null)
      }
    })
  }

  getVideoStream() {
    return this.stream
  }
}

export default interviewSessionAPI