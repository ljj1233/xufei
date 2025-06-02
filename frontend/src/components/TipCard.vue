<template>
  <el-card class="tip-card" :class="{ 'is-important': important }">
    <div class="tip-header">
      <div class="icon-container">
        <EmotionIcons type="tip" :showText="false" />
      </div>
      <h4>{{ title }}</h4>
    </div>
    <div class="tip-content">
      <slot>
        <p>{{ content }}</p>
      </slot>
    </div>
    <div v-if="$slots.actions" class="tip-actions">
      <slot name="actions"></slot>
    </div>
  </el-card>
</template>

<script setup>
import { defineProps } from 'vue'
import EmotionIcons from './EmotionIcons.vue'

const props = defineProps({
  title: {
    type: String,
    default: '面试小贴士'
  },
  content: {
    type: String,
    default: ''
  },
  important: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.tip-card {
  margin-bottom: 20px;
  border-left: 4px solid #909399;
  transition: all 0.3s ease;
}

.tip-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.tip-card.is-important {
  border-left-color: #E6A23C;
  background-color: #fdf6ec;
}

.tip-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.icon-container {
  margin-right: 10px;
}

.tip-header h4 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.tip-content {
  color: #606266;
  line-height: 1.6;
}

.tip-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style> 