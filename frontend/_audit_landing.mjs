import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import path from 'path';

const url = pathToFileURL(path.resolve('landing_new.html')).href;
const browser = await chromium.launch({ headless: true });

const errors = [];
const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 900, height: 1000 },
  { name: 'mobile', width: 390, height: 844 },
];

for (const vp of viewports) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push(`[${vp.name}] pageerror: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') errors.push(`[${vp.name}] console: ${m.text()}`); });

  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(600);
  // desplegar todo el reveal para que el fullPage no salga en blanco
  await page.evaluate(() => document.querySelectorAll('.reveal').forEach(e => e.classList.add('is-visible')));
  await page.waitForTimeout(400);

  await page.screenshot({ path: `_audit-${vp.name}.png`, fullPage: true });

  // desbordamiento horizontal
  const overflow = await page.evaluate(() => {
    const de = document.documentElement;
    const wide = [...document.querySelectorAll('body *')]
      .filter(el => el.getBoundingClientRect().right > de.clientWidth + 1)
      .slice(0, 5)
      .map(el => el.tagName + '.' + (el.className || '').toString().slice(0, 40));
    return { scrollW: de.scrollWidth, clientW: de.clientWidth, wide };
  });
  if (overflow.scrollW > overflow.clientW + 1) {
    errors.push(`[${vp.name}] overflow horizontal ${overflow.scrollW}>${overflow.clientW} :: ${overflow.wide.join(' | ')}`);
  }
  await ctx.close();
}

// contraste de texto pequeno sobre su fondo
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
await page.goto(url, { waitUntil: 'load' });
const contrast = await page.evaluate(() => {
  const lum = (r, g, b) => {
    const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const parse = s => (s.match(/[\d.]+/g) || []).map(Number);
  const over = (fg, bg) => { // fg puede tener alpha
    const a = fg[3] === undefined ? 1 : fg[3];
    return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a));
  };
  const bgOf = el => {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c.length && (c[3] === undefined || c[3] > 0.9)) return c.slice(0, 3);
      n = n.parentElement;
    }
    return [255, 255, 255];
  };
  const out = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    const txt = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!txt) continue;
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize);
    const fg = over(parse(cs.color), bgOf(el));
    const bg = bgOf(el);
    const L1 = lum(...fg), L2 = lum(...bg);
    const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const large = size >= 24 || (size >= 18.66 && parseInt(cs.fontWeight) >= 700);
    const min = large ? 3 : 4.5;
    if (ratio < min) {
      const key = el.className + size;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ sel: el.tagName + '.' + (el.className || ''), size, ratio: +ratio.toFixed(2), min, text: el.textContent.trim().slice(0, 45) });
    }
  }
  return out;
});
await ctx.close();
await browser.close();

console.log('=== ERRORES / OVERFLOW ===');
console.log(errors.length ? errors.join('\n') : 'ninguno');
console.log('\n=== CONTRASTE INSUFICIENTE (WCAG AA) ===');
console.log(contrast.length ? contrast.map(c => `${c.ratio}:1 (min ${c.min}) ${c.size}px  ${c.sel}  "${c.text}"`).join('\n') : 'ninguno');
