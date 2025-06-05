import axios from 'axios'
import { useUserStore } from '../stores/user'
import { API_URL } from '../config'

// 创建axios实例
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 缩短超时时间，更快检测到后端不可用
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
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API请求失败:', error.message || '未知错误')
    
    // 处理网络错误
    if (!error.response) {
      console.error('网络错误或后端服务不可用')
    } 
    // 处理401未授权错误
    else if (error.response.status === 401) {
      console.warn('用户未授权或token已过期，执行登出操作')
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    } 
    // 处理其他HTTP错误
    else {
      console.error(`HTTP错误 ${error.response.status}: ${error.response.statusText}`)
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
    try {
      console.log('获取面试会话列表，参数:', params);
      const response = await api.get('/interview-sessions/', { params });
      console.log('API响应:', response.data);
      return response.data;
    } catch (error) {
      console.error('获取面试会话列表失败:', error);
      
      // 在开发环境中返回模拟数据
      if (import.meta.env.DEV) {
        console.warn('开发环境使用模拟数据');
        
        // 生成面试记录模拟数据
        const total = 15;
        const { page = 1, limit = 10 } = params;
        const start = (page - 1) * limit;
        const end = Math.min(start + limit, total);
        
        const items = [];
        const now = new Date();
        
        for (let i = start; i < end; i++) {
          const date = new Date(now);
          date.setDate(date.getDate() - i - 1);
          
          const positions = [
            { id: 1, title: '前端工程师', tech_field: 'frontend' },
            { id: 2, title: '后端工程师', tech_field: 'backend' },
            { id: 3, title: '全栈工程师', tech_field: 'fullstack' },
            { id: 4, title: '产品经理', tech_field: 'product' },
            { id: 5, title: '数据分析师', tech_field: 'data' }
          ];
          
          items.push({
            id: `interview-${i + 1}`,
            title: `实际面试练习 ${i + 1}`,
            position: positions[i % positions.length],
            created_at: date.toISOString(),
            duration: Math.floor(Math.random() * 40 + 10) * 60,
            questions: Array(Math.floor(Math.random() * 10 + 5)).fill(null).map((_, j) => ({ 
              id: `q-${i}-${j}`, 
              content: `问题 ${j + 1}` 
            })),
            overall_score: (Math.random() * 3 + 7).toFixed(1)
          });
        }
        
        return {
          items: items,
          total: total,
          page: page,
          limit: limit,
          pages: Math.ceil(total / limit)
        };
      }
      
      throw error;
    }
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
    try {
      const response = await api.get(`/interview-sessions/${sessionId}/report`)
      return response.data
    } catch (error) {
      console.error(`获取面试报告失败 (ID: ${sessionId}):`, error)
      
      // 如果后端不可用，返回模拟数据以便前端开发测试
      if (!error.response || error.code === 'ECONNABORTED') {
        console.warn('后端不可用，使用模拟数据')
        return {
          id: sessionId,
          createdAt: new Date().toISOString(),
          overallScore: 7.5,
          scores: {
            professionalKnowledge: 8.0, 
            communicationSkills: 7.2,
            problemSolving: 6.8,
            attitudeAndPotential: 8.1,
            culturalFit: 7.9
          },
          qaList: [
            { type: 'question', content: '请简单介绍一下你自己和你的项目经验。' },
            { type: 'answer', content: '我是一名有5年经验的前端开发工程师，专注于Vue和React开发...' },
            { type: 'question', content: '你是如何处理项目中遇到的技术难题的？' },
            { type: 'answer', content: '我通常会先分析问题的根本原因，然后查阅相关文档和最佳实践...' }
          ],
          overallFeedback: '<p>您在面试中展现了扎实的技术功底和良好的沟通能力。</p><p>优势：技术知识全面，思路清晰，回答问题有条理。</p><p>改进点：可以更多地结合具体案例，展示解决复杂问题的能力。</p>'
        }
      }
      throw error
    }
  },

  // 获取面试统计数据
  getStatistics: async () => {
    try {
      const response = await api.get('/users/interview-stats')
      return response.data
    } catch (error) {
      console.error('获取面试统计失败:', error)
      
      // 如果后端不可用，返回模拟数据
      if (!error.response || error.code === 'ECONNABORTED') {
        console.warn('后端不可用，使用模拟数据')
        return {
          total: 5,
          averageScore: 7.4,
          highestScore: 8.9,
          scoreDistribution: {
            excellent: 2,  // 8-10分
            good: 2,       // 6-8分
            average: 1,    // 4-6分
            poor: 0        // 0-4分
          }
        }
      }
      throw error
    }
  },

  // 获取最近的面试记录
  getRecent: async (limit = 5) => {
    try {
      const response = await api.get(`/interview-sessions/recent?limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('获取最近面试记录失败:', error)
      
      // 如果后端不可用，返回模拟数据
      if (!error.response || error.code === 'ECONNABORTED') {
        console.warn('后端不可用，使用模拟数据')
        // 生成模拟数据
        const mockData = []
        const positions = ['前端开发工程师', '后端开发工程师', '全栈工程师', 'DevOps工程师', '数据分析师']
        const now = new Date()
        
        for (let i = 0; i < limit; i++) {
          const date = new Date(now)
          date.setDate(date.getDate() - i * 3) // 每3天一次面试
          
          mockData.push({
            id: `mock-${i + 1}`,
            date: date.toISOString(),
            position: positions[i % positions.length],
            score: Math.round((6 + Math.random() * 4) * 10) / 10 // 6-10分之间的随机分数
          })
        }
        
        return mockData
      }
      throw error
    }
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
  },

  // 上传音频数据
  uploadAudio: async (sessionId, audioFile, timestamp) => {
    const formData = new FormData()
    formData.append('audio', audioFile)
    formData.append('timestamp', timestamp)
    
    const response = await axios.post(
      `${API_URL}/interview-sessions/${sessionId}/upload-audio`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${useUserStore().token}`
        }
      }
    )
    return response.data
  },

  // 上传视频帧
  uploadVideo: async (sessionId, videoFile, timestamp) => {
    const formData = new FormData()
    formData.append('video', videoFile)
    formData.append('timestamp', timestamp)
    
    const response = await axios.post(
      `${API_URL}/interview-sessions/${sessionId}/upload-video`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${useUserStore().token}`
        }
      }
    )
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
      // 从API_URL获取WebSocket URL
      const wsProtocol = API_URL.startsWith('https') ? 'wss://' : 'ws://'
      const wsBaseUrl = API_URL.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '')
      const wsUrl = `${wsProtocol}${wsBaseUrl}${API_URL.includes('/api/v1') ? '/api/v1' : ''}/interview-sessions/${this.sessionId}/ws?token=${userStore.token}`
      
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

  getReadyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  close() {
    if (this.ws) {
      this.ws.close()
    }
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
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      this.mediaRecorder = new MediaRecorder(this.stream)
      this.audioChunks = []
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.onstop = () => {
        this.isRecording = false
      }
      
      this.mediaRecorder.start(1000) // 每秒触发一次dataavailable事件
      this.isRecording = true
      return true
    } catch (error) {
      console.error('启动音频录制失败:', error)
      return false
    }
  }

  stopRecording() {
    return new Promise((resolve) => {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.onstop = () => {
          const blob = new Blob(this.audioChunks, { type: 'audio/webm' })
          this.isRecording = false
          
          // 停止所有音频轨道
          if (this.stream) {
            this.stream.getAudioTracks().forEach(track => track.stop())
          }
          
          resolve(blob)
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
        audio: true,
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 15 }
        }
      })
      this.mediaRecorder = new MediaRecorder(this.stream)
      this.videoChunks = []
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.videoChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.onstop = () => {
        this.isRecording = false
      }
      
      this.mediaRecorder.start(1000) // 每秒触发一次dataavailable事件
      this.isRecording = true
      return this.stream
    } catch (error) {
      console.error('启动视频录制失败:', error)
      return null
    }
  }

  stopRecording() {
    return new Promise((resolve) => {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.onstop = () => {
          const blob = new Blob(this.videoChunks, { type: 'video/webm' })
          this.isRecording = false
          
          // 停止所有视频轨道
          if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop())
          }
          
          resolve(blob)
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