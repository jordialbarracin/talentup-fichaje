import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';

async function takeAllScreenshots() {
  const browser = await chromium.launch({ headless: true });
  
  // 1. Landing page 1440x900
  let context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  let page = await context.newPage();
  await page.goto(BASE + '/landing.html', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/c/tmp/landing-1440.png', fullPage: false });
  console.log('✓ landing-1440.png');
  await context.close();

  // 2. Login page 1440x900
  context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await context.newPage();
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/c/tmp/login-1440.png', fullPage: false });
  console.log('✓ login-1440.png');
  await context.close();

  // 3. PWA mobile 375x812
  context = await browser.newContext({ viewport: { width: 375, height: 812 } });
  page = await context.newPage();
  await page.goto(BASE + '/mobile/index.html', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/c/tmp/pwa-mobile-375.png', fullPage: false });
  console.log('✓ pwa-mobile-375.png');
  await context.close();

  await browser.close();
  console.log('ALL DONE');
}

takeAllScreenshots().catch(e => console.error('ERROR:', e));
