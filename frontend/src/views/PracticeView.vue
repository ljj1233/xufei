<!-- 
  面试练习页面
  
  展示指定职位的练习题目，允许用户逐题练习和查看参考答案
-->
<template>
  <div class="practice-view">
    <div class="practice-header">
      <div class="position-info" v-if="positionInfo">
        <h2>{{ positionInfo.title }} - 快速练习</h2>
        <p>技术领域: {{ getTechFieldName(positionInfo.tech_field) }}</p>
        <p>岗位类型: {{ getPositionTypeName(positionInfo.position_type) }}</p>
      </div>
      
      <div class="practice-actions">
        <el-button type="primary" @click="backToList">返回列表</el-button>
      </div>
    </div>
    
    <div class="practice-content" v-loading="loading">
      <!-- 题目加载提示 -->
      <div v-if="loading" class="loading-info">
        正在加载练习题目...
      </div>
      
      <!-- 没有题目的提示 -->
      <div v-else-if="questions.length === 0" class="no-questions">
        <el-empty description="暂无练习题目" />
        <el-button type="primary" @click="loadQuestions">重新加载</el-button>
      </div>
      
      <!-- 题目列表 -->
      <div v-else class="question-list">
        <QuestionCard
          v-for="question in questions"
          :key="question.id"
          :question="question"
          :position-id="positionId"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import QuestionCard from '../components/QuestionCard.vue'

// 路由和导航
const route = useRoute()
const router = useRouter()
const positionId = ref(route.params.positionId)

// 状态管理
const loading = ref(true)
const questions = ref([])
const positionInfo = ref(null)

// 技术领域映射
const techFieldMap = {
  'artificial_intelligence': '人工智能',
  'big_data': '大数据',
  'internet_of_things': '物联网',
  'intelligent_system': '智能系统'
}

// 岗位类型映射
const positionTypeMap = {
  'technical': '技术岗',
  'operation': '运维测试岗',
  'product': '产品岗'
}

// 获取技术领域显示名称
const getTechFieldName = (code) => {
  return techFieldMap[code] || code
}

// 获取岗位类型显示名称
const getPositionTypeName = (code) => {
  return positionTypeMap[code] || code
}

// 加载职位信息
const loadPositionInfo = async () => {
  try {
    console.log(`加载职位ID=${positionId.value}的信息`)
    
    const response = await fetch(`/api/job-positions/${positionId.value}`)
    
    if (response.ok) {
      positionInfo.value = await response.json()
      console.log('职位信息加载成功:', positionInfo.value)
    } else {
      const error = await response.json()
      console.error('获取职位信息失败:', error)
      ElMessage.error('获取职位信息失败: ' + (error.detail || '未知错误'))
    }
  } catch (err) {
    console.error('获取职位信息过程出错:', err)
    ElMessage.error('获取职位信息出错: ' + err.message)
  }
}

// 加载练习题目
const loadQuestions = async () => {
  try {
    loading.value = true
    console.log(`加载职位ID=${positionId.value}的练习题目`)
    
    const response = await fetch(`/api/practice/${positionId.value}?count=6`)
    
    if (response.ok) {
      questions.value = await response.json()
      console.log('练习题目加载成功:', questions.value)
    } else {
      const error = await response.json()
      console.error('获取练习题目失败:', error)
      ElMessage.error('获取练习题目失败: ' + (error.detail || '未知错误'))
    }
  } catch (err) {
    console.error('获取练习题目过程出错:', err)
    ElMessage.error('获取练习题目出错: ' + err.message)
  } finally {
    loading.value = false
  }
}

// 返回列表
const backToList = () => {
  router.push('/interview-practice')
}

// 页面加载时初始化数据
onMounted(async () => {
  if (!positionId.value) {
    ElMessage.error('缺少职位ID参数')
    backToList()
    return
  }
  
  // 并行加载职位信息和练习题目
  await Promise.all([
    loadPositionInfo(),
    loadQuestions()
  ])
})
</script>

<style scoped>
.practice-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.practice-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.position-info h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.position-info p {
  margin: 5px 0;
  color: #606266;
}

.practice-content {
  min-height: 400px;
}

.loading-info,
.no-questions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #909399;
}

.no-questions .el-button {
  margin-top: 20px;
}

.question-list {
  padding: 10px 0;
}
</style> 