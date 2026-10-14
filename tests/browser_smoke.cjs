/* Desktop and mobile smoke test. Needs Playwright with Chromium (CI installs it).
   Loads the built page from disk and blocks every network request, so it never
   contacts a retailer or ChatGPT. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    for (const viewport of [{width: 1440, height: 1000}, {width: 390, height: 844}]) {
      const context = await browser.newContext({viewport});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route(/^https?:/, route => route.abort());
      await page.goto(pathToFileURL(path.resolve('ski-deals/index.html')).href);
      await page.waitForSelector('#list article, #list .empty');

      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, 'no horizontal overflow');
      assert.equal(await page.locator('[data-category="ski"]').getAttribute('aria-pressed'), 'true', 'Skis is the default category');
      assert.equal(await page.locator('#brief h2').isVisible(), true, 'the brief is on the main page');
      assert.ok((await page.locator('#brief .b-sec').count()) >= 1, 'the brief has at least one section');

      const kindsShown = () => page.evaluate(() => [...document.querySelectorAll('#list article')]
        .map(el => window.GEAR.dataset.items.find(i => i.id === el.dataset.id).kind));
      await page.locator('[data-view="all"]').click();
      const skiKinds = await kindsShown();
      assert.ok(skiKinds.length > 0, 'skis are listed');
      assert.ok(skiKinds.every(k => k === 'ski'), 'only skis in the Skis view');

      await page.locator('[data-category="clothing"]').click();
      assert.equal(await page.locator('[data-category="clothing"]').getAttribute('aria-pressed'), 'true');
      const clothingKinds = await kindsShown();
      assert.ok(clothingKinds.every(k => k === 'clothing'), 'only clothing in the Clothing view');

      await page.reload();
      await page.waitForSelector('#list article, #list .empty');
      assert.equal(await page.locator('[data-category="ski"]').getAttribute('aria-pressed'), 'true', 'a reload opens on Skis again');

      await page.locator('#openPrefs').click();
      await page.locator('[name="budget"]').fill('250');
      await page.locator('#prefsSave').click();
      const overBudget = await page.evaluate(() => [...document.querySelectorAll('#list article')]
        .map(el => window.GEAR.dataset.items.find(i => i.id === el.dataset.id))
        .filter(i => window.GearApp && i._fit && (i._fit.price || i.price) > 250).length);
      assert.equal(overBudget, 0, 'For you respects an edited budget');
      await page.locator('#openPrefs').click();
      await page.locator('#prefsReset').click();

      await page.locator('#search').fill('NO_SUCH_SKI_987654321');
      await page.waitForSelector('.empty');
      await page.locator('#emptyAll').click();
      assert.equal(await page.locator('#search').inputValue(), '');

      const first = page.locator('#list article').first();
      if (await first.count()) {
        await first.locator('[data-act="save"]').click();
        await page.locator('[data-view="saved"]').click();
        assert.ok((await page.locator('#list article').count()) >= 1, 'saved listing appears under Saved');
      }

      await page.locator('[data-category="ski"]').click();
      if (await page.locator('#openStudio').count()) {
        await page.locator('#openStudio').click();
        await page.locator('#reply').fill('{"snapshot_id":"wrong","headline":"x"}');
        await page.locator('#checkReply').click();
        assert.match(await page.locator('#studioResult').innerText(), /Not accepted/);
        await page.keyboard.press('Escape');
      }
      await page.screenshot({path: `/tmp/gear-${viewport.width}.png`, fullPage: false});
      assert.deepEqual(errors, [], 'no JavaScript errors');
      await context.close();
    }
    console.log('Desktop and mobile smoke tests passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
