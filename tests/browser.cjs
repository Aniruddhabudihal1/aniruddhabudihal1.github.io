// Optional browser checks. Install Playwright outside the site's build dependencies.
// SITE_URL=http://127.0.0.1:4000/budihal_logs.github.io/ NODE_PATH=/path/to/node_modules node tests/browser.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
    args: ['--no-sandbox'],
  });
  const base = process.env.SITE_URL || 'http://127.0.0.1:4000/budihal_logs.github.io/';
  const context = await browser.newContext({ colorScheme: 'dark' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base);
  await page.waitForSelector('.theme-toggle:not([hidden])');
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  await page.getByRole('button', { name: 'Switch to light theme' }).click();
  await page.reload();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  await page.emulateMedia({ colorScheme: 'dark' });
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  await page.evaluate(() => localStorage.removeItem('budihal-theme'));
  await page.reload();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  await page.emulateMedia({ colorScheme: 'light' });
  await page.waitForFunction(() => document.documentElement.dataset.theme === 'light');
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');

  for (const path of ['', 'blogs/', 'cool-stuff/', 'music/', 'contact/', 'now/', '2026-07-24-cow-filesystem-fuse-rust/']) {
    for (const width of [320, 375, 768, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      const response = await page.goto(base + path);
      assert.equal(response.status(), 200);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow at ${path}, ${width}px`);
      assert.equal(await page.locator('h1').count(), 1);
    }
  }
  await page.goto(base);
  await page.locator('.tag-filter summary').click();
  await page.getByText('rust', { exact: true }).click();
  assert(await page.getByRole('checkbox', { name: 'rust', exact: true }).isChecked());
  await page.getByText('systems', { exact: true }).click();
  assert.equal(await page.locator('.filter-count').textContent(), '(2)');
  assert.equal(await page.locator('.writing-entry:visible').count(), 1);
  await page.getByRole('button', { name: 'Clear selection' }).click();
  assert.equal(await page.locator('.tag-option input:checked').count(), 0);
  // Exercise the no-results branch without adding a fabricated post to the real site.
  await page.locator('.writing-entry').evaluate(entry => { entry.dataset.tags = '[]'; });
  await page.getByRole('checkbox', { name: 'rust', exact: true }).focus();
  await page.keyboard.press('Space');
  assert(await page.locator('.filter-empty').isVisible());
  await page.getByRole('button', { name: 'Clear selection' }).click();
  assert.equal(await page.locator('.writing-entry:visible').count(), 1);

  await page.clock.install();
  const track = { name: 'Fixture track', artist: 'Fixture artist', album: '', url: 'https://www.last.fm/music/test', image: '', now_playing: true };
  await page.route('**/assets/data/lastfm.json', route => route.fulfill({ json: { updated_at: new Date().toISOString(), tracks: [track] } }));
  await page.goto(base);
  await page.waitForFunction(() => document.querySelector('[data-lastfm]').textContent.includes('Fixture track'));
  assert.match(await page.locator('[data-lastfm]').textContent(), /♫ Fixture track · Fixture artist/);
  // An already-open page must pick up a newly deployed snapshot without reload.
  await page.route('**/assets/data/lastfm.json', route => route.fulfill({ json: {
    updated_at: new Date().toISOString(), tracks: [{ ...track, name: 'Next track' }],
  } }));
  await page.clock.runFor(60 * 1000);
  await page.waitForFunction(() => document.querySelector('[data-lastfm]').textContent.includes('Next track'));
  await page.route('**/assets/data/lastfm.json', route => route.abort());
  await page.clock.runFor(60 * 1000);
  assert.match(await page.locator('[data-lastfm]').textContent(), /Next track/);
  await page.route('**/assets/data/lastfm.json', route => route.fulfill({ json: { updated_at: new Date().toISOString(), tracks: [track] } }));
  await page.goto(base + 'music/');
  await page.waitForSelector('.track-list');
  assert.equal(await page.locator('.track-list img').count(), 0);
  await page.route('**/assets/data/lastfm.json', route => route.fulfill({ json: { updated_at: '2020-01-01T00:00:00Z', tracks: [track] } }));
  await page.goto(base);
  await page.waitForFunction(() => document.querySelector('[data-lastfm]').textContent.includes('Fixture track'));
  assert(!(await page.locator('[data-lastfm]').textContent()).includes('♫'));
  await page.route('**/assets/data/lastfm.json', route => route.abort());
  await page.goto(base + 'music/');
  await page.waitForTimeout(100);
  assert.match(await page.locator('[data-lastfm]').textContent(), /unavailable/);

  await page.goto(base + '2026-07-24-cow-filesystem-fuse-rust/');
  assert(await page.locator('[data-toc] li').count() > 0);
  const images = await page.locator('.article-body img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0));
  assert(images, 'Article images must load');
  assert.deepEqual(errors, []);
  await page.setViewportSize({ width: 1280, height: 1000 });
  await page.goto(base);
  await page.screenshot({ path: '/tmp/budihal-home-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.screenshot({ path: '/tmp/budihal-home-mobile.png', fullPage: true });

  const nojs = await browser.newContext({ javaScriptEnabled: false });
  const staticPage = await nojs.newPage();
  await staticPage.goto(base + 'blogs/');
  assert.equal(await staticPage.locator('.writing-entry:visible').count(), 1);
  assert.equal(await staticPage.locator('.tag-filter:visible').count(), 0);
  assert.deepEqual(errors, []);
  console.log('Browser checks passed: themes, persistence, system changes, navigation, 4 viewport sizes, filters/keyboard, Last.fm fixtures/failure, article assets/TOC, and no-JS reading.');
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
