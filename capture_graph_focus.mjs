import { chromium } from 'playwright';

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const baseUrl = 'http://127.0.0.1:8513';

async function extractRoutes(page) {
  return page.locator('a').evaluateAll((anchors) => {
    return anchors
      .map((anchor) => ({
        text: (anchor.textContent || '').trim(),
        href: anchor.getAttribute('href') || '',
      }))
      .filter((item) => item.href);
  });
}

async function openRoute(page, routeMap, label) {
  const entry = routeMap.find((item) => item.text === label && item.href);
  if (!entry) {
    throw new Error(`Could not resolve route for ${label}`);
  }
  await page.goto(entry.href, { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(5000);
}

async function capturePage(page, routeMap, label, path) {
  await openRoute(page, routeMap, label);
  await page.screenshot({ path, fullPage: true });
}

async function main() {
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage({ viewport: { width: 1800, height: 1800 } });
  await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(5000);
  const routeMap = await extractRoutes(page);

  await capturePage(page, routeMap, 'Dashboard', 'review-dashboard-focus.png');
  await capturePage(page, routeMap, 'Climate Signals', 'review-signals-focus.png');
  await capturePage(page, routeMap, 'Risk Intelligence', 'review-risk-focus.png');
  await capturePage(page, routeMap, 'AI Predictions', 'review-predictions-focus.png');

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
