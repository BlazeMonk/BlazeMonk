// Local preview that mimics GitHub's README rendering (light and dark) plus a mid-animation header frame.
// Usage: gh api -X POST /markdown -F mode=gfm -F text=@README.md > preview/body.html   (done by tools/preview.sh)
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire('/Users/allangarbagnati/Blaze-PROD/blaze/node_modules/.pnpm/playwright-core@1.63.0/node_modules/playwright-core/package.json');
const { chromium } = require('./index.js');
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const body = fs.readFileSync(path.join(root, 'preview/body.html'), 'utf8')
  .replace(/(src|srcset)="assets\//g, `$1="file://${root}/assets/`);
const css = (dark) => `
body{margin:0;background:${dark ? '#0d1117' : '#fff'};color:${dark ? '#f0f6fc' : '#1f2328'};
 font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif}
.box{box-sizing:border-box;width:1012px;padding:32px;margin:0 auto}
.md{border:1px solid ${dark ? '#3d444d' : '#d1d9e0'};border-radius:6px;padding:32px;box-sizing:border-box}
.md h1,.md h2,.md h3{font-weight:600;line-height:1.25;margin:24px 0 16px}
.md h2{font-size:1.5em;padding-bottom:.3em;border-bottom:1px solid ${dark ? '#3d444d' : '#d1d9e0'}}
.md h3{font-size:1.25em}
.md p{margin:0 0 16px} .md img{max-width:100%;box-sizing:content-box}
.md a{color:${dark ? '#4493f8' : '#0969da'};text-decoration:none}
.md hr{height:.25em;border:0;background:${dark ? '#3d444d' : '#d1d9e0'};margin:24px 0}`;
const page = (dark) => `<!doctype html><meta charset=utf-8><style>${css(dark)}</style><div class=box><div class=md>${body}</div></div>`;
const b = await chromium.launch();
for (const scheme of ['light', 'dark']) {
  const p = await b.newPage({ viewport: { width: 1012, height: 900 }, colorScheme: scheme });
  const f = path.join(root, `preview/page-${scheme}.html`);
  fs.writeFileSync(f, page(scheme === 'dark'));
  await p.goto('file://' + f);
  await p.waitForLoadState('networkidle').catch(() => {});
  await p.waitForTimeout(14000);
  await p.screenshot({ path: path.join(root, `preview/readme-${scheme}.png`), fullPage: true, animations: 'allow', timeout: 60000 });
  await p.close();
}
// header mid-animation (t = 1.4 s), light and dark
for (const scheme of ['light', 'dark']) {
  const p = await b.newPage({ viewport: { width: 1200, height: 340 }, colorScheme: scheme });
  await p.goto('file://' + path.join(root, `assets/header-${scheme}.svg`));
  await p.evaluate(() => document.getAnimations().forEach((a) => { a.pause(); a.currentTime = 1400; }));
  await p.screenshot({ path: path.join(root, `preview/header-midanimation-${scheme}.png`), timeout: 20000 });
  await p.close();
}
await b.close();
