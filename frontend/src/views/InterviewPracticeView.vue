<template>
  <div class="interview-practice">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-microphone-alt"></i>
        模拟面试练习
      </h1>
      <p class="page-subtitle">选择职位和配置参数，开始您的AI面试练习</p>
    </div>

    <!-- 主要内容区域 -->
    <div class="practice-container">
      <!-- 左侧：配置面试 -->
      <div class="config-section">
        <div class="config-card">
          <h2 class="section-title">
            <i class="fas fa-cog"></i>
            面试配置
          </h2>
          
          <form @submit.prevent="createInterview" class="config-form">
            <!-- 基本信息 -->
            <div class="form-group">
              <label for="title">面试标题</label>
              <input
                id="title"
                v-model="form.title"
                type="text"
                placeholder="请输入面试标题"
                required
              />
            </div>

            <div class="form-group">
              <label for="description">面试描述</label>
              <textarea
                id="description"
                v-model="form.description"
                placeholder="请描述本次面试的目标和要求（可选）"
                rows="3"
              ></textarea>
            </div>

            <!-- 职位选择 -->
            <div class="form-group">
              <label for="jobPosition">目标职位</label>
              <select
                id="jobPosition"
                v-model="form.job_position_id"
                required
                @change="onJobPositionChange"
              >
                <option value="">请选择职位</option>
                <option
                  v-for="position in jobPositions"
                  :key="position.id"
                  :value="position.id"
                >
                  {{ position.name }} - {{ position.field }}
                </option>
              </select>
            </div>

            <!-- 职位详情显示 -->
            <div v-if="selectedPosition" class="position-details">
              <h4>职位详情</h4>
              <div class="detail-item">
                <strong>技术领域：</strong>{{ selectedPosition.field }}
              </div>
              <div class="detail-item">
                <strong>岗位类型：</strong>{{ selectedPosition.type }}
              </div>
              <div class="detail-item">
                <strong>所需技能：</strong>{{ selectedPosition.required_skills }}
              </div>
              <div class="detail-item">
                <strong>岗位描述：</strong>{{ selectedPosition.description }}
              </div>
            </div>

            <!-- 面试参数 -->
            <div class="form-row">
              <div class="form-group half">
                <label for="difficulty">难度等级</label>
                <select id="difficulty" v-model="form.difficulty_level">
                  <option value="easy">简单</option>
                  <option value="medium">中等</option>
                  <option value="hard">困难</option>
                </select>
              </div>
              
              <div class="form-group half">
                <label for="questionCount">问题数量</label>
                <select id="questionCount" v-model="form.question_count">
                  <option :value="3">3题</option>
                  <option :value="5">5题</option>
                  <option :value="8">8题</option>
                  <option :value="10">10题</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label for="duration">预计时长</label>
                <select id="duration" v-model="form.planned_duration">
                  <option :value="900">15分钟</option>
                  <option :value="1800">30分钟</option>
                  <option :value="2700">45分钟</option>
                  <option :value="3600">60分钟</option>
                </select>
              </div>
              
              <div class="form-group half">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="form.enable_real_time_feedback"
                  />
                  <span class="checkmark"></span>
                  启用实时反馈
                </label>
              </div>
            </div>

            <!-- 提交按钮 -->
            <div class="form-actions">
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="loading || !form.job_position_id"
              >
                <i class="fas fa-play" v-if="!loading"></i>
                <i class="fas fa-spinner fa-spin" v-else></i>
                {{ loading ? '创建中...' : '开始面试' }}
              </button>
              
              <router-link to="/practice-history" class="btn btn-secondary">
                <i class="fas fa-history"></i>
                练习历史
              </router-link>
            </div>
          </form>
        </div>
      </div>

      <!-- 右侧：功能介绍和统计 -->
      <div class="info-section">
        <!-- 功能介绍 -->
        <div class="info-card">
          <h3 class="card-title">
            <i class="fas fa-lightbulb"></i>
            功能特色
          </h3>
          <div class="feature-list">
            <div class="feature-item">
              <i class="fas fa-brain"></i>
              <div>
                <h4>多模态分析</h4>
                <p>综合分析语音、表情、肢体语言等多维度数据</p>
              </div>
            </div>
            <div class="feature-item">
              <i class="fas fa-comments"></i>
              <div>
                <h4>实时反馈</h4>
                <p>面试过程中提供即时的表现反馈和改进建议</p>
              </div>
            </div>
            <div class="feature-item">
              <i class="fas fa-chart-radar"></i>
              <div>
                <h4>能力评估</h4>
                <p>生成详细的能力雷达图和个性化提升方案</p>
              </div>
            </div>
            <div class="feature-item">
              <i class="fas fa-graduation-cap"></i>
              <div>
                <h4>学习推荐</h4>
                <p>基于表现提供针对性的学习资源和路径</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 个人统计 -->
        <div class="stats-card" v-if="userStats">
          <h3 class="card-title">
            <i class="fas fa-chart-line"></i>
            我的统计
          </h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ userStats.total_sessions }}</div>
              <div class="stat-label">总练习次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.average_score?.toFixed(1) || '0.0' }}</div>
              <div class="stat-label">平均得分</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ Math.round(userStats.average_duration / 60) || 0 }}</div>
              <div class="stat-label">平均时长(分钟)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ (userStats.completion_rate * 100)?.toFixed(0) || 0 }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </div>

        <!-- 技术领域覆盖 -->
        <div class="domains-card">
          <h3 class="card-title">
            <i class="fas fa-code"></i>
            支持领域
          </h3>
          <div class="domains-list">
            <div class="domain-tag ai">
              <i class="fas fa-robot"></i>
              人工智能
            </div>
            <div class="domain-tag bigdata">
              <i class="fas fa-database"></i>
              大数据
            </div>
            <div class="domain-tag iot">
              <i class="fas fa-wifi"></i>
              物联网
            </div>
            <div class="domain-tag system">
              <i class="fas fa-cogs"></i>
              智能系统
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { interviewSessionAPI } from '../api/interviewSession'
import { jobPositionAPI } from '../api/jobPosition'
import { ElMessage } from 'element-plus'

