const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const srv = http.createServer((q, r) => { const u = decodeURIComponent(q.url.split('?')[0]); const f = path.join(__dirname, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); }); }).listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const seq = process.argv[2] || 'proto'; await p.goto(`http://127.0.0.1:${srv.address().port}/?seq=${seq}`); await p.waitForFunction(() => window.pret === true, null, { timeout: 180000 });
  const e = await p.evaluate(() => Array.from({ length: Math.round(window.DUREE * 10) + 1 }, (_, i) => window.etat(i / 10)));
  fs.writeFileSync(seq === 'proto' ? 'etat.json' : `etat_${seq}.json`, JSON.stringify(e)); await b.close(); srv.close(); });
