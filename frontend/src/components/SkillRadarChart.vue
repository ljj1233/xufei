<template>
  <div class="radar-chart-container">
    <div class="chart-title" v-if="title">{{ title }}</div>
    <div class="radar-chart" ref="chartContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarChart,
  CanvasRenderer
])

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  data: {
    type: Array,
    required: true,
    // 期望格式: [{ name: '语音清晰度', value: 8.5 }, ...]
  },
  maxScore: {
    type: Number,
    default: 10
  }
})

const chartContainer = ref(null)
let chart = null

const initChart = () => {
  if (!chartContainer.value) return
  
  // 销毁旧实例
  if (chart) {
    chart.dispose()
  }
  
  // 创建新实例
  chart = echarts.init(chartContainer.value)
  
  // 准备雷达图数据
  const indicator = props.data.map(item => ({
    name: item.name,
    max: props.maxScore
  }))
  
  const seriesData = [{
    value: props.data.map(item => item.value),
    name: '能力评分',
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(30, 136, 229, 0.8)' },
        { offset: 1, color: 'rgba(30, 136, 229, 0.2)' }
      ])
    }
  }]
  
  // 配置项
  const option = {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicator,
      radius: '65%',
      splitNumber: 5,
      axisName: {
        color: '#606266',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: ['#f5f7fa', '#e4e7ed'],
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.1)'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#dcdfe6'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#dcdfe6'
        }
      }
    },
    series: [{
      type: 'radar',
      data: seriesData,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2,
        color: '#1E88E5'
      },
      itemStyle: {
        color: '#1E88E5'
      },
      emphasis: {
        lineStyle: {
          width: 4
        }
      }
    }]
  }
  
  // 应用配置
  chart.setOption(option)
  
  // 响应窗口大小变化
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
}

// 监听数据变化
watch(() => props.data, () => {
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()
})
</script>

<style scoped>
.radar-chart-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  text-align: center;
}

.radar-chart {
  width: 100%;
  height: 300px;
}
</style> 