import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';
const SECTIONS = ['dashboard', 'empleados', 'calendario', 'turnos', 'fichajes', 'vacaciones', 'bajas', 'informes', 'configuracion'];

async function takeScreenshots(prefix = 'before') {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Navigate and login
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Check if we're on login screen
  const loginVisible = await page.locator('#login-screen').isVisible();
  console.log('Login screen visible:', loginVisible);

  // Click demo button using JS directly
  await page.evaluate(() => {
    const btn = document.getElementById('demo-btn');
    if (btn) {
      console.log('Demo btn found, clicking...');
      btn.click();
    } else {
      console.log('Demo btn NOT found');
    }
  });
  await page.waitForTimeout(2000);

  // Check if app is visible
  const appVisible = await page.locator('#app').isVisible();
  console.log('App visible after demo click:', appVisible);

  // If app is still hidden, try direct state manipulation
  if (!appVisible) {
    console.log('Trying direct state manipulation...');
    await page.evaluate(() => {
      state.token = 'demo-token';
      state.user = { name: 'Demo', email: 'demo@talentup.es', role: 'owner', tenant_id: 'demo' };
      state.isDemo = true;
      enterApp();
    });
    await page.waitForTimeout(2000);
  }

  const appVisible2 = await page.locator('#app').isVisible();
  console.log('App visible after direct:', appVisible2);

  for (const section of SECTIONS) {
    // Click nav item
    const navItem = page.locator(`.nav-item[data-page="${section}"]`);
    if (await navItem.isVisible()) {
      await navItem.click();
      await page.waitForTimeout(2000); // Wait for data to load
    }
    await page.screenshot({
      path: `/d/tmp/${prefix}-${section}.png`,
      fullPage: false
    });
    console.log(`  ✓ ${prefix}-${section}.png`);
  }

  await browser.close();
}

console.log('Taking ' + process.argv[2] + ' screenshots...');
takeScreenshots(process.argv[2] || 'before').then(() => console.log('DONE')).catch(e => console.error('ERROR:', e));
