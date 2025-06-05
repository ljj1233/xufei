<template>
  <div class="practice-history-container">
    <h1>模拟面试练习记录</h1>
    
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
          <el-tag size="small" :type="getPositionTagType(row.position)" effect="light">{{ row.position }}</el-tag>
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
      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="viewReport(row.id)">查看报告</el-button>
          <el-button type="info" size="small" @click="viewRecording(row.id)">查看录像</el-button>
          <el-button type="danger" size="small" @click="confirmDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
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
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const practiceRecords = ref([])
const isLoading = ref(true)
const currentPage = ref(1)
const pageSize = ref(10)
const totalRecords = ref(0)
const searchKeyword = ref('')
const dateRange = ref([])
const deleteDialogVisible = ref(false)
const recordToDelete = ref(null)

// 模拟数据 - 实际项目中应从API获取
onMounted(async () => {
  try {
    // 模拟API加载延迟
    setTimeout(() => {
      // 模拟获取练习记录数据
      const mockRecords = Array.from({ length: 25 }, (_, i) => {
        const date = new Date()
        date.setDate(date.getDate() - Math.floor(Math.random() * 30))
        
        const positions = ['前端开发', '后端开发', '全栈开发', '产品经理', '数据分析师', 'UI设计师']
        const position = positions[Math.floor(Math.random() * positions.length)]
        
        return {
          id: `practice-${i + 1}`,
          sessionName: `模拟面试练习 ${i + 1}`,
          position,
          createdAt: date.toISOString(),
          duration: Math.floor(Math.random() * 40 + 10) * 60, // 10-50分钟的随机时长（秒）
          questionCount: Math.floor(Math.random() * 10 + 5), // 5-15题
          overallScore: (Math.random() * 3 + 7).toFixed(1), // 7.0-10.0的随机分数
        }
      })
      
      practiceRecords.value = mockRecords
      totalRecords.value = mockRecords.length
      isLoading.value = false
    }, 1000)
  } catch (error) {
    ElMessage.error('获取练习记录失败')
    console.error(error)
    isLoading.value = false
  }
})

// 根据筛选条件过滤记录
const filteredPracticeRecords = computed(() => {
  let result = [...practiceRecords.value]
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(record => 
      record.sessionName.toLowerCase().includes(keyword) || 
      record.position.toLowerCase().includes(keyword)
    )
  }
  
  // 日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const startDate = new Date(dateRange.value[0])
    startDate.setHours(0, 0, 0, 0)
    
    const endDate = new Date(dateRange.value[1])
    endDate.setHours(23, 59, 59, 999)
    
    result = result.filter(record => {
      const recordDate = new Date(record.createdAt)
      return recordDate >= startDate && recordDate <= endDate
    })
  }
  
  return result
})

// 应用筛选
const filterRecords = () => {
  currentPage.value = 1 // 重置到第一页
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

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
const deletePractice = () => {
  if (!recordToDelete.value) return
  
  // 模拟删除操作
  practiceRecords.value = practiceRecords.value.filter(record => record.id !== recordToDelete.value)
  totalRecords.value = practiceRecords.value.length
  
  ElMessage({
    type: 'success',
    message: '删除成功'
  })
  
  deleteDialogVisible.value = false
  recordToDelete.value = null
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

// 获取职位标签样式
const getPositionTagType = (position) => {
  const positionMap = {
    '前端开发': 'success',
    '后端开发': 'info',
    '全栈开发': 'warning',
    '产品经理': 'danger',
    '数据分析师': 'primary',
    'UI设计师': ''
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
</style> 