<template>
  <div class="practice-history-container">
    <h1>我的练习记录</h1>
    
    <!-- 开发环境提示 -->
    <el-alert
      v-if="isDevelopment"
      type="info"
      :closable="false"
      show-icon
      title="开发环境提示"
      description="当前处于开发环境，可能显示模拟数据。生产环境将显示实际用户数据。"
      class="env-notice"
    />
    
    <div class="filter-section">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索面试记录"
        class="search-input"
        clearable
        prefix-icon="Search"
      />
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        class="date-picker"
      />
      <el-button type="primary" @click="filterRecords">筛选</el-button>
    </div>
    
    <el-card class="stat-card" v-if="!isLoading && practiceRecords.length > 0">
      <div class="stats-header">
        <h3>练习统计</h3>
      </div>
      <div class="stats-content">
        <div class="stat-item">
          <div class="stat-value">{{ totalRecords }}</div>
          <div class="stat-label">总练习次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ practiceRecords.length > 0 ? Math.round(practiceRecords.reduce((sum, record) => sum + (record.duration || 0), 0) / 60 / practiceRecords.length) : 0 }}</div>
          <div class="stat-label">平均时长(分钟)</div>
        </div>
        <div class="stat-item" v-if="practiceRecords.some(r => r.overallScore && r.overallScore !== '未评分')">
          <div class="stat-value">{{ 
            practiceRecords
              .filter(r => r.overallScore && r.overallScore !== '未评分')
              .reduce((max, r) => Math.max(max, parseFloat(r.overallScore)), 0)
              .toFixed(1) 
          }}</div>
          <div class="stat-label">最高分数</div>
        </div>
      </div>
    </el-card>
    
    <el-table
      v-loading="isLoading"
      :data="filteredPracticeRecords"
      style="width: 100%"
      border
      stripe
      :empty-text="isLoading ? '加载中...' : '暂无练习记录'"
    >
      <el-table-column label="序号" type="index" width="80" align="center" />
      <el-table-column prop="sessionName" label="练习名称" min-width="180">
        <template #default="{ row }">
          <span class="practice-name">{{ row.sessionName || '未命名练习' }}</span>
          <el-tag size="small" :type="getPositionTagType(row.position)" effect="light">{{ getPositionDisplay(row.position) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="练习时间" width="180" sortable>
        <template #default="{ row }">
          {{ formatDate(row.createdAt) }}
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="时长" width="100" sortable>
        <template #default="{ row }">
          {{ formatDuration(row.duration) }}
        </template>
      </el-table-column>
      <el-table-column prop="questionCount" label="问题数" width="100" sortable align="center" />
      <el-table-column prop="overallScore" label="总分" width="100" sortable align="center">
        <template #default="{ row }">
          <span :class="getScoreClass(row.overallScore)">{{ row.overallScore }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="240" align="center" fixed="right">
        <template #default="{ row }">
          <div class="button-group">
            <el-button type="primary" size="small" @click="viewReport(row.id)">
              <el-icon><Document /></el-icon> 
              查看报告
            </el-button>
            <el-button type="info" size="small" @click="viewRecording(row.id)">
              <el-icon><VideoPlay /></el-icon>
              查看录像
            </el-button>
            <el-button type="danger" size="small" @click="confirmDelete(row.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 没有记录时的提示 -->
    <el-empty 
      v-if="!isLoading && filteredPracticeRecords.length === 0"
      description="暂无练习记录"
    >
      <el-button type="primary" @click="router.push('/interview-practice')">开始练习</el-button>
    </el-empty>

    <div class="pagination-container" v-if="totalRecords > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalRecords"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <el-dialog v-model="deleteDialogVisible" title="删除确认" width="30%">
      <p>确定要删除这条练习记录吗？删除后无法恢复。</p>
      <template #footer>
        <span>
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="deletePractice">确定删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, VideoPlay, Delete } from '@element-plus/icons-vue'
import { interviewSessionAPI } from '../api/interviewSession'
import { useUserStore } from '../stores/user'
import { CONFIG } from '../config'

const router = useRouter()
const userStore = useUserStore()
const practiceRecords = ref([])
const isLoading = ref(true)
const currentPage = ref(1)
const pageSize = ref(10)
const totalRecords = ref(0)
const searchKeyword = ref('')
const dateRange = ref([])
const deleteDialogVisible = ref(false)
const recordToDelete = ref(null)
const isDevelopment = CONFIG.isDevelopment

// 获取用户个人练习记录
onMounted(async () => {
  await fetchPracticeRecords()
})

// 获取个人练习记录
const fetchPracticeRecords = async () => {
  try {
    isLoading.value = true
    console.log('开始获取面试记录...')
    
    // 调用API获取用户个人练习记录
    const response = await interviewSessionAPI.getSessions({
      page: currentPage.value,
      limit: pageSize.value
    })
    
    console.log('API返回数据:', response)
    
    // 清空备用数据，确保使用API返回的数据
    practiceRecords.value = []
    
    // 处理API返回数据
    if (response && response.items && response.items.length > 0) {
      practiceRecords.value = response.items.map(item => ({
        id: item.id,
        sessionName: item.title || item.name || `模拟面试 ${item.id}`,
        position: item.position || item.job_position || '未指定职位',
        createdAt: item.created_at || item.createdAt || item.create_time,
        duration: item.duration || 0,
        questionCount: getQuestionCount(item),
        overallScore: getOverallScore(item)
      }))
      
      totalRecords.value = response.total || response.items.length
    } else {
      console.warn('API返回数据为空')
      ElMessage.warning('未找到练习记录')
      practiceRecords.value = []
      totalRecords.value = 0
    }
    
    isLoading.value = false
  } catch (error) {
    console.error('获取练习记录失败:', error)
    ElMessage.error('获取练习记录失败，请稍后重试')
    
    // 仅在开发环境使用示例数据
    if (import.meta.env.DEV) {
      console.warn('开发环境下使用示例数据')
      useDemoData()
    } else {
      practiceRecords.value = []
      totalRecords.value = 0
    }
    
    isLoading.value = false
  }
}

// 获取问题数量
const getQuestionCount = (item) => {
  if (item.questions && Array.isArray(item.questions)) {
    return item.questions.length
  }
  if (item.questionCount !== undefined) return item.questionCount
  if (item.question_count !== undefined) return item.question_count
  return 0
}

// 获取总分
const getOverallScore = (item) => {
  if (item.overall_score !== undefined) {
    return parseFloat(item.overall_score).toFixed(1)
  }
  if (item.overallScore !== undefined) {
    return parseFloat(item.overallScore).toFixed(1)
  }
  if (item.score !== undefined) {
    return parseFloat(item.score).toFixed(1)
  }
  return '未评分'
}

// 获取职位显示文本
const getPositionDisplay = (position) => {
  if (!position) return '未指定职位'
  
  if (typeof position === 'object' && position !== null) {
    return position.title || position.name || JSON.stringify(position)
  }
  
  return position
}

// 示例数据（仅当API不可用时在开发环境中使用）
const useDemoData = () => {
  // 使用当前日期作为基准，避免未来日期
  const mockRecords = Array.from({ length: 5 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (i * 2 + 1)) // 确保所有日期都是过去的
    
    const positions = ['前端开发', '后端开发', '全栈开发', '产品经理', '数据分析师']
    const position = positions[i % positions.length]
    
    return {
      id: `demo-session-${i + 1}`, // 添加demo-前缀便于识别
      sessionName: `测试练习 ${i + 1} (示例数据)`, // 明确标记为示例数据
      position,
      createdAt: date.toISOString(),
      duration: Math.floor(Math.random() * 40 + 10) * 60,
      questionCount: Math.floor(Math.random() * 10 + 5),
      overallScore: (Math.random() * 3 + 7).toFixed(1),
    }
  })
  
  practiceRecords.value = mockRecords
  totalRecords.value = mockRecords.length
}

// 应用筛选
const filterRecords = async () => {
  currentPage.value = 1 // 重置到第一页
  await fetchPracticeRecords()
}

// 分页处理
const handleSizeChange = async (size) => {
  pageSize.value = size
  await fetchPracticeRecords()
}

const handleCurrentChange = async (page) => {
  currentPage.value = page
  await fetchPracticeRecords()
}

// 根据筛选条件过滤记录
const filteredPracticeRecords = computed(() => {
  let result = [...practiceRecords.value]
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(record => 
      (record.sessionName && record.sessionName.toLowerCase().includes(keyword)) || 
      (record.position && record.position.toLowerCase().includes(keyword))
    )
  }
  
  // 日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const startDate = new Date(dateRange.value[0])
    startDate.setHours(0, 0, 0, 0)
    
    const endDate = new Date(dateRange.value[1])
    endDate.setHours(23, 59, 59, 999)
    
    result = result.filter(record => {
      if (!record.createdAt) return false
      const recordDate = new Date(record.createdAt)
      return recordDate >= startDate && recordDate <= endDate
    })
  }
  
  return result
})

