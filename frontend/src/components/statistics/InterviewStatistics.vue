<template>
  <div class="interview-statistics">
    <el-card class="statistics-card">
      <template #header>
        <div class="card-header">
          <h3>面试统计</h3>
          <el-button type="primary" link @click="refresh">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="hasInterviews" class="statistics-content">
        <el-row :gutter="20">
          <el-col :span="8" class="statistics-number">
            <div class="stat-icon">
              <InterviewIcon />
            </div>
            <div class="stat-info">
              <div class="stat-label">面试总数</div>
              <div class="stat-value">{{ stats.total }}</div>
            </div>
          </el-col>
          
          <el-col :span="8" class="statistics-number">
            <div class="stat-icon">
              <AverageIcon />
            </div>
            <div class="stat-info">
              <div class="stat-label">平均分数</div>
              <div class="stat-value">{{ stats.averageScore.toFixed(1) }}</div>
            </div>
          </el-col>
          
          <el-col :span="8" class="statistics-number">
            <div class="stat-icon">
              <TopScoreIcon />
            </div>
            <div class="stat-info">
              <div class="stat-label">最高分数</div>
              <div class="stat-value">{{ stats.highestScore.toFixed(1) }}</div>
            </div>
          </el-col>
        </el-row>
        
        <el-divider />
        
        <div class="chart-section">
          <h4>分数分布</h4>
          <div class="chart-container">
            <pie-chart 
              :chart-data="scoreDistribution" 
              :is-empty="!hasInterviews" 
              empty-text="暂无面试数据"
              height="240px"
            />
          </div>
        </div>
        
        <div class="recent-interviews">
          <h4>最近面试</h4>
          <el-table 
            :data="recentInterviews" 
            style="width: 100%"
            :header-cell-style="{background: '#f7f9fc'}"
          >
            <el-table-column prop="date" label="日期" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.date) }}
              </template>
            </el-table-column>
            <el-table-column prop="position" label="岗位" width="180" />
            <el-table-column prop="score" label="得分" width="100">
              <template #default="scope">
                <el-tag :type="getScoreTag(scope.row.score)">
                  {{ scope.row.score.toFixed(1) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="操作">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  link 
                  size="small" 
                  @click="viewReport(scope.row.id)"
                >
                  查看报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="view-all-button">
            <el-button type="primary" plain @click="viewAllReports">查看全部面试</el-button>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <div class="empty-icon">
          <EmptyDataIcon />
        </div>
        <h3>暂无面试记录</h3>
        <p>您还没有进行过任何面试，开始您的第一次面试体验吧！</p>
        <el-button type="primary" @click="startNewInterview">开始面试</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { interviewSessionAPI } from '../../api/interviewSession'
import PieChart from '../charts/PieChart.vue'
import { ElMessage } from 'element-plus'

// SVG图标组件定义
const InterviewIcon = {
  render() {
    return h('svg', {
      class: 'icon',
      viewBox: '0 0 1024 1024',
      width: '24',
      height: '24'
    }, [
      h('path', {
        d: 'M832 64H192c-52.928 0-96 43.072-96 96v704c0 52.928 43.072 96 96 96h640c52.928 0 96-43.072 96-96V160c0-52.928-43.072-96-96-96z',
        fill: '#E6F3FF'
      }),
      h('path', {
        d: 'M832 96a64 64 0 0 1 64 64v704a64 64 0 0 1-64 64H192a64 64 0 0 1-64-64V160a64 64 0 0 1 64-64h640m0-32H192c-52.928 0-96 43.072-96 96v704c0 52.928 43.072 96 96 96h640c52.928 0 96-43.072 96-96V160c0-52.928-43.072-96-96-96z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M256 448a32 32 0 0 1 0-64h320a32 32 0 0 1 0 64H256zM256 576a32 32 0 0 1 0-64h192a32 32 0 0 1 0 64H256zM256 704a32 32 0 0 1 0-64h320a32 32 0 0 1 0 64H256z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M640 192a96 96 0 1 1-192 0 96 96 0 0 1 192 0z',
        fill: '#1890FF'
      }),
      h('path', {
        d: 'M544 320c-70.692 0-128-57.308-128-128s57.308-128 128-128 128 57.308 128 128-57.308 128-128 128z m0-224c-52.936 0-96 43.064-96 96s43.064 96 96 96 96-43.064 96-96-43.064-96-96-96z',
        fill: '#003366'
      })
    ])
  }
}

const AverageIcon = {
  render() {
    return h('svg', {
      class: 'icon',
      viewBox: '0 0 1024 1024',
      width: '24',
      height: '24'
    }, [
      h('path', {
        d: 'M917.333333 853.333333H106.666667c-23.466667 0-42.666667-19.2-42.666667-42.666666V213.333333c0-23.466667 19.2-42.666667 42.666667-42.666666h810.666666c23.466667 0 42.666667 19.2 42.666667 42.666666v597.333334c0 23.466667-19.2 42.666667-42.666667 42.666666z',
        fill: '#E6F3FF'
      }),
      h('path', {
        d: 'M917.333333 853.333333H106.666667c-23.466667 0-42.666667-19.2-42.666667-42.666666V213.333333c0-23.466667 19.2-42.666667 42.666667-42.666666h810.666666c23.466667 0 42.666667 19.2 42.666667 42.666666v597.333334c0 23.466667-19.2 42.666667-42.666667 42.666666z',
        stroke: '#003366',
        'stroke-width': '32'
      }),
      h('path', {
        d: 'M832 597.333333h-85.333333a21.333333 21.333333 0 0 1-21.333334-21.333333v-128a21.333333 21.333333 0 0 1 21.333334-21.333333h85.333333a21.333333 21.333333 0 0 1 21.333333 21.333333v128a21.333333 21.333333 0 0 1-21.333333 21.333333zM640 597.333333h-85.333333a21.333333 21.333333 0 0 1-21.333334-21.333333V341.333333a21.333333 21.333333 0 0 1 21.333334-21.333333h85.333333a21.333333 21.333333 0 0 1 21.333333 21.333333v234.666667a21.333333 21.333333 0 0 1-21.333333 21.333333zM448 597.333333h-85.333333a21.333333 21.333333 0 0 1-21.333334-21.333333v-106.666667a21.333333 21.333333 0 0 1 21.333334-21.333333h85.333333a21.333333 21.333333 0 0 1 21.333333 21.333333v106.666667a21.333333 21.333333 0 0 1-21.333333 21.333333zM256 597.333333h-85.333333a21.333333 21.333333 0 0 1-21.333334-21.333333V405.333333a21.333333 21.333333 0 0 1 21.333334-21.333333h85.333333a21.333333 21.333333 0 0 1 21.333333 21.333333v170.666667a21.333333 21.333333 0 0 1-21.333333 21.333333z',
        fill: '#1890FF'
      }),
      h('path', {
        d: 'M810.666667 704H213.333333a21.333333 21.333333 0 0 1 0-42.666667h597.333334a21.333333 21.333333 0 0 1 0 42.666667z',
        fill: '#003366'
      })
    ])
  }
}

const TopScoreIcon = {
  render() {
    return h('svg', {
      class: 'icon',
      viewBox: '0 0 1024 1024',
      width: '24',
      height: '24'
    }, [
      h('path', {
        d: 'M512 853.333333c-188.522667 0-341.333333-152.810667-341.333333-341.333333S323.477333 170.666667 512 170.666667s341.333333 152.810667 341.333333 341.333333-152.810667 341.333333-341.333333 341.333333z',
        fill: '#E6F3FF'
      }),
      h('path', {
        d: 'M512 192a320 320 0 1 1 0 640 320 320 0 0 1 0-640m0-42.666667c-200.298667 0-362.666667 162.368-362.666667 362.666667s162.368 362.666667 362.666667 362.666667 362.666667-162.368 362.666667-362.666667-162.368-362.666667-362.666667-362.666667z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M512 320L442.624 459.648 288 480l112 109.248L376.192 744 512 680.448 647.808 744 624 589.248 736 480l-154.624-20.352z',
        fill: '#1890FF'
      })
    ])
  }
}

const EmptyDataIcon = {
  render() {
    return h('svg', {
      class: 'icon',
      viewBox: '0 0 1024 1024',
      width: '80',
      height: '80'
    }, [
      h('path', {
        d: 'M512 226C335.3 226 192 369.3 192 546s143.3 320 320 320 320-143.3 320-320S688.7 226 512 226z',
        fill: '#E6F3FF'
      }),
      h('path', {
        d: 'M512 866c-176.7 0-320-143.3-320-320s143.3-320 320-320 320 143.3 320 320-143.3 320-320 320z m0-600c-154.6 0-280 125.4-280 280s125.4 280 280 280 280-125.4 280-280-125.4-280-280-280z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M368 502.4c20.6 0 37.2-16.6 37.2-37.2 0-20.6-16.6-37.2-37.2-37.2-20.6 0-37.2 16.6-37.2 37.2 0 20.6 16.6 37.2 37.2 37.2zM656 502.4c20.6 0 37.2-16.6 37.2-37.2 0-20.6-16.6-37.2-37.2-37.2-20.6 0-37.2 16.6-37.2 37.2 0 20.6 16.6 37.2 37.2 37.2z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M512 693.6c61.5 0 114-48.3 129.9-112H382.1c15.9 63.7 68.4 112 129.9 112z',
        fill: '#003366'
      }),
      h('path', {
        d: 'M169.6 258.6l684.8 506.8',
        stroke: '#003366',
        'stroke-width': '36',
        'stroke-linecap': 'round'
      })
    ])
  }
}

// 路由
const router = useRouter()

// 数据
const loading = ref(false)
const stats = ref({
  total: 0,
  averageScore: 0,
  highestScore: 0,
  scoreDistribution: {
    excellent: 0,
    good: 0,
    average: 0,
    poor: 0
  }
})
const recentInterviews = ref([])

// 计算属性
const hasInterviews = computed(() => stats.value.total > 0)

// 饼图数据
const scoreDistribution = computed(() => {
  const { excellent, good, average, poor } = stats.value.scoreDistribution
  
  return {
    title: '分数分布',
    data: [
      { value: excellent, name: '优秀 (8-10分)', itemStyle: { color: '#52c41a' } },
      { value: good, name: '良好 (6-8分)', itemStyle: { color: '#1890ff' } },
      { value: average, name: '一般 (4-6分)', itemStyle: { color: '#faad14' } },
      { value: poor, name: '需改进 (0-4分)', itemStyle: { color: '#f5222d' } }
    ],
    legend: ['优秀 (8-10分)', '良好 (6-8分)', '一般 (4-6分)', '需改进 (0-4分)']
  }
})

// 获取统计数据
const fetchStatistics = async () => {
  loading.value = true
  try {
    const result = await interviewSessionAPI.getStatistics()
    stats.value = result
    loading.value = false
  } catch (error) {
    console.error('获取面试统计数据失败:', error)
    ElMessage.warning('获取统计信息失败，将显示默认数据')
    stats.value = {
      total: 0,
      averageScore: 0,
      highestScore: 0,
      scoreDistribution: {
        excellent: 0,
        good: 0,
        average: 0,
        poor: 0
      }
    }
    loading.value = false
  }
}

// 获取最近面试记录
const fetchRecentInterviews = async () => {
  try {
    const result = await interviewSessionAPI.getRecent(5) // 获取最近5条
    recentInterviews.value = result
  } catch (error) {
    console.error('获取最近面试记录失败:', error)
    recentInterviews.value = []
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 根据分数获取标签类型
const getScoreTag = (score) => {
  if (score >= 8) return 'success'
  if (score >= 6) return 'primary'
  if (score >= 4) return 'warning'
  return 'danger'
}

// 查看报告
const viewReport = (id) => {
  router.push(`/interview-report/${id}`)
}

// 查看全部报告
const viewAllReports = () => {
  router.push('/practice-history')
}

// 开始新面试
const startNewInterview = () => {
  router.push('/interview-practice')
}

// 刷新数据
const refresh = () => {
  fetchStatistics()
  fetchRecentInterviews()
}

// 页面加载时获取数据
onMounted(() => {
  fetchStatistics()
  fetchRecentInterviews()
})
</script>

<style scoped>
.interview-statistics {
  margin-bottom: 20px;
}

.statistics-card {
  background-color: var(--bg-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.loading-container {
  padding: 20px;
}

.statistics-content {
  padding: 10px 0;
}

.statistics-number {
  display: flex;
  align-items: center;
  padding: 10px;
  text-align: center;
}

.stat-icon {
  background-color: var(--bg-tertiary);
  border-radius: 50%;
  height: 50px;
  width: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 12px;
}

.stat-info {
  text-align: left;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-section {
  margin: 20px 0;
}

.chart-section h4 {
  margin-bottom: 10px;
  font-size: 16px;
  color: var(--text-primary);
}

.chart-container {
  width: 100%;
  height: 240px;
}

.recent-interviews {
  margin: 20px 0 10px;
}

.recent-interviews h4 {
  margin-bottom: 10px;
  font-size: 16px;
  color: var(--text-primary);
}

.view-all-button {
  display: flex;
  justify-content: center;
  margin: 20px 0 10px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.7;
}

.empty-state h3 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  max-width: 300px;
}
</style> 