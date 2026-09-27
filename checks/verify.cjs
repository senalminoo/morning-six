const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.MORNING_SIX_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, 'data/matches.js'), 'utf8'), sandbox);
const data = sandbox.window.MORNING_SIX_DATA;
const big6 = ['arsenal', 'tottenham', 'chelsea', 'liverpool', 'city', 'united'];
const expectedCodes = {arsenal:3, united:1, city:43, chelsea:8, liverpool:14, tottenham:6,
  'aston-villa':7,bournemouth:91,brentford:94,brighton:36,burnley:90,'crystal-palace':31,
  everton:11,fulham:54,leeds:2,newcastle:4,'nottingham-forest':17,sunderland:56,'west-ham':21,wolves:39};
assert.equal(data.matches.length, 380);
const targets = data.matches.filter(m => big6.includes(m.home) || big6.includes(m.away));
assert.equal(targets.length, 198);
assert.equal(new Set(targets.flatMap(m => m.videos.map(v => v.url))).size, 198);
for (const match of targets) {
  assert.equal(match.videos.length, 1);
  assert.match(match.videos[0].url, /^https:\/\/www\.youtube\.com\/watch\?v=[\w-]{11}$/);
  assert.equal(match.videos[0].channelId, 'UCnBht7BrOx-A328KFXgysqQ');
}
for (const [id, code] of Object.entries(expectedCodes)) {
  assert.equal(data.teams[id].crestCode, code, id);
  assert.ok(fs.existsSync(path.join(root, data.teams[id].crestUrl)));
}
const playerAssets = JSON.parse(fs.readFileSync(path.join(root, 'data/players.json'), 'utf8'));
assert.deepEqual(Object.keys(playerAssets).sort(), big6.slice().sort());
for (const player of Object.values(playerAssets)) assert.ok(fs.existsSync(path.join(root, player.path)), player.path);

(async () => {
  const artifacts = path.join(root, 'artifacts');
  fs.mkdirSync(artifacts, { recursive: true });
  const crests = JSON.parse(fs.readFileSync(path.join(root, 'data/crests.json'), 'utf8'));
  fs.writeFileSync(path.join(artifacts, 'crests.html'), '<!doctype html><meta charset="utf-8"><title>Club crest check</title><style>body{font:15px Arial;background:#f6f7f2;margin:24px;color:#243b32}main{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}article{background:white;border:1px solid #dde3d7;border-radius:12px;padding:16px;text-align:center}img{width:80px;height:90px;object-fit:contain}p{margin:10px 0 0}</style><main>' + Object.entries(crests).map(([id, crest]) => `<article><img src="../${crest.path}" alt="${id}"><p>${crest.name}</p><small>t${crest.code}</small></article>`).join('') + '</main>');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 920 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(path.join(artifacts, 'crests.html')).href);
    const assets = await page.locator('img').evaluateAll(images => images.map(i => ({name:i.alt, ok:i.complete && i.naturalWidth > 0})));
    assert.equal(assets.length, 20);
    assert.ok(assets.every(a => a.ok), JSON.stringify(assets));
    await page.screenshot({ path: path.join(artifacts, 'crests.png') });
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href + '#matches');
    await page.waitForFunction(() => document.querySelectorAll('.official-video').length === 20);
    const firstDetails = page.locator('.match-card details').first();
    assert.equal(await firstDetails.getAttribute('open'), '');
    await firstDetails.locator('summary').click();
    assert.equal(await firstDetails.getAttribute('open'), null);
    await firstDetails.locator('summary').click();
    assert.equal(await firstDetails.getAttribute('open'), '');
    assert.match(await page.locator('#results-line').innerText(), /198\/198/);
    assert.equal(await page.locator('#video-count').innerText(), '198');
    assert.equal(await page.locator('.ace-card').count(), 6);
    const aceImages = await page.locator('.ace-card img').evaluateAll(images => images.map(image => image.complete && image.naturalWidth > 0));
    assert.ok(aceImages.every(Boolean), JSON.stringify(aceImages));
    await page.locator('.ace-card[data-hero-team="arsenal"]').click();
    assert.equal(await page.locator('#match-count').innerText(), '38');
    await page.locator('[data-team="big6"]').click();
    assert.equal(await page.locator('#view-mode-box').count(), 1);
    assert.equal(await page.locator('#filter-value-box').count(), 1);
    const initialBoxes = await page.locator('.view-switch-button').evaluateAll(buttons => buttons.map(button => {
      const box = button.getBoundingClientRect();
      return { width: box.width, height: box.height };
    }));
    assert.ok(initialBoxes.every(box => box.width >= 64 && box.height <= 40), JSON.stringify(initialBoxes));
    await page.getByRole('button', { name: '라운드별' }).click();
    assert.equal(await page.locator('#digest-filter option').first().innerText(), '전체 라운드');
    assert.equal(await page.locator('#digest-filter option').count(), 39);
    await page.locator('#digest-filter').selectOption('31');
    assert.match(await page.locator('#results-line').innerText(), /31라운드/);
    await page.getByRole('button', { name: '날짜별' }).click();
    assert.equal(await page.locator('#digest-filter option').first().innerText(), '전체 날짜');
    assert.ok((await page.locator('#digest-filter option').count()) > 39);
    await page.screenshot({ path: path.join(artifacts, 'desktop.png') });
    for (const team of big6) {
      await page.locator(`[data-team="${team}"]`).click();
      assert.equal(await page.locator('#match-count').innerText(), '38');
      assert.equal(await page.locator('#video-count').innerText(), '38');
      await page.getByRole('button', { name: '다음 18경기 보기' }).click();
      assert.equal(await page.locator('.match-card .official-video').count(), 38);
      const hrefs = await page.locator('.match-card .official-video').evaluateAll(links => links.map(a => a.href));
      assert.ok(hrefs.every(h => /^https:\/\/www\.youtube\.com\/watch\?v=[\w-]{11}$/.test(h)));
    }
    await page.locator('[data-team="all"]').click();
    assert.equal(await page.locator('#match-count').innerText(), '380');
    await page.locator('[data-team="big6"]').click();
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({ path: path.join(artifacts, 'mobile.png') });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Mobile horizontal overflow');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({matches:380, targets:198, links:198, crests:20, teamFilters:'6 x 38 links', consoleErrors:errors.length, mobileOverflow:false}));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
