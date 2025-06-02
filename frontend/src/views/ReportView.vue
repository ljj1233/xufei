<template>
  <div class="report-container">
    <el-card class="report-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>面试评估报告</h2>
          <div class="header-actions">
            <el-button @click="shareReport" type="success" plain>
              <el-icon><Share /></el-icon>分享
            </el-button>
            <el-button @click="$router.push('/results')" type="primary" plain>返回列表</el-button>
          </div>
        </div>
      </template>
      
      <div v-if="!loading && report">
        <div class="report-header">
          <h3>{{ report.title || '面试报告' }}</h3>
          <p class="report-time">创建时间: {{ formatDate(report.created_at) }}</p>
        </div>
        
        <div class="report-summary">
          <div class="summary-text">
            <p class="summary-intro">
              <EmotionIcons :type="getScoreEmotionType(report.overall_score)" :showText="false" />
              <span>{{ getScoreSummary(report.overall_score) }}</span>
            </p>
          </div>
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
        
        <el-divider content-position="center">能力雷达图</el-divider>
        
        <div class="chart-section">
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <div class="chart-card">
                <h4>内容能力</h4>
                <SkillRadarChart :data="contentSkillData" />
              </div>
            </el-col>
            <el-col :xs="24" :md="12">
              <div class="chart-card">
                <h4>表达能力</h4>
                <SkillRadarChart :data="expressionSkillData" />
              </div>
            </el-col>
          </el-row>
        </div>
        
        <el-divider content-position="center">评估详情</el-divider>
        
        <div class="analysis-section">
          <el-tabs type="border-card">
            <el-tab-pane label="优势">
              <div class="tab-header">
                <EmotionIcons type="excellent" />
                <h4>您的优势</h4>
              </div>
              <ul class="analysis-list">
                <li v-for="(item, index) in report.strengths" :key="'strength-'+index">
                  {{ item }}
                </li>
              </ul>
            </el-tab-pane>
            
            <el-tab-pane label="不足">
              <div class="tab-header">
                <EmotionIcons type="needsImprovement" />
                <h4>需要改进的地方</h4>
              </div>
              <ul class="analysis-list">
                <li v-for="(item, index) in report.weaknesses" :key="'weakness-'+index">
                  {{ item }}
                </li>
              </ul>
            </el-tab-pane>
            
            <el-tab-pane label="建议">
              <div class="tab-header">
                <EmotionIcons type="tip" />
                <h4>改进建议</h4>
              </div>
              <ul class="analysis-list">
                <li v-for="(item, index) in report.suggestions" :key="'suggestion-'+index">
                  {{ item }}
                </li>
              </ul>
              
              <div class="action-tips">
                <TipCard title="行动建议" important>
                  <p>尝试按照以上建议进行练习，然后再次上传面试视频，看看您的表现是否有所提升！</p>
                  <template #actions>
                    <el-button type="primary" @click="$router.push('/upload')">开始练习</el-button>
                  </template>
                </TipCard>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="详细分析">
              <div class="detailed-analysis">
                <div class="analysis-section-item">
                  <h4>内容分析</h4>
                  <p>{{ report.content_analysis || '暂无详细内容分析' }}</p>
                </div>
                
                <div class="analysis-section-item">
                  <h4>语音分析</h4>
                  <p>{{ report.speech_analysis || '暂无详细语音分析' }}</p>
                </div>
                
                <div class="analysis-section-item">
                  <h4>视觉分析</h4>
                  <p>{{ report.visual_analysis || '暂无详细视觉分析' }}</p>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
        
        <div class="report-actions">
          <el-button type="primary" @click="$router.push('/upload')">继续练习</el-button>
          <el-button @click="downloadReport">下载报告</el-button>
        </div>
      </div>
      
      <div v-if="!loading && !report" class="no-data">
        <el-empty description="未找到报告数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Share } from '@element-plus/icons-vue'
import axios from 'axios'
import EmotionIcons from '../components/EmotionIcons.vue'
import TipCard from '../components/TipCard.vue'
import SkillRadarChart from '../components/SkillRadarChart.vue'

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

// 获取评分对应的情感类型
const getScoreEmotionType = (score) => {
  if (score >= 8) return 'excellent'
  if (score >= 6) return 'good'
  if (score >= 4) return 'average'
  return 'needsImprovement'
}

// 获取评分总结
const getScoreSummary = (score) => {
  if (score >= 8) return '恭喜您！您的面试表现非常出色，展现了很强的专业能力和沟通技巧。'
  if (score >= 6) return '不错的表现！您的面试整体良好，有一些亮点，也有一些可以改进的地方。'
  if (score >= 4) return '您的面试表现一般，有一些基本要点，但还需要在多个方面加强。'
  return '您的面试需要显著改进，请关注我们提供的建议来提升您的表现。'
}

