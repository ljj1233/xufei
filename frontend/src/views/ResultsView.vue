<template>
  <div class="results-container">
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <h2>面试结果列表</h2>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="interviews.length === 0" class="empty-container">
        <el-empty description="暂无面试记录" />
        <el-button type="primary" @click="$router.push('/upload')">开始新的面试</el-button>
      </div>
      
      <div v-else>
        <el-table :data="interviews" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="面试标题" />
          <el-table-column prop="created_at" label="创建时间">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="score" label="综合评分" width="100">
            <template #default="scope">
              <el-rate
                v-model="scope.row.score"
                disabled
                show-score
                :max="10"
                :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                @click="viewReport(scope.row.id)"
              >
                查看报告
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
          v-model="currentPage" 
          :page-size="pageSize"  
          :page-sizes="[10, 20, 30, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { interviewAPI } from '../api/interview'

const router = useRouter()
const interviews = ref([])
const loading = ref(true)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取面试列表
const fetchInterviews = async () => {
  loading.value = true
  try {
    const response = await interviewAPI.getInterviews({
      page: currentPage.value,
      page_size: pageSize.value
    })
    interviews.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取面试列表失败:', error)
    ElMessage.error('获取面试列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 查看报告
const viewReport = (id) => {
  router.push(`/report/${id}`)
}

// 处理页码变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchInterviews()
}

// 处理每页数量变化
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchInterviews()
}

onMounted(() => {
  fetchInterviews()
})
</script>

<style scoped>
.results-container {
  padding: 20px;
}

.results-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>