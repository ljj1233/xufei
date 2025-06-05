<template>
  <div ref="chartContainer" :style="{height: height, width: width}" class="pie-chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([PieChart, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  },
  height: {
    type: String,
    default: '300px'
  },
  width: {
    type: String,
    default: '100%'
  },
  isEmpty: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  }
})

const chartContainer = ref(null)
let chart = null

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return
  
  chart = echarts.init(chartContainer.value)
  updateChart()
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chart) return

  const defaultOptions = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      data: props.chartData?.legend || []
    },
    series: []
  }

  // 构建饼图系列
  if (props.isEmpty) {
    // 空数据状态
    defaultOptions.series = [{
      name: props.chartData.title || '',
      type: 'pie',
      radius: ['50%', '70%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '16',
          fontWeight: 'bold',
          formatter: props.emptyText
        }
      },
      labelLine: {
        show: false
      },
      data: [{
        value: 1,
        name: props.emptyText,
        itemStyle: {
          color: '#e0e0e0'
        }
      }]
    }, {
      name: '',
      type: 'pie',
      radius: ['0%', '40%'],
      label: {
        show: true,
        position: 'center',
        formatter: props.emptyText,
        fontSize: 16,
        fontWeight: 'bold',
        color: '#666'
      },
      labelLine: {
        show: false
      },
      data: [{
        value: 1,
        name: '',
        itemStyle: {
          color: '#f5f7fa'
        }
      }]
    }]
  } else {
    // 正常数据状态
    defaultOptions.series = [{
      name: props.chartData.title || '',
      type: 'pie',
      radius: props.chartData.radius || ['50%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {d}%'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '16',
          fontWeight: 'bold'
        }
      },
      data: props.chartData.data || []
    }]
  }

  // 合并自定义选项
  const mergedOptions = {
    ...defaultOptions,
    ...props.options
  }

  chart.setOption(mergedOptions)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chart) {
    chart.resize()
  }
}

// 监听数据变化
watch(() => props.chartData, updateChart, { deep: true })
watch(() => props.isEmpty, updateChart)

// 生命周期钩子
onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.pie-chart-container {
  position: relative;
}
</style> 