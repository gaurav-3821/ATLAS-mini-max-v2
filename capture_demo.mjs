import { chromium } from 'playwright';

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const baseUrl = 'http://127.0.0.1:8513';

async function extractRoutes(page) {
  return page.locator('a').evaluateAll((anchors) => {
    return anchors.map((anchor) => ({
      text: (anchor.textContent || '').trim(),
      href: anchor.getAttribute('href') || '',
    }));
  });
}

async function openRoute(page, routeMap, label) {
  const entry = routeMap.find((item) => item.text === label && item.href);
  const href = entry?.href;
  if (!href) {
    throw new Error(`Could not resolve href for page link: ${label}`);
  }
  await page.goto(new URL(href, baseUrl).toString(), { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(5000);
}

async function main() {
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage({ viewport: { width: 1540, height: 1400 } });
  await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(5000);
  const routeMap = await extractRoutes(page);
  await page.screenshot({ path: 'review-home.png', fullPage: true });

  await openRoute(page, routeMap, 'Dashboard');
  await page.screenshot({ path: 'review-dashboard.png', fullPage: true });

  await openRoute(page, routeMap, 'Climate Signals');
  await page.screenshot({ path: 'review-signals.png', fullPage: true });

  await openRoute(page, routeMap, 'Global Climate Map');
  await page.screenshot({ path: 'review-global-map.png', fullPage: true });

  await openRoute(page, routeMap, 'Risk Intelligence');
  await page.screenshot({ path: 'review-risk.png', fullPage: true });

  await openRoute(page, routeMap, 'AI Predictions');
  await page.screenshot({ path: 'review-predictions.png', fullPage: true });

  await openRoute(page, routeMap, 'Data Explorer');
  await page.screenshot({ path: 'review-explorer.png', fullPage: true });

  await openRoute(page, routeMap, 'Settings');
  await page.screenshot({ path: 'review-settings.png', fullPage: true });

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
