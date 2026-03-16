import { chromium } from 'playwright';

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const baseUrl = 'http://127.0.0.1:8514';

async function extractRoutes(page) {
  return page.locator('a').evaluateAll((anchors) =>
    anchors.map((anchor) => ({
      text: (anchor.textContent || '').trim(),
      href: anchor.getAttribute('href') || '',
    })),
  );
}

async function openRoute(page, routeMap, label) {
  const entry = routeMap.find((item) => item.text === label && item.href);
  if (!entry) {
    throw new Error(`Missing route for ${label}`);
  }
  await page.goto(new URL(entry.href, baseUrl).toString(), { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForTimeout(9000);
}

async function capture(page, path) {
  const target = page.locator('[data-testid="stAppViewContainer"]');
  await target.screenshot({ path });
}

const pages = [
  ['Landing', 'review-home-priority.png'],
  ['Dashboard', 'review-dashboard-priority.png'],
  ['Global Climate Map', 'review-global-map-priority.png'],
  ['Risk Intelligence', 'review-risk-priority.png'],
];

(async () => {
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage({ viewport: { width: 1700, height: 2600 } });
  await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForTimeout(9000);
  const routeMap = await extractRoutes(page);

  await capture(page, 'review-home-priority.png');
  for (const [label, output] of pages.slice(1)) {
    await openRoute(page, routeMap, label);
    await capture(page, output);
  }

  await browser.close();
})();