// 查看报告详情
const viewReport = (id) => {
  router.push(`/interview-report/${id}`)
}

// 查看录像（模拟功能）
const viewRecording = (id) => {
  ElMessage({
    message: '录像播放功能开发中，敬请期待',
    type: 'info'
  })
}

// 删除确认对话框
const confirmDelete = (id) => {
  recordToDelete.value = id
  deleteDialogVisible.value = true
}

// 删除练习记录
const deletePractice = async () => {
  if (!recordToDelete.value) return
  
  try {
    // 调用API删除面试记录
    await interviewSessionAPI.deleteSession(recordToDelete.value)
    
    // 删除成功后更新列表
    await fetchPracticeRecords()
    
    ElMessage({
      type: 'success',
      message: '删除成功'
    })
  } catch (error) {
    console.error('删除练习记录失败:', error)
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    deleteDialogVisible.value = false
    recordToDelete.value = null
  }
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 格式化时长
const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
}

// 根据职位标签样式
const getPositionTagType = (position) => {
  // 如果position是对象，提取title字段
  if (typeof position === 'object' && position !== null && position.title) {
    position = position.title
  }

  const positionMap = {
    '前端开发': 'success',
    '后端开发': 'info',
    '全栈开发': 'warning',
    '产品经理': 'danger',
    '数据分析师': 'primary',
    'UI设计师': '',
    '前端工程师': 'success',
    '后端工程师': 'info',
    '全栈工程师': 'warning'
  }
  return positionMap[position] || ''
}

