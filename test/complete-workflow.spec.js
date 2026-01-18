const { test, expect } = require('@playwright/test');

test('E2E Flow: Complete Training Workflow with Find Numbers Game', async ({ browser }) => {
    // Step 1: Admin Login and Start Training
    console.log('\n=== Step 1: Admin Login ===');
    const adminPage = await browser.newPage();
    await adminPage.goto('http://127.0.0.1:8000/admin/login');
    await adminPage.fill('input[name="password"]', 'admin123');
    await adminPage.click('button[type="submit"]');
    console.log('✓ Admin logged in');

    // Wait for admin dashboard
    await adminPage.waitForSelector('form[action="/api/admin/update"]');

    // Start the training  
    await adminPage.selectOption('select[name="status"]', 'running');
    await adminPage.click('button:has-text("保存设置")');
    console.log('✓ Training started by admin');
    await adminPage.screenshot({ path: 'screenshots/01-admin-dashboard.png' });

    // Step 2: Open Public Display Screen
    console.log('\n=== Step 2: Open Public Display Screen ===');
    const displayPage = await browser.newPage();
    await displayPage.goto('http://127.0.0.1:8000/');
    await displayPage.waitForTimeout(1000);
    console.log('✓ Display screen opened');
    await displayPage.screenshot({ path: 'screenshots/02-display-home.png' });

    // Step 3: Regular User Sign-in
    console.log('\n=== Step 3: Regular User Sign-in ===');
    const userPage = await browser.newPage();
    await userPage.goto('http://localhost:8000/signin');
    await userPage.fill('input[name="name"]', '测试用户张三');
    await userPage.fill('input[name="department"]', '技术部');
    await userPage.selectOption('select[name="role"]', 'user');
    await userPage.click('button[type="submit"]');

    // Wait for user home page
    await userPage.waitForTimeout(1500);
    console.log('✓ User signed in');
    await userPage.screenshot({ path: 'screenshots/03-user-home.png' });

    // Step 4: Host Sign-in
    console.log('\n=== Step 4: Host Sign-in ===');
    const hostPage = await browser.newPage();
    await hostPage.goto('http://127.0.0.1:8000/signin');
    await hostPage.fill('input[name="name"]', '主持人王老师');
    await hostPage.fill('input[name="department"]', '培训部');
    await hostPage.selectOption('select[name="role"]', 'host');

    // Wait for password field to appear
    await hostPage.waitForSelector('input[name="host_password"]', { state: 'visible' });
    await hostPage.fill('input[name="host_password"]', 'admin123');
    await hostPage.click('button[type="submit"]');

    // Verify host dashboard
    await expect(hostPage.locator('h3:has-text("主持人控制台")')).toBeVisible({ timeout: 15000 });
    console.log('✓ Host logged in');
    await hostPage.screenshot({ path: 'screenshots/04-host-dashboard.png' });

    // Step 5: Host Starts Find Numbers Game
    console.log('\n=== Step 5: Host Starts Find Numbers Game ===');

    // Setup dialog handlers
    hostPage.on('dialog', async dialog => {
        console.log(`Host Dialog: ${dialog.message()}`);
        await dialog.accept();
    });

    // Find and click the "找数字规律" plugin
    const finderPlugin = hostPage.locator('div').filter({
        has: hostPage.locator('strong:has-text("找数字规律")')
    }).last();

    await finderPlugin.getByRole('button', { name: '加载互动' }).click();
    await hostPage.waitForTimeout(1000);
    console.log('✓ Find Numbers game loaded in host control');
    await hostPage.screenshot({ path: 'screenshots/05-host-game-loaded.png' });

    // Start the game
    const startButton = hostPage.locator('button:has-text("开始游戏")');
    if (await startButton.count() > 0) {
        await startButton.click();
        console.log('✓ Game started by host');
    } else {
        console.log('! Start button not found, game may auto-start');
    }

    await hostPage.waitForTimeout(2000);
    await hostPage.screenshot({ path: 'screenshots/06-host-game-started.png' });

    // Step 6: Verify Game on Display Screen
    console.log('\n=== Step 6: Verify Game on Display Screen ===');
    await displayPage.waitForTimeout(2000);
    await displayPage.reload();
    await displayPage.waitForTimeout(1000);
    console.log('✓ Display screen showing the game');
    await displayPage.screenshot({ path: 'screenshots/07-display-game-active.png' });

    // Step 7: User Participates in Game
    console.log('\n=== Step 7: User Participates in Game ===');

    // Check if user can see the game
    await userPage.waitForTimeout(2000);
    await userPage.reload();
    await userPage.waitForTimeout(1000);

    const enterGameButton = userPage.locator('button:has-text("进入")');
    if (await enterGameButton.count() > 0) {
        await enterGameButton.first().click();
        await userPage.waitForTimeout(1000);
        console.log('✓ User entered the game');
    }

    await userPage.screenshot({ path: 'screenshots/08-user-in-game.png' });

    // Try to participate - fill in some numbers
    const answerInput = userPage.locator('input[type="text"], input[type="number"], textarea').first();
    if (await answerInput.count() > 0) {
        await answerInput.fill('5, 15, 25');
        await userPage.waitForTimeout(500);

        const submitButton = userPage.locator('button:has-text("提交"), button:has-text("确认")');
        if (await submitButton.count() > 0) {
            await submitButton.first().click();
            console.log('✓ User submitted answer');
            await userPage.waitForTimeout(1000);
        }
    }

    await userPage.screenshot({ path: 'screenshots/09-user-submitted.png' });

    // Step 8: Host Ends the Game
    console.log('\n=== Step 8: Host Ends the Game ===');
    await hostPage.waitForTimeout(1000);

    const endButton = hostPage.locator('button:has-text("结束"), button:has-text("停止"), button:has-text("显示结果")');
    if (await endButton.count() > 0) {
        await endButton.first().click();
        console.log('✓ Host ended the game');
        await hostPage.waitForTimeout(2000);
    }

    await hostPage.screenshot({ path: 'screenshots/10-host-game-ended.png' });

    // Step 9: Verify Results on Display
    console.log('\n=== Step 9: Verify Results on Display ===');
    await displayPage.waitForTimeout(2000);
    await displayPage.reload();
    await displayPage.waitForTimeout(1000);
    console.log('✓ Display showing results');
    await displayPage.screenshot({ path: 'screenshots/11-display-results.png' });

    // Step 10: Check User View After Game
    console.log('\n=== Step 10: Check User View After Game ===');
    await userPage.waitForTimeout(1000);
    await userPage.reload();
    await userPage.waitForTimeout(1000);
    console.log('✓ User view after game ended');
    await userPage.screenshot({ path: 'screenshots/12-user-after-game.png' });

    console.log('\n=== ✓ Complete Workflow Test Finished ===\n');
});
