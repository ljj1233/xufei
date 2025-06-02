<template>
  <div class="interview-prep">
    <h3 class="prep-title">
      <EmotionIcons type="tip" :showText="false" />
      <span>面试准备</span>
    </h3>
    
    <el-carousel height="160px" indicator-position="outside" :interval="5000" arrow="always" class="tips-carousel">
      <el-carousel-item v-for="(tip, index) in interviewTips" :key="index">
        <div class="tip-item">
          <div class="tip-icon">{{ tip.icon }}</div>
          <h4>{{ tip.title }}</h4>
          <p>{{ tip.content }}</p>
        </div>
      </el-carousel-item>
    </el-carousel>
    
    <div class="prep-actions">
      <el-button type="primary" @click="startPrep">
        <el-icon><VideoPlay /></el-icon>
        开始热身
      </el-button>
    </div>
    
    <el-dialog
      v-model="dialogVisible"
      title="面试热身"
      width="500px"
    >
      <div class="prep-dialog-content">
        <div class="prep-step" v-if="currentStep === 1">
          <h4>深呼吸放松</h4>
          <div class="breathing-animation">
            <div class="circle"></div>
            <p>{{ breathingText }}</p>
          </div>
          <p class="step-desc">深呼吸有助于缓解紧张，提高表现</p>
        </div>
        
        <div class="prep-step" v-if="currentStep === 2">
          <h4>调整坐姿</h4>
          <div class="posture-tips">
            <p><el-icon><Check /></el-icon> 挺直腰背</p>
            <p><el-icon><Check /></el-icon> 双脚平放地面</p>
            <p><el-icon><Check /></el-icon> 双肩放松</p>
            <p><el-icon><Check /></el-icon> 保持目光平视</p>
          </div>
        </div>
        
        <div class="prep-step" v-if="currentStep === 3">
          <h4>准备好了吗？</h4>
          <p class="ready-text">
            <EmotionIcons type="excellent" />
            你已完成热身准备，现在可以开始面试了！
          </p>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button v-if="currentStep < 3" type="primary" @click="nextStep">
            下一步
          </el-button>
          <el-button v-else type="success" @click="finishPrep">
            准备完成
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { VideoPlay, Check } from '@element-plus/icons-vue'
import EmotionIcons from './EmotionIcons.vue'

const interviewTips = [
  {
    icon: '🧘',
    title: '深呼吸放松',
    content: '面试前做几次深呼吸，有助于缓解紧张情绪，保持冷静'
  },
  {
    icon: '👔',
    title: '检查着装',
    content: '确保着装整洁得体，给面试官留下专业印象'
  },
  {
    icon: '🔊',
    title: '注意语速',
    content: '保持适中的语速，不要过快或过慢，确保表达清晰'
  },
  {
    icon: '👁️',
    title: '保持眼神接触',
    content: '与面试官保持适当的眼神接触，展示自信和专注'
  },
  {
    icon: '📝',
    title: '准备问题',
    content: '准备2-3个问题，展示你对职位和公司的兴趣'
  }
]

const dialogVisible = ref(false)
const currentStep = ref(1)
const breathingText = ref('吸气...')
let breathingInterval = null

const startPrep = () => {
  dialogVisible.value = true
  currentStep.value = 1
  startBreathingAnimation()
}

const nextStep = () => {
  currentStep.value++
  if (currentStep.value === 1) {
    startBreathingAnimation()
  } else {
    stopBreathingAnimation()
  }
}

const finishPrep = () => {
  dialogVisible.value = false
  currentStep.value = 1
}

const startBreathingAnimation = () => {
  if (breathingInterval) clearInterval(breathingInterval)
  
  let isInhale = true
  breathingText.value = '吸气...'
  
  breathingInterval = setInterval(() => {
    isInhale = !isInhale
    breathingText.value = isInhale ? '吸气...' : '呼气...'
  }, 4000)
}

const stopBreathingAnimation = () => {
  if (breathingInterval) {
    clearInterval(breathingInterval)
    breathingInterval = null
  }
}

onMounted(() => {
  if (currentStep.value === 1) {
    startBreathingAnimation()
  }
})

onUnmounted(() => {
  stopBreathingAnimation()
})
</script>

<style scoped>
.interview-prep {
  margin-bottom: 30px;
}

.prep-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.tips-carousel {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tip-item {
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  background-color: #f5f7fa;
}

.tip-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.tip-item h4 {
  margin: 0 0 10px;
  color: #303133;
}

.tip-item p {
  margin: 0;
  color: #606266;
}

.prep-actions {
  display: flex;
  justify-content: center;
}

.prep-dialog-content {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.prep-step {
  text-align: center;
  width: 100%;
}

.breathing-animation {
  position: relative;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: rgba(64, 158, 255, 0.2);
  animation: breathe 8s infinite ease-in-out;
}

@keyframes breathe {
  0%, 100% {
    transform: scale(1);
    background-color: rgba(64, 158, 255, 0.2);
  }
  50% {
    transform: scale(1.5);
    background-color: rgba(64, 158, 255, 0.5);
  }
}

.posture-tips {
  text-align: left;
  max-width: 300px;
  margin: 0 auto;
}

.posture-tips p {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ready-text {
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.step-desc {
  margin-top: 15px;
  color: #909399;
  font-size: 14px;
}
</style> 