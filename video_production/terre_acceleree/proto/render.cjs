// node render.cjs [debut] [fin] [pas] [dossier] [séquence]  → images JPEG de la scène (30 i/s)
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [deb = 0, fin = 20, pas = 1 / 30, out = 'frames', seq = 'proto'] = process.argv.slice(2).map((v, i) => i < 3 ? Number(v) : v);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => {
  const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
}).listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERREUR page:', e.message));
  await p.goto(`http://127.0.0.1:${srv.address().port}/?seq=${seq}`);
  await p.waitForFunction(() => window.pret === true, null, { timeout: 180000 });
  fs.mkdirSync(out, { recursive: true });
  const n = Math.round((fin - deb) / pas); const t0 = Date.now();
  for (let i = 0; i <= n; i++) {
    const t = deb + i * pas;
    await p.evaluate(t => window.frame(t), t);
    await p.screenshot({ path: `${out}/${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
    if (i % 30 === 0) console.log(`image ${i}/${n}  t=${t.toFixed(2)}  ${((Date.now() - t0) / 1000 / (i + 1)).toFixed(2)} s/image`);
  }
  await b.close(); srv.close();
});
