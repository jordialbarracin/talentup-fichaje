import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';

async function takeDashboardScreenshot() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Navigate to login
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Click "Entrar modo demo" button
  const demoBtn = page.locator('#demo-btn');
  if (await demoBtn.isVisible()) {
    console.log('Demo button found, clicking...');
    await demoBtn.click();
    await page.waitForTimeout(2000);
  } else {
    console.log('Demo button NOT found, trying JS click...');
    await page.evaluate(() => {
      const btn = document.getElementById('demo-btn');
      if (btn) btn.click();
    });
    await page.waitForTimeout(2000);
  }

  // Check if app is visible
  const appVisible = await page.locator('#app').isVisible();
  console.log('App visible:', appVisible);

  // If not visible, try direct state manipulation
  if (!appVisible) {
    console.log('Trying direct state manipulation...');
    await page.evaluate(() => {
      if (typeof state !== 'undefined') {
        state.token = 'demo-token';
        state.user = { name: 'Demo', email: 'demo@talentup.es', role: 'owner', tenant_id: 'demo' };
        state.isDemo = true;
        if (typeof enterApp === 'function') enterApp();
      }
    });
    await page.waitForTimeout(2000);
  }

  // Take dashboard screenshot
  await page.screenshot({ path: '/tmp/dashboard-1440.png', fullPage: false });
  console.log('✓ dashboard-1440.png');

  await browser.close();
}

takeDashboardScreenshot().then(() => console.log('DONE')).catch(e => console.error('ERROR:', e));