export default {
  name: 'InterviewPracticeView',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const jobPositions = ref([])
    const userStats = ref(null)
    
    const form = reactive({
      title: '',
      description: '',
      job_position_id: '',
      difficulty_level: 'medium',
      question_count: 5,
      planned_duration: 1800,
      enable_real_time_feedback: true
    })

    const selectedPosition = computed(() => {
      return jobPositions.value.find(p => p.id === parseInt(form.job_position_id))
    })

    // 加载职位列表
    const loadJobPositions = async () => {
      try {
        const response = await jobPositionAPI.getAllPositions()
        console.log('职位数据:', response)
        jobPositions.value = response || []
      } catch (error) {
        console.error('加载职位列表失败:', error)
        ElMessage.error('加载职位列表失败，请稍后重试')
        // 添加模拟数据用于测试
        jobPositions.value = [
          {
            id: 1,
            name: '前端工程师',
            field: 'Web开发',
            type: '全职',
            required_skills: 'JavaScript, Vue, React',
            description: '负责Web应用前端开发'
          },
          {
            id: 2,
            name: '后端工程师',
            field: '服务端开发',
            type: '全职',
            required_skills: 'Python, FastAPI, Django',
            description: '负责后端API和服务开发'
          }
        ]
      }
    }

    // 加载用户统计
    const loadUserStats = async () => {
      try {
        const stats = await interviewSessionAPI.getUserStats()
        userStats.value = stats
      } catch (error) {
        console.error('加载用户统计失败:', error)
        // 添加模拟数据用于测试
        userStats.value = {
          total_sessions: 0,
          average_score: 0,
          average_duration: 0,
          completion_rate: 0
        }
      }
    }

    // 职位选择变化
    const onJobPositionChange = () => {
      if (selectedPosition.value) {
        // 根据职位自动设置面试标题
        if (!form.title) {
          form.title = `${selectedPosition.value.name}面试练习`
        }
      }
    }

    // 创建面试
    const createInterview = async () => {
      if (!form.job_position_id) {
        ElMessage.warning('请选择目标职位')
        return
      }

      loading.value = true
      try {
        const session = await interviewSessionAPI.createSession(form)
        ElMessage.success('面试创建成功，即将开始')
        
        // 跳转到面试页面
        router.push({
          name: 'interview-session',
          params: { id: session.id }
        })
      } catch (error) {
        console.error('创建面试失败:', error)
        ElMessage.error(error.response?.data?.detail || '创建面试失败，请稍后重试')
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadJobPositions()
      loadUserStats()
    })

    return {
      form,
      loading,
      jobPositions,
      userStats,
      selectedPosition,
      onJobPositionChange,
      createInterview
    }
  }
}
</script>

<style scoped>
.interview-practice {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem 0;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
  color: white;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.page-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
}

.practice-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
}

/* 配置区域 */
.config-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #4a5568;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group.half {
  flex: 1;
}

/* 复选框样式 */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  margin-top: 1.5rem;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
}

/* 职位详情 */
.position-details {
  background: #f7fafc;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.position-details h4 {
  margin: 0 0 0.75rem 0;
  color: #2d3748;
  font-size: 1rem;
}

.detail-item {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #4a5568;
}

.detail-item strong {
  color: #2d3748;
}

/* 按钮 */
.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  flex: 1;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #cbd5e0;
}

/* 信息区域 */
.info-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-card,
.stats-card,
.domains-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 功能特色 */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.feature-item i {
  color: #667eea;
  font-size: 1.25rem;
  margin-top: 0.25rem;
}

.feature-item h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  color: #2d3748;
}

.feature-item p {
  margin: 0;
  font-size: 0.9rem;
  color: #718096;
  line-height: 1.4;
}

/* 统计数据 */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.8rem;
  color: #718096;
  font-weight: 500;
}

/* 技术领域 */
.domains-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.domain-tag {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  text-align: center;
  justify-content: center;
}

.domain-tag.ai {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.domain-tag.bigdata {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
}

.domain-tag.iot {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: white;
}

.domain-tag.system {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  color: #2d3748;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .practice-container {
    grid-template-columns: 1fr;
    padding: 0 1rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .domains-list {
    grid-template-columns: 1fr;
  }
}
</style>