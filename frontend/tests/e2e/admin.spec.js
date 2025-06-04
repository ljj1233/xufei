// 注意：这个文件需要单独通过Playwright运行，不应该在单元测试中执行
// 通过单元测试运行器执行时会跳过这些测试

// 这些测试使用Playwright进行端到端测试，需要单独设置和运行
// import { test, expect } from '@playwright/test';

// 辅助函数，用于管理员登录
async function adminLogin(page) {
  // 访问登录页面
  await page.goto('/login');
  
  // 输入管理员凭据
  await page.fill('[data-test="username"]', 'admin');
  await page.fill('[data-test="password"]', 'adminpass123');
  await page.click('[data-test="login-button"]');
  
  // 等待重定向到首页
  await page.waitForURL('**/');
}

/*
// 测试管理员登录和访问管理控制台
test('管理员可以访问管理控制台', async ({ page }) => {
  await adminLogin(page);
  
  // 检查管理控制台链接是否可见
  await expect(page.locator('[data-test="admin-link"]')).toBeVisible();
  
  // 点击管理控制台链接
  await page.click('[data-test="admin-link"]');
  
  // 验证已进入管理页面
  await expect(page).toHaveURL('**/admin');
  await expect(page.locator('h1')).toContainText('管理控制台');
});

// 测试管理员可以查看用户列表
test('管理员可以查看用户列表', async ({ page }) => {
  await adminLogin(page);
  await page.goto('/admin');
  
  // 检查用户列表是否加载
  await expect(page.locator('[data-test="user-table"]')).toBeVisible();
  await expect(page.locator('[data-test="user-row"]').first()).toBeVisible();
});

// 测试管理员可以管理用户状态
test('管理员可以管理用户状态', async ({ page }) => {
  await adminLogin(page);
  await page.goto('/admin');
  
  // 检查停用/激活用户按钮是否存在
  await expect(page.locator('[data-test="toggle-user-status"]').first()).toBeVisible();
  
  // 点击停用/激活用户按钮
  await page.click('[data-test="toggle-user-status"]');
  
  // 检查确认对话框
  await expect(page.locator('.el-dialog__title')).toContainText('确认操作');
  
  // 确认操作
  await page.click('[data-test="confirm-btn"]');
  
  // 验证操作成功消息
  await expect(page.locator('.el-message')).toBeVisible();
});
*/

export default {}; 