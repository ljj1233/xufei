<template>
  <div class="upload-container">
    <h1 class="page-title">上传面试视频/音频</h1>
    
    <el-form
      ref="uploadFormRef"
      :model="uploadForm"
      :rules="uploadRules"
      label-position="top"
      class="card"
    >
      <!-- 面试标题和描述 -->
      <el-form-item label="面试标题" prop="title">
        <el-input v-model="uploadForm.title" placeholder="例如：产品经理面试-XX公司" />
      </el-form-item>
      
      <el-form-item label="面试描述（可选）">
        <el-input 
          v-model="uploadForm.description" 
          type="textarea" 
          :rows="3"
          placeholder="描述此次面试的背景、职位等信息"
        />
      </el-form-item>
      
      <!-- 职位选择 -->
      <h3>选择面试职位</h3>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="技术领域">
            <el-select v-model="uploadForm.tech_field" style="width: 100%">
              <el-option 
                v-for="option in techFieldOptions" 
                :key="option.value" 
                :label="option.label" 
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="岗位类型">
            <el-select v-model="uploadForm.position_type" style="width: 100%">
              <el-option 
                v-for="option in positionTypeOptions" 
                :key="option.value" 
                :label="option.label" 
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="选择具体职位" prop="job_position_id">
        <el-select 
          v-model="uploadForm.job_position_id" 
          style="width: 100%"
          placeholder="请先选择职位或创建新职位"
          clearable
        >
          <el-option 
            v-for="position in jobPositions" 
            :key="position.id" 
            :label="`${position.title} (${getTechFieldLabel(position.tech_field)}/${getPositionTypeLabel(position.position_type)})`" 
            :value="position.id"
          />
        </el-select>
      </el-form-item>
      
      <!-- 创建新职位 -->
      <el-collapse>
        <el-collapse-item title="创建新职位" name="1">
          <el-form-item label="职位名称">
            <el-input v-model="newPosition.title" placeholder="例如：高级AI工程师" />
          </el-form-item>
          
          <el-form-item label="所需技能">
            <el-input 
              v-model="newPosition.required_skills" 
              type="textarea" 
              :rows="2"
              placeholder="例如：Python, TensorFlow, 计算机视觉"
            />
          </el-form-item>
          
          <el-form-item label="岗位描述">
            <el-input 
              v-model="newPosition.job_description" 
              type="textarea" 
              :rows="3"
              placeholder="详细描述该职位的工作内容和要求"
            />
          </el-form-item>
          
          <el-form-item label="评估标准">
            <el-input 
              v-model="newPosition.evaluation_criteria" 
              type="textarea" 
              :rows="3"
              placeholder="面试评估的关键指标和标准"
            />
          </el-form-item>
        </el-collapse-item>
      </el-collapse>
      
      <!-- 文件上传 -->
      <div class="upload-area">
        <h3>上传面试文件</h3>
        <p>支持的格式：MP4, AVI, MOV, MP3, WAV (最大100MB)</p>
        
        <el-upload
          ref="uploadRef"
          action=""
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          :on-remove="handleRemove"
          :file-list="fileList"
          accept=".mp4,.avi,.mov,.mp3,.wav"
        >
          <template #trigger>
            <el-button type="primary">选择文件</el-button>
          </template>
          <template #tip>
            <div class="el-upload__tip">
              请上传您的面试视频或音频文件，文件大小不超过100MB
            </div>
          </template>
        </el-upload>
      </div>
      
      <!-- 提交按钮 -->
      <el-form-item>
        <el-button type="primary" @click="submitUpload" :loading="uploading">
          上传并分析
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 上传进度 -->
    <div v-if="uploading" class="card">
      <h3>处理进度</h3>
      <p>{{ statusText }}</p>
      <el-progress :percentage="progressPercentage" />
    </div>
    
    <!-- 上传成功后的操作 -->
    <div v-if="uploadSuccess" class="card">
      <el-result
        icon="success"
        title="分析完成！"
        sub-title="您的面试已成功上传并完成分析"
      >
        <template #extra>
          <el-button type="primary" @click="viewReport">查看分析结果</el-button>
          <el-button @click="resetForm">继续上传</el-button>
        </template>
      </el-result>
    </div>
    
    <!-- 上传说明 -->
    <el-collapse class="card">
      <el-collapse-item title="上传说明" name="1">
        <h4>如何获得最佳分析效果？</h4>
        <ol>
          <li><strong>视频质量</strong>：确保视频清晰，光线充足，面部可见</li>
          <li><strong>音频质量</strong>：确保音频清晰，背景噪音小</li>
          <li><strong>时长建议</strong>：建议上传3-10分钟的面试片段</li>
          <li><strong>文件大小</strong>：文件大小不超过100MB</li>
          <li><strong>格式支持</strong>：支持MP4、AVI、MOV视频格式和MP3、WAV音频格式</li>
        </ol>
        
        <h4>隐私说明</h4>
        <p>您上传的面试视频/音频将仅用于分析目的，系统会保护您的隐私，不会将您的数据用于其他用途。</p>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInterviewStore } from '../stores/interview'
import { useUserStore } from '../stores/user'

const router = useRouter()
const interviewStore = useInterviewStore()
const userStore = useUserStore()

// 表单引用
const uploadFormRef = ref(null)
const uploadRef = ref(null)

// 文件列表
const fileList = ref([])

// 上传状态
const uploading = ref(false)
const uploadSuccess = ref(false)
const progressPercentage = ref(0)
const statusText = ref('')
const uploadedInterviewId = ref(null)

// 职位列表
const jobPositions = ref([])

// 技术领域选项
const techFieldOptions = [
  { value: 'artificial_intelligence', label: '人工智能' },
  { value: 'big_data', label: '大数据' },
  { value: 'internet_of_things', label: '物联网' },
  { value: 'intelligent_system', label: '智能系统' }
]

