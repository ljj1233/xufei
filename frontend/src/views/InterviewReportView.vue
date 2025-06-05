<template>
  <div class="interview-report-container">
    <h1>面试报告详情</h1>
    <el-card v-if="report" class="report-card">
      <template #header>
        <div class="card-header">
          <h2>面试ID: {{ sessionId }}</h2>
          <span>{{ formatDate(report.createdAt) }}</span>
        </div>
      </template>

      <div class="report-content">
        <el-row :gutter="20">
          <el-col :span="24">
            <h3>总体评分</h3>
            <el-progress
              :percentage="report.overallScore * 10"
              :format="format => `${report.overallScore}/10`"
              :color="getScoreColor(report.overallScore)"
            ></el-progress>
          </el-col>
        </el-row>

        <el-divider></el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <h3>能力雷达图</h3>
            <div class="chart-container">
              <RadarChart :chart-data="radarChartData" :options="radarChartOptions" />
            </div>
          </el-col>
          <el-col :span="12">
            <h3>评分详情</h3>
            <div v-for="(score, category) in report.scores" :key="category" class="score-item">
              <span class="category-name">{{ getCategoryDisplayName(category) }}</span>
              <el-progress
                :percentage="score * 10"
                :format="format => `${score}/10`"
                :color="getScoreColor(score)"
              ></el-progress>
            </div>
          </el-col>
        </el-row>

        <el-divider></el-divider>

        <el-row>
          <el-col :span="24">
            <h3>面试问题与回答</h3>
            <el-timeline>
              <el-timeline-item
                v-for="(qa, index) in report.qaList"
                :key="index"
                :type="qa.type === 'question' ? 'primary' : 'success'"
                :icon="qa.type === 'question' ? 'QuestionFilled' : 'ChatDotRound'"
              >
                <h4>{{ qa.type === 'question' ? '面试官' : '你' }}</h4>
                <p>{{ qa.content }}</p>
                <div v-if="qa.type === 'answer' && qa.feedback" class="answer-feedback">
                  <h5>回答点评：</h5>
                  <p>{{ qa.feedback }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-col>
        </el-row>

        <el-divider></el-divider>

        <el-row>
          <el-col :span="24">
            <h3>总体评价与建议</h3>
            <el-card class="feedback-card">
              <div v-html="report.overallFeedback"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-skeleton v-else :rows="10" animated />

    <div class="actions">
      <el-button type="primary" @click="router.push('/interview-practice')">再次练习</el-button>
      <el-button @click="router.push('/practice-history')">返回练习记录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import RadarChart from '../components/charts/RadarChart.vue'
import { interviewSessionAPI } from '../api/interviewSession'

// 获取路由参数
const route = useRoute()
const router = useRouter()
const sessionId = route.params.sessionId
const report = ref(null)
const isLoading = ref(true)

// 从API获取报告数据
onMounted(async () => {
  try {
    isLoading.value = true
    // 调用API获取报告数据
    const result = await interviewSessionAPI.getReport(sessionId)
    report.value = result
    isLoading.value = false
  } catch (error) {
    console.error('获取报告失败:', error)
    
    // 处理不同类型的错误
    if (error.response) {
      if (error.response.status === 403) {
        ElMessage.warning('您没有权限查看此报告')
      } else if (error.response.status === 404) {
        ElMessage.warning('报告不存在或已被删除')
      } else {
        ElMessage.error('获取报告失败：' + (error.response.data?.detail || '服务器错误'))
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else {
      ElMessage.error('获取报告失败：' + (error.message || '未知错误'))
    }
    
    isLoading.value = false
  }
})

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 获取分数颜色
const getScoreColor = (score) => {
  if (score >= 8) return '#67C23A'
  if (score >= 6) return '#E6A23C'
  return '#F56C6C'
}

// 类别名称映射
const getCategoryDisplayName = (category) => {
  const map = {
    professionalKnowledge: '专业知识',
    communicationSkills: '沟通能力',
    problemSolving: '解决问题',
    attitudeAndPotential: '态度与潜力',
    culturalFit: '文化契合度'
  }
  return map[category] || category
}

// 雷达图数据
const radarChartData = computed(() => {
  if (!report.value) return { labels: [], datasets: [] }
  
  const labels = Object.keys(report.value.scores).map(key => getCategoryDisplayName(key))
  const data = Object.values(report.value.scores)
  
  return {
    labels,
    datasets: [
      {
        label: '能力评分',
        data,
        backgroundColor: 'rgba(30, 136, 229, 0.2)',
        borderColor: 'rgba(30, 136, 229, 0.8)',
        pointBackgroundColor: 'rgba(30, 136, 229, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(30, 136, 229, 1)'
      }
    ]
  }
})

// 雷达图配置
const radarChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      angleLines: {
        display: true
      },
      suggestedMin: 0,
      suggestedMax: 10
    }
  }
}
</script>

<style scoped>
.interview-report-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  margin-bottom: 20px;
}

.score-item {
  margin-bottom: 15px;
}

.category-name {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.answer-feedback {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border-left: 3px solid #1E88E5;
  border-radius: 4px;
}

.answer-feedback h5 {
  margin-top: 0;
  color: #1E88E5;
}

.feedback-card {
  background-color: #f8f9fa;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}
</style> 