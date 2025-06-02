<template>
  <div class="upload-container">
    <h1 class="page-title">上传面试视频/音频</h1>
    
    <div class="upload-intro">
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div class="intro-text">
            <h2>准备好展示最好的自己了吗？</h2>
            <p>上传您的面试视频或音频，让AI助手为您提供专业评估和改进建议。</p>
            <p>每次练习都是进步的机会！</p>
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <InterviewPrep />
        </el-col>
      </el-row>
    </div>
    
    <el-form
      ref="uploadFormRef"
      :model="uploadForm"
      :rules="uploadRules"
      label-position="top"
      class="card"
    >
      <!-- 步骤导航 -->
      <div class="steps-nav">
        <div class="step-item" :class="{ 'active': currentStep >= 1 }">
          <div class="step-number">1</div>
          <div class="step-label">基本信息</div>
        </div>
        <div class="step-connector"></div>
        <div class="step-item" :class="{ 'active': currentStep >= 2 }">
          <div class="step-number">2</div>
          <div class="step-label">选择职位</div>
        </div>
        <div class="step-connector"></div>
        <div class="step-item" :class="{ 'active': currentStep >= 3 }">
          <div class="step-number">3</div>
          <div class="step-label">上传文件</div>
        </div>
      </div>
      
      <!-- 步骤1：基本信息 -->
      <div v-show="currentStep === 1">
        <div class="step-header">
          <h3>
            <EmotionIcons type="tip" :showText="false" />
            <span>基本信息</span>
          </h3>
        </div>
        
        <el-form-item label="面试标题" prop="title">
          <el-input 
            v-model="uploadForm.title" 
            placeholder="例如：产品经理面试-XX公司" 
            :prefix-icon="Document"
          />
        </el-form-item>
        
        <el-form-item label="面试描述（可选）">
          <el-input 
            v-model="uploadForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="描述此次面试的背景、职位等信息"
          />
        </el-form-item>
        
        <div class="step-actions">
          <el-button type="primary" @click="nextStep">下一步</el-button>
        </div>
      </div>
      
      <!-- 步骤2：职位选择 -->
      <div v-show="currentStep === 2">
        <div class="step-header">
          <h3>
            <EmotionIcons type="tip" :showText="false" />
            <span>选择面试职位</span>
          </h3>
        </div>
        
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
            <TipCard 
              title="为什么创建新职位？" 
              content="创建特定职位可以让AI更准确地评估您的面试表现，针对特定岗位要求提供更精准的建议。"
            />
            
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
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="nextStep">下一步</el-button>
        </div>
      </div>
      
      <!-- 步骤3：文件上传 -->
      <div v-show="currentStep === 3">
        <div class="step-header">
          <h3>
            <EmotionIcons type="tip" :showText="false" />
            <span>上传面试文件</span>
          </h3>
        </div>
        
        <TipCard important>
          <template #default>
            <h4>上传提示</h4>
            <ul class="upload-tips">
              <li><strong>视频质量</strong>：确保视频清晰，光线充足，面部可见</li>
              <li><strong>音频质量</strong>：确保音频清晰，背景噪音小</li>
              <li><strong>时长建议</strong>：建议上传3-10分钟的面试片段</li>
            </ul>
          </template>
        </TipCard>
        
        <div class="upload-area">
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
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                请上传您的面试视频或音频文件，文件大小不超过100MB
              </div>
            </template>
          </el-upload>
        </div>
        
        <div class="privacy-notice">
          <el-alert
            title="隐私说明"
            type="info"
            description="您上传的面试视频/音频将仅用于分析目的，系统会保护您的隐私，不会将您的数据用于其他用途。"
            show-icon
            :closable="false"
          />
        </div>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            上传并分析
          </el-button>
        </div>
      </div>
    </el-form>
    
    <!-- 上传进度 -->
    <div v-if="uploading" class="card">
      <h3>处理进度</h3>
      <div class="progress-status">
        <EmotionIcons type="loading" />
        <p>{{ statusText }}</p>
      </div>
      <el-progress :percentage="progressPercentage" :status="progressStatus" />
    </div>
    
    <!-- 上传成功后的操作 -->
    <div v-if="uploadSuccess" class="card success-card">
      <el-result
        icon="success"
        title="分析完成！"
        sub-title="您的面试已成功上传并完成分析"
      >
        <template #icon>
          <div class="custom-result-icon">
            <EmotionIcons type="success" />
          </div>
        </template>
        <template #extra>
          <el-button type="primary" @click="viewReport">查看分析结果</el-button>
          <el-button @click="resetForm">继续上传</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInterviewStore } from '../stores/interview'
