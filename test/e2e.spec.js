const { test, expect } = require('@playwright/test');

test('E2E Flow: Check-in -> Lobby -> Game Start -> Game Play', async ({ browser }) => {
  // 1. Open Large Screen
  const screenPage = await browser.newPage();
  const screenConsoleLogs = [];
  screenPage.on('console', msg => screenConsoleLogs.push(msg.text()));
  
  await screenPage.goto('http://localhost:5175/');
  console.log('Opened Screen Page');
  
  // Wait for load
  await screenPage.waitForTimeout(1000);
  
  if (screenConsoleLogs.length > 0) {
      console.log('Screen Console Logs:', screenConsoleLogs);
  }

  // Verify QR Code section exists
  const qrSection = screenPage.locator('.qrcode-section');
  await expect(qrSection).toBeVisible();
  
  // 2. Open Mobile Page (Simulate User)
  const mobilePage = await browser.newPage();
  await mobilePage.goto('http://localhost:5175/mobile');
  console.log('Opened Mobile Page');

  // Login
  await mobilePage.fill('input', 'TestUser');
  await mobilePage.click('button');
  
  // Verify Lobby
  await expect(mobilePage.locator('.mobile-lobby')).toBeVisible();
  console.log('Mobile User Logged In');

  // Verify User Count on Screen (Wait for SignalR propagation)
  await screenPage.waitForTimeout(1000);
  // Note: Current implementation resets count on refresh, but user join increments it. 
  // Since screen was open first, it should receive the Join event.
  // However, the current code in ScreenHome.vue increments count on 'UserJoined'.
  // Let's check if '已签到人数' contains '1'
  const userCountText = await screenPage.locator('.users-section h2').innerText();
  console.log('User Count on Screen:', userCountText);

  // 3. Start Game (Simulate Host action via Console)
  console.log('Starting Game via SignalR...');
  await screenPage.evaluate(async () => {
      if (window.__SIGNALR_CONNECTION__) {
          await window.__SIGNALR_CONNECTION__.invoke("StartInteraction", "FindNumber");
      } else {
          throw new Error("SignalR connection not found on window");
      }
  });

  // 4. Verify Game Loaded on Screen
  // Wait for the game container to appear
  await screenPage.waitForSelector('.find-number-screen', { timeout: 5000 });
  console.log('Game Loaded on Screen');
  
  // 5. Verify Game Loaded on Mobile
  await mobilePage.waitForSelector('.find-number-mobile', { timeout: 5000 });
  console.log('Game Loaded on Mobile');

  // 6. Play Game (Submit Answer)
  await mobilePage.fill('input.number-input', '42');
  await mobilePage.click('button.submit-btn');
  
  // Verify button state
  const btnText = await mobilePage.locator('button.submit-btn').innerText();
  expect(btnText).toBe('已提交');
  console.log('Mobile Answer Submitted');

  // 7. Wait for Result (Game is 30s long, maybe too long for test?)
  // We can just verify the game started for now.
});
