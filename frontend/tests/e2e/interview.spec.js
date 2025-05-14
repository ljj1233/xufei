// 端到端测试 - 面试功能
import { test, expect } from '@playwright/test';

// 测试登录功能
test('用户可以登录系统', async ({ page }) => {
  // 访问登录页面
  await page.goto('/login');
  
  // 填写登录表单
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'testpassword123');
  
  // 提交表单
  await page.click('button[type="submit"]');
  
  // 验证登录成功，跳转到首页
  await expect(page).toHaveURL('/');
  
  // 验证导航菜单显示已登录状态
  await expect(page.locator('.user-dropdown')).toContainText('testuser');
});

// 测试面试上传功能
test('用户可以上传面试文件', async ({ page }) => {
  // 先登录
  await page.goto('/login');
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'testpassword123');
  await page.click('button[type="submit"]');
  
  // 导航到上传页面
  await page.click('text=上传面试');
  await expect(page).toHaveURL('/upload');
  
  // 填写上传表单
  await page.fill('input[placeholder="例如：产品经理面试-XX公司"]', '测试面试上传');
  await page.fill('textarea', '这是一个测试面试描述');
  
  // 选择技术领域和岗位类型
  await page.click('.el-select >> nth=0');
  await page.click('text=人工智能');
  await page.click('.el-select >> nth=1');
  await page.click('text=技术岗');
  
  // 上传文件
  await page.setInputFiles('input[type="file"]', './tests/e2e/fixtures/test_audio.mp3');
  
  // 提交表单
  await page.click('button:has-text("提交")'); 
  
  // 验证上传成功，跳转到结果页面
  await expect(page).toHaveURL('/results');
  
  // 验证成功消息
  await expect(page.locator('.el-message')).toBeVisible();
  await expect(page.locator('.el-message')).toContainText('上传成功');
});

// 测试查看面试结果列表
test('用户可以查看面试结果列表', async ({ page }) => {
  // 先登录
  await page.goto('/login');
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'testpassword123');
  await page.click('button[type="submit"]');
  
  // 导航到结果页面
  await page.click('text=分析结果');
  await expect(page).toHaveURL('/results');
  
  // 验证结果列表存在
  await expect(page.locator('.interview-list')).toBeVisible();
  
  // 验证至少有一条记录（之前上传的测试面试）
  await expect(page.locator('.interview-item')).toHaveCount({ min: 1 });
});

// 测试查看面试详情
test('用户可以查看面试详情', async ({ page }) => {
  // 先登录
  await page.goto('/login');
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="password"]', 'testpassword123');
  await page.click('button[type="submit"]');
  
  // 导航到结果页面
  await page.click('text=分析结果');
  
  // 点击第一个面试记录
  await page.click('.interview-item >> nth=0');
  
  // 验证详情页面加载
  await expect(page.locator('.interview-detail')).toBeVisible();
  
  // 验证详情页面包含关键信息
  await expect(page.locator('.interview-title')).toBeVisible();
  await expect(page.locator('.overall-score')).toBeVisible();
  await expect(page.locator('.radar-chart')).toBeVisible();
  await expect(page.locator('.improvement-suggestions')).toBeVisible();
});