// 内容能力数据
const contentSkillData = computed(() => {
  if (!report.value) return []
  
  return [
    { name: '专业知识', value: report.value.content_knowledge || 5 },
    { name: '逻辑思维', value: report.value.content_logic || 5 },
    { name: '问题解决', value: report.value.content_problem_solving || 5 },
    { name: '创新思维', value: report.value.content_innovation || 5 },
    { name: '行业理解', value: report.value.content_industry || 5 }
  ]
})

// 表达能力数据
const expressionSkillData = computed(() => {
  if (!report.value) return []
  
  return [
    { name: '语音清晰度', value: report.value.speech_clarity || 5 },
    { name: '语速控制', value: report.value.speech_pace || 5 },
    { name: '肢体语言', value: report.value.visual_body_language || 5 },
    { name: '眼神接触', value: report.value.visual_eye_contact || 5 },
    { name: '情感表达', value: report.value.speech_emotion || 5 }
  ]
})

// 获取报告详情
const fetchReport = async () => {
  loading.value = true
  try {
    // 模拟API调用
    // const response = await axios.get(`/api/interviews/${reportId.value}`)
    // report.value = response.data
    
    // 模拟数据
    setTimeout(() => {
      report.value = {
        id: reportId.value,
        title: '产品经理面试 - 某科技公司',
        created_at: new Date().toISOString(),
        overall_score: 7.5,
        content_score: 8.0,
        speech_score: 7.0,
        visual_score: 7.5,
        strengths: [
          '对产品开发流程有清晰的理解和丰富的经验',
          '能够清晰地表达产品理念和设计思路',
          '展示了良好的团队协作意识和沟通能力',
          '对用户需求分析方法有深入理解'
        ],
        weaknesses: [
          '在讨论技术实现细节时不够自信',
          '对某些市场趋势的分析不够深入',
          '回答问题时偶尔语速过快',
          '在压力情境下的表现可以进一步提升'
        ],
        suggestions: [
          '加强对技术领域的了解，提高与开发团队沟通的信心',
          '定期关注行业动态，深入分析市场趋势',
          '练习控制语速，特别是在讨论复杂概念时',
          '多进行模拟面试，提高压力情境下的表现'
        ],
        content_analysis: '候选人在产品管理方面展示了扎实的基础知识，能够清晰地描述产品生命周期和用户需求挖掘方法。对产品设计理念的阐述有深度，但在讨论技术实现方案时略显不足。市场分析能力中等，可以进一步加强对竞品分析的深度。',
        speech_analysis: '语音清晰度良好，发音准确，但语速偏快，特别是在讨论自己熟悉的话题时。语调变化适中，能够有效传达重点信息。在回答压力问题时，语音节奏略显紧张，可以通过深呼吸来改善。',
        visual_analysis: '面部表情自然，眼神接触良好，展示了自信和诚恳。肢体语言适度，手势辅助表达效果良好。坐姿端正，整体形象专业。在讨论不熟悉话题时，身体语言略显紧张，可以通过放松肩膀来改善。',
        
        // 详细能力评分
        content_knowledge: 8.5,
        content_logic: 7.8,
        content_problem_solving: 8.2,
        content_innovation: 7.0,
        content_industry: 7.5,
        
        speech_clarity: 8.0,
        speech_pace: 6.5,
        speech_emotion: 7.2,
        
        visual_body_language: 7.5,
        visual_eye_contact: 8.0
      }
      loading.value = false
    }, 1000)
  } catch (error) {
    console.error('获取报告详情失败:', error)
    ElMessage.error('获取报告详情失败，请稍后重试')
    router.push('/results')
  }
}

// 分享报告
const shareReport = () => {
  ElMessage.success('分享链接已复制到剪贴板')
}

// 下载报告
const downloadReport = () => {
  ElMessage.success('报告下载中...')
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
  max-width: 1200px;
  margin: 0 auto;
}

.report-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
}

.report-time {
  color: #909399;
  font-size: 14px;
}

.report-summary {
  background-color: #f0f8ff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  text-align: center;
}

.summary-intro {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 16px;
  color: #303133;
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

.chart-section {
  margin: 30px 0;
}

.chart-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-card h4 {
  text-align: center;
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}

.tab-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.tab-header h4 {
  margin: 0;
  color: #303133;
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

.analysis-section-item {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px dashed #ebeef5;
}

.analysis-section-item:last-child {
  border-bottom: none;
}

.action-tips {
  margin-top: 30px;
}

.report-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;
}

.no-data {
  padding: 40px 0;
  text-align: center;
}

@media (max-width: 768px) {
  .score-section {
    flex-direction: column;
  }
  
  .detail-scores {
    width: 100%;
  }
}
</style>