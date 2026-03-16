import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 2200 } });
  await page.addInitScript(() => {
    localStorage.setItem('atlas_theme', 'dark_mode');
  });
  await page.goto('http://127.0.0.1:5000', { waitUntil: 'networkidle', timeout: 120000 });
  await page.screenshot({ path: 'frontend-dashboard-dark.png', fullPage: true });
  await page.click('#theme-toggle');
  await page.waitForTimeout(700);
  await page.screenshot({ path: 'frontend-dashboard-light.png', fullPage: true });
  await browser.close();
})();
