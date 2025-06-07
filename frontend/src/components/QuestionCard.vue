<!-- 
  问题卡片组件
  
  用于显示面试问题、技能标签、建议回答时长
  集成录音功能和查看参考答案功能
-->
<template>
  <div class="question-card" :class="{ 'is-answered': hasRecorded }">
    <!-- 问题卡片头部 -->
    <div class="question-header">
      <div class="skill-tags">
        <el-tag 
          v-for="(tag, index) in question.skill_tags" 
          :key="index" 
          size="small" 
          effect="plain"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="suggested-time">
        建议时长: {{ formatTime(question.suggested_duration_seconds) }}
      </div>
    </div>
    
    <!-- 问题内容 -->
    <div class="question-content">
      <h3>{{ question.question }}</h3>
    </div>
    
    <!-- 录音组件 -->
    <AudioRecorder 
      ref="audioRecorder"
      mode="single"
      :question-id="question.id"
      :position-id="positionId"
      :max-duration="question.suggested_duration_seconds * 1.5"
      @on-record-start="onRecordStart"
      @on-record-stop="onRecordStop"
      @on-audio-blob="onAudioBlob"
    />
    
    <!-- 查看参考答案 -->
    <div class="answer-section">
      <el-button 
        type="primary" 
        plain 
        @click="showAnswer"
        :disabled="!question.has_reference_answer && !answerLoaded"
      >
        查看参考答案
      </el-button>
    </div>
    
    <!-- 参考答案弹窗 -->
    <el-dialog
      v-model="answerVisible"
      :title="`问题参考答案`"
      width="50%"
      :close-on-click-modal="true"
    >
      <div v-loading="answerLoading">
        <div v-if="referenceAnswer" class="reference-answer">
          <pre>{{ referenceAnswer }}</pre>
        </div>
        <div v-else-if="!answerLoading" class="no-answer">
          暂无参考答案
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import AudioRecorder from './AudioRecorder.vue'

// 定义组件属性
const props = defineProps({
  question: {
    type: Object,
    required: true
  },
  positionId: {
    type: [String, Number],
    required: true
  }
})

// 内部状态
const audioRecorder = ref(null)
const hasRecorded = ref(false)
const answerVisible = ref(false)
const answerLoading = ref(false)
const referenceAnswer = ref('')
const answerLoaded = ref(false)

// 格式化时间为分钟:秒
const formatTime = (seconds) => {
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}:${sec.toString().padStart(2, '0')}`
}

// 录音开始事件处理
const onRecordStart = () => {
  console.log('开始录制问题答案')
}

// 录音结束事件处理
const onRecordStop = (data) => {
  console.log('录制完成', data)
  hasRecorded.value = true
}

// 获取音频Blob事件处理
const onAudioBlob = (blob) => {
  console.log('收到音频Blob', blob.size + ' 字节')
}

// 显示参考答案
const showAnswer = async () => {
  answerVisible.value = true
  
  // 如果已经加载过答案，直接显示
  if (answerLoaded.value) return
  
  try {
    answerLoading.value = true
    console.log(`加载问题${props.question.id}的参考答案`)
    
    // 调用API获取参考答案
    const response = await fetch(`/api/questions/${props.question.id}/answer`)
    
    if (response.ok) {
      const data = await response.json()
      referenceAnswer.value = data.reference_answer
      answerLoaded.value = true
      console.log('参考答案加载成功')
    } else {
      const error = await response.json()
      console.error('获取参考答案失败:', error)
      ElMessage.error('获取参考答案失败: ' + (error.detail || '未知错误'))
    }
  } catch (err) {
    console.error('获取参考答案过程出错:', err)
    ElMessage.error('获取参考答案出错: ' + err.message)
  } finally {
    answerLoading.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  resetRecording: () => {
    if (audioRecorder.value) {
      audioRecorder.value.resetRecording()
      hasRecorded.value = false
    }
  }
})
</script>

<style scoped>
.question-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.question-card.is-answered {
  border-left: 4px solid #67c23a;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggested-time {
  font-size: 14px;
  color: #909399;
  white-space: nowrap;
}

.question-content {
  margin-bottom: 20px;
}

.question-content h3 {
  margin: 0;
  font-size: 16px;
  line-height: 1.5;
  color: #303133;
}

.answer-section {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.reference-answer {
  white-space: pre-wrap;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.no-answer {
  text-align: center;
  color: #909399;
  padding: 20px;
}
</style> 