// 获取分数样式
const getScoreClass = (score) => {
  const numScore = parseFloat(score)
  if (numScore >= 9.0) return 'score excellent'
  if (numScore >= 8.0) return 'score good'
  if (numScore >= 7.0) return 'score average'
  return 'score below'
}
</script>

<style scoped>
.practice-history-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filter-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 250px;
}

.date-picker {
  width: 350px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.practice-name {
  margin-right: 8px;
  font-weight: 500;
}

.score {
  font-weight: bold;
}

.score.excellent {
  color: #67C23A;
}

.score.good {
  color: #409EFF;
}

.score.average {
  color: #E6A23C;
}

.score.below {
  color: #F56C6C;
}

.stat-card {
  margin-bottom: 20px;
}

.stats-header {
  margin-bottom: 15px;
}

.stats-header h3 {
  font-size: 18px;
  margin: 0;
  color: var(--primary-color);
}

.stats-content {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
  padding: 15px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.button-group .el-button {
  min-width: 72px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.button-group .el-icon {
  margin-right: 4px;
}

.env-notice {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .button-group {
    flex-direction: column;
    gap: 5px;
  }
  
  .button-group .el-button {
    margin-left: 0 !important;
    width: 100%;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input,
  .date-picker {
    width: 100%;
    margin-bottom: 10px;
  }
}
</style> 