// 岗位类型选项
const positionTypeOptions = [
  { value: 'technical', label: '技术岗' },
  { value: 'operation', label: '运维测试岗' },
  { value: 'product', label: '产品岗' }
]

// 上传表单数据
const uploadForm = reactive({
  title: '',
  description: '',
  tech_field: 'artificial_intelligence',
  position_type: 'technical',
  job_position_id: ''
})

// 新职位数据
const newPosition = reactive({
  title: '',
  tech_field: 'artificial_intelligence',
  position_type: 'technical',
  required_skills: '',
  job_description: '',
  evaluation_criteria: ''
})

// 表单验证规则
const uploadRules = {
  title: [
    { required: true, message: '请输入面试标题', trigger: 'blur' }
  ],
  job_position_id: [
    { 
      validator: (rule, value, callback) => {
        if (!value && !newPosition.title) {
          callback(new Error('请选择职位或创建新职位'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ]
}

// 获取技术领域标签
const getTechFieldLabel = (value) => {
  const option = techFieldOptions.find(opt => opt.value === value)
  return option ? option.label : value
}

// 获取岗位类型标签
const getPositionTypeLabel = (value) => {
  const option = positionTypeOptions.find(opt => opt.value === value)
  return option ? option.label : value
}

// 加载职位列表
const loadJobPositions = async () => {
  const result = await interviewStore.getJobPositions()
  if (result.success) {
    jobPositions.value = result.data
  } else {
    ElMessage.error('获取职位列表失败')
  }
}

// 创建新职位
const createJobPosition = async () => {
  if (!newPosition.title) {
    return null
  }
  
  // 设置技术领域和岗位类型
  newPosition.tech_field = uploadForm.tech_field
  newPosition.position_type = uploadForm.position_type
  
  const result = await interviewStore.createJobPosition(newPosition)
  if (result.success) {
    ElMessage.success('职位创建成功！')
    await loadJobPositions() // 重新加载职位列表
    return result.data.id
  } else {
    ElMessage.error(result.message || '创建职位失败')
    return null
  }
}

// 处理文件变更
const handleFileChange = (file) => {
  // 检查文件大小（100MB = 100 * 1024 * 1024 bytes）
  const maxSize = 100 * 1024 * 1024
  if (file.raw.size > maxSize) {
    ElMessage.error('文件大小不能超过100MB')
    fileList.value = []
    return false
  }
  return true
}

// 处理文件超出限制
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

// 处理文件移除
const handleRemove = () => {
  fileList.value = []
}

// 模拟上传进度
const simulateProgress = (start, end, duration, callback) => {
  progressPercentage.value = start
  const step = (end - start) / (duration / 100)
  let current = start
  
  const interval = setInterval(() => {
    current += step
    progressPercentage.value = Math.min(Math.round(current), end)
    
    if (current >= end) {
      clearInterval(interval)
      if (callback) callback()
    }
  }, 100)
  
  return interval
}

// 提交上传
const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  await uploadFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 检查是否有文件
    if (fileList.value.length === 0) {
      ElMessage.error('请上传面试文件')
      return
    }
    
    uploading.value = true
    uploadSuccess.value = false
    statusText.value = '正在上传文件...'
    
    try {
      // 如果选择创建新职位
      let positionId = uploadForm.job_position_id
      if (!positionId && newPosition.title) {
        positionId = await createJobPosition()
        if (!positionId) {
          uploading.value = false
          return
        }
      }
      
      // 模拟文件上传进度
      const uploadInterval = simulateProgress(0, 100, 1000, async () => {
        // 准备表单数据
        const formData = new FormData()
        formData.append('file', fileList.value[0].raw)
        formData.append('title', uploadForm.title)
        if (uploadForm.description) {
          formData.append('description', uploadForm.description)
        }
        formData.append('job_position_id', positionId)
        
        // 上传文件
        const uploadResult = await interviewStore.uploadInterview(formData)
        
        if (uploadResult.success) {
          ElMessage.success('文件上传成功！')
          uploadedInterviewId.value = uploadResult.data.id
          
          // 开始分析
          statusText.value = '正在进行多模态分析...'
          progressPercentage.value = 0
          
          // 模拟分析进度
          simulateProgress(0, 100, 5000, async () => {
            // 调用分析API
            const analysisResult = await interviewStore.startAnalysis(uploadedInterviewId.value)
            
            if (analysisResult.success) {
              ElMessage.success('分析完成！')
              statusText.value = '分析已完成'
              uploadSuccess.value = true
            } else {
              ElMessage.error(analysisResult.message || '分析失败')
              statusText.value = '分析失败'
            }
            
            uploading.value = false
          })
        } else {
          ElMessage.error(uploadResult.message || '上传失败')
          statusText.value = '上传失败'
          uploading.value = false
        }
      })
    } catch (error) {
      ElMessage.error('处理过程中出错')
      console.error(error)
      statusText.value = '处理失败'
      uploading.value = false
    }
  })
}

// 查看报告
const viewReport = () => {
  if (uploadedInterviewId.value) {
    router.push(`/report/${uploadedInterviewId.value}`)
  }
}

// 重置表单
const resetForm = () => {
  uploadFormRef.value?.resetFields()
  fileList.value = []
  uploadSuccess.value = false
  uploadedInterviewId.value = null
  newPosition.title = ''
  newPosition.required_skills = ''
  newPosition.job_description = ''
  newPosition.evaluation_criteria = ''
}

// 组件挂载时加载职位列表
onMounted(() => {
  loadJobPositions()
})
</script>

<style scoped>
.upload-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.upload-area {
  margin: 20px 0;
}

.el-upload__tip {
  margin-top: 10px;
}
</style>