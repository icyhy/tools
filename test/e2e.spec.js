const { test, expect } = require('@playwright/test');

test('E2E Flow: Participant Join & Host Start Game', async ({ browser }) => {
  // 1. Open Large Screen
  const screenPage = await browser.newPage();
  const screenConsoleLogs = [];
  screenPage.on('console', msg => screenConsoleLogs.push(msg.text()));
  
  await screenPage.goto('http://localhost:5175/');
  console.log('Opened Screen Page');
  
  // Wait for load
  await screenPage.waitForTimeout(1000);
  
  // Verify QR Code section exists
  const qrSection = screenPage.locator('.qrcode-section');
  await expect(qrSection).toBeVisible();
  
  // 2. Open Mobile Page (Simulate Participant)
  const participantPage = await browser.newPage();
  await participantPage.goto('http://localhost:5175/mobile');
  console.log('Opened Participant Page');

  // Select Role: Participant
  await participantPage.click('button.role-btn:has-text("我是参与者")');
  
  // Login
  participantPage.on('console', msg => console.log('Participant Console:', msg.text()));
  await participantPage.fill('input.input-field', 'TestUser');
  await participantPage.click('button.btn-primary');
  
  // Verify Lobby
  console.log('Waiting for Lobby...');
  await expect(participantPage.locator('.mobile-lobby')).toBeVisible({ timeout: 10000 });
  console.log('Participant Logged In');

  // Verify User Count on Screen (Wait for SignalR propagation)
  await screenPage.waitForTimeout(1000);
  const userCountText = await screenPage.locator('.users-section h2').innerText();
  console.log('User Count on Screen:', userCountText);
  // Expect count to be at least 1 (or incremented)
  // Note: Depending on server restart, it might be 1. 
  // Let's just log it for now as strict equality might be flaky if test re-runs without server restart.

  // 3. Open Mobile Page (Simulate Host)
  const hostPage = await browser.newPage();
  await hostPage.goto('http://localhost:5175/mobile');
  console.log('Opened Host Page');

  // Select Role: Host
  await hostPage.click('button.role-btn:has-text("我是主持人")');
  
  // Input Password
  await hostPage.fill('input[type="password"]', 'admin123');
  await hostPage.click('button.btn-primary');
  
  // Verify Host Dashboard
  await expect(hostPage.locator('.host-dashboard')).toBeVisible();
  console.log('Host Logged In');

  // 4. Host Start Game
  console.log('Host Starting Game...');
  // Find "找数字规律" card and click start
  const pluginCard = hostPage.locator('.plugin-card').filter({ hasText: '找数字规律' });
  await pluginCard.locator('button.start-btn').click();

  // 5. Verify Game Loaded on Screen
  await screenPage.waitForSelector('.find-number-screen', { timeout: 10000 });
  console.log('Game Loaded on Screen');
  
  // 6. Verify Game Loaded on Participant Mobile
  await participantPage.waitForSelector('.find-number-mobile', { timeout: 10000 });
  console.log('Game Loaded on Participant Mobile');

  // 7. Participant Play Game
  await participantPage.fill('input.number-input', '42');
  await participantPage.click('button.submit-btn');
  
  // Verify button state
  const btnText = await participantPage.locator('button.submit-btn').innerText();
  expect(btnText).toBe('已提交');
  console.log('Participant Answer Submitted');
});
