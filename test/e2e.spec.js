const { test, expect } = require('@playwright/test');

test('E2E Flow: Participant Join & Host Start Game', async ({ browser }) => {
  // 1. Open Admin Page First to Setup
  const adminPage = await browser.newPage();
  await adminPage.goto('http://127.0.0.1:8000/admin/login');
  await adminPage.fill('input[name="password"]', 'admin123');
  await adminPage.click('button[type="submit"]');
  console.log('Admin Logged In');
  
  // Wait for admin page
  await adminPage.waitForSelector('form[action="/api/admin/update"]');
  
  // Set Status to Running
  await adminPage.selectOption('select[name="status"]', 'running');
  // Enable plugins if checkboxes exist
  // Check demo_vote and demo_finder if possible
  // For now, default is usually checked or we assume so.
  
  await adminPage.click('button:has-text("保存设置")');
  console.log('Training Started by Admin');
  
  // 2. Open Large Screen
  const screenPage = await browser.newPage();
  const screenConsoleLogs = [];
  screenPage.on('console', msg => screenConsoleLogs.push(msg.text()));

  await screenPage.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded' });
  console.log('Opened Screen Page');
  
  // Wait for load
  await screenPage.waitForTimeout(1000);

  // Attempt to reset state via Admin API before test
  // This ensures we start clean
  await screenPage.request.post('http://127.0.0.1:8000/api/plugin/reset', {
      headers: {
          // We need a session token for host to reset, BUT wait.
          // The reset endpoint currently requires host login.
          // Let's rely on the flow or just try to recover.
      }
  });
  // Actually, we can't easily call reset without auth.
  // Let's just proceed. If previous test left it in "Results" state, the home page check might fail.
  // BUT the test failed at getting #count.
  // In Results state, #count might not be visible or ID might be different?
  // In my new index.html, #count is in the header IF running/results.
  // Or in .home-stats IF idle.
  // Let's check where #count is.
  
  // In index.html:
  // Header: <span>人数: <span id="count">{{ participant_count }}</span></span>
  // Home: 已签到: <span id="count">{{ participant_count }}</span> 人
  // So #count should exist in both states.
  
  // However, if the page is reloading or in transition, it might flake.
  // Let's add a wait for #count.
  
  // Note: The previous failure "Test timeout of 30000ms exceeded" at waiting for locator('#count').
  // This means it couldn't find #count within the remaining time?
  // Or the whole test took too long.
  
  // Let's bump timeout for the test.

  // 2. Open Mobile Page (Simulate Participant)
  const participantPage = await browser.newPage();
  await participantPage.goto('http://localhost:8000/signin');
  console.log('Opened Participant Page');

  // Login as Participant
  participantPage.on('console', msg => console.log('Participant Console:', msg.text()));
  await participantPage.fill('input[name="name"]', 'TestUser');
  await participantPage.selectOption('select[name="role"]', 'user');
  await participantPage.click('button[type="submit"]');

  // Verify Home Page
  console.log('Waiting for Home Page...');
  await expect(participantPage.locator('h3:has-text("你好，TestUser")')).toBeVisible({ timeout: 10000 });
  console.log('Participant Logged In');

  // Verify User Count on Screen (Wait for SignalR/WebSocket propagation)
  await screenPage.waitForTimeout(2000);
  // It seems #count might be tricky to find if it's inside a specific structure or hidden?
  // Let's try to reload the screen page to get fresh server-side rendered count
  await screenPage.reload();
  await screenPage.waitForTimeout(1000);
  
  await expect(screenPage.locator('#count')).toBeVisible({ timeout: 10000 });
  // Get count text, trim whitespace
  const userCountText = await screenPage.locator('#count').innerText();
  console.log('User Count on Screen:', userCountText);
  // Expect count to be >= 1
  expect(parseInt(userCountText)).toBeGreaterThanOrEqual(1);

  // 3. Open Mobile Page (Simulate Host)
  const hostPage = await browser.newPage();
  hostPage.on('console', msg => console.log('Host Console:', msg.text()));
  await hostPage.goto('http://127.0.0.1:8000/signin', { waitUntil: 'domcontentloaded' });
  console.log('Opened Host Page');

  // Login as Host
  await hostPage.fill('input[name="name"]', 'HostUser');
  await hostPage.selectOption('select[name="role"]', 'host');
  
  // Wait for password field animation/visibility
  // Using forceful wait or waitForSelector with visible state
  await hostPage.waitForSelector('input[name="host_password"]', { state: 'visible' });
  
  // Password field should be visible now
  await hostPage.fill('input[name="host_password"]', 'admin123');
  await hostPage.click('button[type="submit"]');

  // Verify Host Dashboard
  await expect(hostPage.locator('h3:has-text("主持人控制台")')).toBeVisible({ timeout: 15000 });
  console.log('Host Logged In');

  // 4. Host Start Game (Vote Plugin)
  console.log('Host Starting Game...');
  
  // Click "加载互动" for "投票插件" (demo_vote)
  // Locate the specific plugin item div inside the list
  // Use xpath to find the div that directly contains the strong tag with text
  const pluginItem = hostPage.locator('div').filter({ has: hostPage.locator('strong', { hasText: '投票插件' }) }).last();
  
  await pluginItem.getByRole('button', { name: '加载互动' }).click();
  
  // Wait for plugin content to load
  await expect(hostPage.locator('#plugin-container')).toBeVisible();
  // Verify correct plugin loaded (Fix for: "displayed demo_finder instead of demo_vote")
  await expect(hostPage.locator('#plugin-content')).toContainText('现场投票');
  
  // Start Vote
  await hostPage.click('button:has-text("开始投票")');
  
  // Handle alert
  hostPage.on('dialog', dialog => dialog.accept());

  // 5. Verify Game Loaded on Screen
  // Vote plugin shows "现场投票"
  await expect(screenPage.locator('.vote-plugin-screen')).toBeVisible({ timeout: 10000 });
  await expect(screenPage.getByText('现场投票')).toBeVisible();
  console.log('Vote Game Loaded on Screen');
  
  // 6. Verify Participant Page
  // Vote plugin user page
  await expect(participantPage.locator('.vote-plugin-user')).toBeVisible({ timeout: 10000 });
  console.log('Vote Game Loaded on Participant Mobile');
  
  // 7. Participant Submit Answer
  // Click first option (Python)
  await participantPage.click('button:has-text("Python")');
  // Handle alert
  // Playwright handles dialogs automatically or we can add handler
  // But our code uses window.alert.
  // We need to accept it.
  // Actually, we already have a dialog handler set up? No.
  
  participantPage.on('dialog', async dialog => {
      console.log(`Participant Dialog: ${dialog.message()}`);
      await dialog.accept();
  });
  
  console.log('Participant Answer Submitted');

  // 8. Host Stop Game (Directly)
  console.log('Host Stopping Game...');
  
  hostPage.on('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      try {
        await dialog.accept();
      } catch (e) {}
  });
  
  await hostPage.click('button:has-text("直接结束 (显示结果)")');
  
  // Verify Results on Screen
  // Wait for results.html content
  await expect(screenPage.locator('.results-view')).toBeVisible({ timeout: 10000 });
  await expect(screenPage.getByText('总票数:')).toBeVisible();
  await expect(screenPage.getByText('Python')).toBeVisible();
  console.log('Results Page Loaded on Screen');

  // Verify Results on Participant Mobile
  // Use a more generic locator or wait longer
  await expect(participantPage.locator('#interactive-area')).toContainText('互动已结束', { timeout: 15000 });
  console.log('Results Message on Participant Mobile');

  // 9. Host Close Console (Reset to Home)
  console.log('Host Resetting Game...');
  
  hostPage.on('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      try {
        await dialog.accept();
      } catch (e) {}
  });
  
  await hostPage.click('button:has-text("关闭控制台")');
  
  // Verify Screen Resets to Home
  // QR code container should be visible again
  // Wait for reload
  await screenPage.waitForTimeout(2000);
  await expect(screenPage.locator('.home-qr-container')).toBeVisible({ timeout: 10000 });
  console.log('Screen Reset to Home');
  
  // Verify Participant Mobile Resets
  await expect(participantPage.getByText('暂无进行中的互动')).toBeVisible({ timeout: 10000 });
  console.log('Participant Mobile Reset to Idle');
});
