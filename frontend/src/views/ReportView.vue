<template>
  <div class="report-container">
    <el-card class="report-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>面试评估报告</h2>
          <el-button @click="$router.push('/results')" type="primary" plain>返回列表</el-button>
        </div>
      </template>
      
      <div v-if="!loading && report">
        <div class="report-header">
          <h3>{{ report.title || '面试报告' }}</h3>
          <p class="report-time">创建时间: {{ formatDate(report.created_at) }}</p>
        </div>
        
        <el-divider content-position="center">综合评分</el-divider>
        
        <div class="score-section">
          <div class="overall-score">
            <el-progress type="dashboard" :percentage="report.overall_score * 10" :color="scoreColor" :width="120">
              <template #default="{ percentage }">
                <span class="progress-value">{{ (percentage / 10).toFixed(1) }}</span>
                <span class="progress-label">总分</span>
              </template>
            </el-progress>
          </div>
          
          <div class="detail-scores">
            <div class="score-item">
              <span class="score-label">内容评分</span>
              <el-progress :percentage="report.content_score * 10" :color="scoreColor" :show-text="false" />
              <span class="score-value">{{ report.content_score.toFixed(1) }}</span>
            </div>
            
            <div class="score-item">
              <span class="score-label">语音评分</span>
              <el-progress :percentage="report.speech_score * 10" :color="scoreColor" :show-text="false" />
              <span class="score-value">{{ report.speech_score.toFixed(1) }}</span>
            </div>
            
            <div class="score-item">
              <span class="score-label">视觉评分</span>
              <el-progress :percentage="report.visual_score * 10" :color="scoreColor" :show-text="false" />
              <span class="score-value">{{ report.visual_score.toFixed(1) }}</span>
            </div>
          </div>
        </div>
        
        <el-divider content-position="center">评估详情</el-divider>
        
        <div class="analysis-section">
          <el-tabs type="border-card">
            <el-tab-pane label="优势">
              <ul class="analysis-list">
                <li v-for="(item, index) in report.strengths" :key="'strength-'+index">
                  {{ item }}
                </li>
              </ul>
            </el-tab-pane>
            
            <el-tab-pane label="不足">
              <ul class="analysis-list">
                <li v-for="(item, index) in report.weaknesses" :key="'weakness-'+index">
                  {{ item }}
                </li>
              </ul>
            </el-tab-pane>
            
            <el-tab-pane label="建议">
              <ul class="analysis-list">
                <li v-for="(item, index) in report.suggestions" :key="'suggestion-'+index">
                  {{ item }}
                </li>
              </ul>
            </el-tab-pane>
            
            <el-tab-pane label="详细分析">
              <div class="detailed-analysis">
                <h4>内容分析</h4>
                <p>{{ report.content_analysis || '暂无详细内容分析' }}</p>
                
                <h4>语音分析</h4>
                <p>{{ report.speech_analysis || '暂无详细语音分析' }}</p>
                
                <h4>视觉分析</h4>
                <p>{{ report.visual_analysis || '暂无详细视觉分析' }}</p>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const report = ref(null)
const loading = ref(true)

// 获取报告ID
const reportId = computed(() => route.params.id)

// 评分颜色计算
const scoreColor = (percentage) => {
  if (percentage < 40) return '#F56C6C'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取报告详情
const fetchReport = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/api/interviews/${reportId.value}`)
    report.value = response.data
  } catch (error) {
    console.error('获取报告详情失败:', error)
    ElMessage.error('获取报告详情失败，请稍后重试')
    router.push('/results')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (reportId.value) {
    fetchReport()
  } else {
    ElMessage.error('报告ID无效')
    router.push('/results')
  }
})
</script>

<style scoped>
.report-container {
  padding: 20px;
}

.report-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
}

.report-time {
  color: #909399;
  font-size: 14px;
}

.score-section {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 30px 0;
  flex-wrap: wrap;
}

.overall-score {
  text-align: center;
  margin-bottom: 20px;
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

.detail-scores {
  flex: 1;
  min-width: 300px;
  max-width: 500px;
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

.analysis-list {
  padding-left: 20px;
}

.analysis-list li {
  margin-bottom: 10px;
  line-height: 1.6;
}

.detailed-analysis h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #303133;
}

.detailed-analysis p {
  line-height: 1.6;
  color: #606266;
  white-space: pre-line;
}

@media (max-width: 768px) {
  .score-section {
    flex-direction: column;
  }
  
  .detail-scores {
    width: 100%;
    margin-top: 20px;
  }
}
</style>