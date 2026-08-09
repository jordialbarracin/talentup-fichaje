import { chromium } from 'playwright';

const base = 'file:///C:/Users/jordi/talentup-fichaje/frontend/';
const shots = [
  ['landing_new.html',   1440, 900, 'shot-landing-desktop.png', false],
  ['landing_new.html',    390, 844, 'shot-landing-mobile.png',  false],
  ['dashboard_new.html', 1440, 900, 'shot-dash-desktop.png',    false],
  ['dashboard_new.html',  900, 800, 'shot-dash-rail.png',       false],
  ['dashboard_new.html',  390, 844, 'shot-dash-mobile.png',     false],
];

const b = await chromium.launch();
for (const [file, w, h, out, full] of shots) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.goto(base + file);
  await p.waitForTimeout(1800);
  const overflow = await p.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await p.screenshot({ path: out, fullPage: full });
  console.log(out, '| overflow-x:', overflow, '| errores:', errs.length ? errs.join(' // ') : 'ninguno');
  await p.close();
}
await b.close();
