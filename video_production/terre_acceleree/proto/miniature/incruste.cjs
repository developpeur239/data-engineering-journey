// node miniature/incruste.cjs image.png "GRAND" "ligne orange" sortie.jpg  → compteur du film incrusté sur une image
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [img, grand, orange, out] = process.argv.slice(2);
const ROOT = path.join(__dirname, '..');
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  if (u === '/') { r.writeHead(200, { 'Content-Type': 'text/html' }); r.end(`<!doctype html><meta charset=utf-8><style>
    @font-face { font-family: Serif4; src: url(node_modules/@fontsource/source-serif-4/files/source-serif-4-latin-300-normal.woff2); font-weight: 300; }
    @font-face { font-family: InterW; src: url(node_modules/@fontsource/inter/files/inter-latin-600-normal.woff2); font-weight: 600; }
    body{margin:0;width:1920px;height:1080px;background:url(/img) center/cover;overflow:hidden}
    #v{position:fixed;left:0;top:0;width:1250px;height:640px;background:radial-gradient(ellipse at 0% 0%, rgba(4,18,42,.72) 0%, rgba(4,18,42,.45) 45%, rgba(4,18,42,0) 72%)}
    #t{position:fixed;left:70px;top:62px;color:#fff;text-shadow:0 3px 18px rgba(0,0,0,.6)}
    </style><div id=v></div><div id=t><div style="font:600 46px InterW;letter-spacing:.24em">UNE JOURNÉE DURE</div>
    <div style="font:300 250px Serif4;line-height:1;margin:6px 0 18px;letter-spacing:-.02em;white-space:nowrap">${grand}</div>
    <div style="font:600 46px InterW;letter-spacing:.2em;color:#ffb347">${orange}</div></div>`); return; }
  const f = u === '/img' ? path.resolve(img) : path.join(ROOT, u);
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200); r.end(d); });
}).listen(0, async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto(`http://127.0.0.1:${srv.address().port}/`); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
  await p.screenshot({ path: out, type: 'jpeg', quality: 95 }); await b.close(); srv.close();
});
