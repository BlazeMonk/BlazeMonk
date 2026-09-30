// Quick screenshot of an SVG at a given width; optional animation time (ms) and colour scheme.
import { createRequire } from 'node:module';
const require = createRequire('/Users/allangarbagnati/Blaze-PROD/blaze/node_modules/.pnpm/playwright-core@1.63.0/node_modules/playwright-core/package.json');
const { chromium } = require('./index.js');
const [file, out, w = '1200', scheme = 'light', t = ''] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: +w, height: Math.round(+w * 0.3) }, colorScheme: scheme, deviceScaleFactor: 2 });
await p.goto('file://' + file);
if (t) await p.evaluate((ms) => document.getAnimations().forEach((a) => { a.pause(); a.currentTime = +ms; }), t);
else await p.waitForTimeout(6000);
await p.screenshot({ path: out, timeout: 20000 });
await b.close();
