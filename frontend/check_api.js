/**
 * API就绪检测脚本
 * 
 * 用于检查后端API是否可用
 */

const axios = require('axios');

const API_URL = 'http://localhost:8000/api/v1';

async function checkApiHealth() {
  console.log('正在检查API服务可用性...');
  try {
    // 尝试访问健康检查端点
    const response = await axios.get(`${API_URL}/health`);
    if (response.status === 200) {
      console.log('✅ API服务正常运行');
      if (response.data && response.data.status === 'healthy') {
        console.log(`服务时间: ${response.data.timestamp || '未知'}`);
      }
      return true;
    } else {
      console.log(`❌ API服务返回非正常状态: ${response.status}`);
      return false;
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ API服务未启动或无法连接');
    } else if (error.response) {
      console.log(`❌ API服务返回错误: ${error.response.status} - ${error.response.data?.detail || '未知错误'}`);
    } else {
      console.log(`❌ API检查失败: ${error.message}`);
    }
    return false;
  }
}

// 尝试访问根路径以验证服务器是否在运行
async function checkRootEndpoint() {
  try {
    console.log('检查API根路径...');
    const response = await axios.get('http://localhost:8000/');
    if (response.status === 200) {
      console.log('✅ API服务器正在运行');
      return true;
    }
    return false;
  } catch (error) {
    console.log('❌ 无法连接到API服务器');
    return false;
  }
}

// 检查就绪性并输出信息
async function checkReadiness() {
  const isServerRunning = await checkRootEndpoint();
  
  if (!isServerRunning) {
    console.log('\n❌ API服务器未启动');
    showStartInstructions();
    process.exit(1);
  }
  
  const isApiReady = await checkApiHealth();
  
  if (isApiReady) {
    console.log('\n✅ 系统就绪，可以启动前端服务');
    process.exit(0);
  } else {
    console.log('\n❌ API健康检查失败，服务可能未完全初始化');
    console.log('请等待几秒后再次尝试，或检查后端服务日志');
    showStartInstructions();
    process.exit(1);
  }
}

function showStartInstructions() {
  console.log('\n请按照以下步骤启动后端服务:');
  console.log('1. 打开一个新的终端');
  console.log('2. 进入后端目录: cd xufei/backend');
  console.log('3. 启动API服务: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000');
}

// 执行检查
checkReadiness(); 