import { useUserStore } from '../stores/user'
import { Document, UploadFilled } from '@element-plus/icons-vue'
import EmotionIcons from '../components/EmotionIcons.vue'
import TipCard from '../components/TipCard.vue'
import InterviewPrep from '../components/InterviewPrep.vue'

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

// 步骤控制
const currentStep = ref(1)

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
    { required: true, message: '请选择面试职位', trigger: 'change' }
  ]
}

// 进度状态
const progressStatus = computed(() => {
  if (progressPercentage.value < 100) {
    return ''
  }
  return 'success'
})

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

// 步骤控制
const nextStep = () => {
  if (currentStep.value === 1) {
    if (!uploadForm.title) {
      ElMessage.warning('请填写面试标题')
      return
    }
  } else if (currentStep.value === 2) {
    if (!uploadForm.job_position_id) {
      ElMessage.warning('请选择面试职位')
      return
    }
  }
  
  currentStep.value++
}

const prevStep = () => {
  currentStep.value--
}

// 处理文件变化
const handleFileChange = (file) => {
  console.log('文件变化:', file)
}

// 处理超出文件数量限制
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

// 处理文件移除
const handleRemove = () => {
  fileList.value = []
}

// 提交上传
const submitUpload = async () => {
  if (!fileList.value.length) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  statusText.value = '正在上传文件...'
  progressPercentage.value = 10
  
  try {
    // 模拟上传过程
    await simulateProgress()
    
    // 模拟上传成功
    uploadSuccess.value = true
    uploadedInterviewId.value = '123456' // 模拟ID
    
    ElMessage.success('面试分析完成')
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

// 模拟进度
const simulateProgress = () => {
  return new Promise((resolve) => {
    let progress = 10
    const interval = setInterval(() => {
      progress += 5
      progressPercentage.value = progress
      
      if (progress < 30) {
        statusText.value = '正在上传文件...'
      } else if (progress < 60) {
        statusText.value = 'AI正在分析语音内容...'
      } else if (progress < 80) {
        statusText.value = 'AI正在分析视觉表现...'
      } else {
        statusText.value = '正在生成评估报告...'
      }
      
      if (progress >= 100) {
        clearInterval(interval)
        resolve()
      }
    }, 300)
  })
}

// 查看报告
const viewReport = () => {
  router.push(`/report/${uploadedInterviewId.value}`)
}

// 重置表单
const resetForm = () => {
  uploadFormRef.value.resetFields()
  fileList.value = []
  uploadSuccess.value = false
  progressPercentage.value = 0
  currentStep.value = 1
}

// 获取职位列表
const fetchJobPositions = async () => {
  try {
    // 模拟获取职位列表
    jobPositions.value = [
      { id: '1', title: '高级AI工程师', tech_field: 'artificial_intelligence', position_type: 'technical' },
      { id: '2', title: '产品经理', tech_field: 'artificial_intelligence', position_type: 'product' },
      { id: '3', title: '运维工程师', tech_field: 'intelligent_system', position_type: 'operation' }
    ]
  } catch (error) {
    console.error('获取职位列表失败:', error)
    ElMessage.error('获取职位列表失败，请稍后重试')
  }
}

onMounted(() => {
  fetchJobPositions()
})
</script>

<style scoped>
.upload-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  text-align: center;
  color: #1E88E5;
  margin-bottom: 30px;
}

.upload-intro {
  margin-bottom: 30px;
}

.intro-text {
  padding: 20px;
  background-color: #f0f8ff;
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.intro-text h2 {
  color: #1E88E5;
  margin-top: 0;
}

.card {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.steps-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 30px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 100px;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #dcdfe6;
  color: #fff;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  transition: all 0.3s;
}

.step-label {
  font-size: 14px;
  color: #909399;
  transition: all 0.3s;
}

.step-connector {
  flex: 1;
  height: 2px;
  background-color: #dcdfe6;
  margin: 0 10px;
  position: relative;
  top: -15px;
}

.step-item.active .step-number {
  background-color: #1E88E5;
}

.step-item.active .step-label {
  color: #1E88E5;
  font-weight: bold;
}

.step-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.step-header h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  color: #303133;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
  gap: 10px;
}

.upload-area {
  text-align: center;
  margin: 20px 0;
}

.upload-tips {
  padding-left: 20px;
  line-height: 1.8;
}

.privacy-notice {
  margin: 20px 0;
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.success-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e1f5fe 100%);
}

.custom-result-icon {
  font-size: 72px;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .steps-nav {
    flex-direction: column;
    gap: 10px;
  }
  
  .step-connector {
    width: 2px;
    height: 20px;
    margin: 5px 0;
    top: 0;
  }
  
  .step-item {
    flex-direction: row;
    width: 100%;
    justify-content: flex-start;
    gap: 10px;
  }
}
</style>