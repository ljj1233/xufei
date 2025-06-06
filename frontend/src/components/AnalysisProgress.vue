<template>
  <div class="analysis-progress">
    <div class="progress-container">
      <el-progress 
        :percentage="progress" 
        :status="progressStatus"
        :stroke-width="10"
      ></el-progress>
      <div class="status-message">{{ statusMessage }}</div>
    </div>

    <div v-if="partialFeedback.length > 0" class="partial-feedback">
      <div v-for="(feedback, index) in partialFeedback" :key="index" class="feedback-item">
        <div class="feedback-type">{{ getFeedbackTypeLabel(feedback.type) }}</div>
        <div class="feedback-content">
          <!-- 根据反馈类型渲染不同的内容 -->
          <div v-if="feedback.type === 'speech'">
            <div class="metric">
              <span>语速:</span> {{ feedback.content.speech_rate }} 字/分钟
            </div>
            <div class="metric">
              <span>清晰度:</span> {{ feedback.content.clarity_score }} 分
            </div>
          </div>
          <div v-else-if="feedback.type === 'visual'">
            <div class="metric">
              <span>姿态评分:</span> {{ feedback.content.posture_score }} 分
            </div>
            <div class="metric">
              <span>表情自然度:</span> {{ feedback.content.expression_score }} 分
            </div>
          </div>
          <div v-else-if="feedback.type === 'content'">
            <div class="metric">
              <span>内容相关性:</span> {{ feedback.content.relevance_score }} 分
            </div>
            <div class="metric">
              <span>逻辑性:</span> {{ feedback.content.logic_score }} 分
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { webSocketService } from '../services/websocket.service';
import { useUserStore } from '../stores/user';

const userStore = useUserStore();
const progress = ref(0);
const statusMessage = ref('准备分析...');
const partialFeedback = ref([]);

const progressStatus = computed(() => {
  if (progress.value === 100) return 'success';
  return '';
});

const getFeedbackTypeLabel = (type) => {
  switch (type) {
    case 'speech': return '语音分析';
    case 'visual': return '视觉分析';
    case 'content': return '内容分析';
    default: return '其他分析';
  }
};

// 处理分析进度更新
const handleProgressUpdate = (message) => {
  const { data } = message;
  progress.value = data.progress;
  statusMessage.value = data.status;
};

// 处理部分反馈
const handlePartialFeedback = (message) => {
  const { data } = message;
  partialFeedback.value.push(data);
};

// 处理错误消息
const handleError = (message) => {
  const { data } = message;
  console.error(`错误: ${data.code} - ${data.message}`);
  // 这里可以添加错误通知逻辑
};

onMounted(() => {
  // 连接WebSocket
  webSocketService.connect(userStore.userId);
  
  // 注册消息处理器
  webSocketService.on('ANALYSIS_PROGRESS', handleProgressUpdate);
  webSocketService.on('FEEDBACK', handlePartialFeedback);
  webSocketService.on('ERROR', handleError);
});

onUnmounted(() => {
  // 移除消息处理器
  webSocketService.off('ANALYSIS_PROGRESS', handleProgressUpdate);
  webSocketService.off('FEEDBACK', handlePartialFeedback);
  webSocketService.off('ERROR', handleError);
  
  // 断开WebSocket连接
  webSocketService.disconnect();
});
</script>

<style scoped>
.analysis-progress {
  margin: 20px 0;
  padding: 20px;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.progress-container {
  margin-bottom: 20px;
}

.status-message {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.partial-feedback {
  margin-top: 20px;
}

.feedback-item {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 4px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.feedback-type {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.feedback-content {
  font-size: 14px;
}

.metric {
  margin-bottom: 4px;
}

.metric span {
  font-weight: 500;
  color: #606266;
}
</style> 