@echo off
echo 准备启动面试智能体前端开发服务器...

echo 检查Node.js安装...
where node >nul 2>nul
if %errorlevel% neq 0 (
  echo ❌ 未找到Node.js，请先安装Node.js
  pause
  exit /b
)

echo 检查后端API服务...
node check_api.js
if %errorlevel% neq 0 (
  echo 后端API服务未就绪，请先启动后端服务
  pause
  exit /b
)

echo 安装依赖...
npm install

echo 启动前端开发服务器...
npm run dev 