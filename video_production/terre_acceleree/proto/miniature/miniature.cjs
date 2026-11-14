// node miniature/miniature.cjs scene:seq t "GRAND" "ligne orange" sortie.jpg
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [seq, t, grand, orange, out] = process.argv.slice(2);
const ROOT = path.join(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]); const f = path.join(ROOT, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
}).listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('ERREUR page:', e.message));
  const [sc, sq] = seq.split(':');
  await p.goto(`http://127.0.0.1:${srv.address().port}/?scene=${sc}&seq=${sq}`);
  await p.waitForFunction(() => window.pret === true, null, { timeout: 180000 });
  await p.evaluate(t => window.frame(t), Number(t));
  await p.evaluate(([grand, orange]) => {
    for (const id of ['hud', 'sous', 'voileHaut']) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
    const v = document.createElement('div');
    v.style.cssText = 'position:fixed;left:0;top:0;width:1250px;height:640px;pointer-events:none;' +
      'background:radial-gradient(ellipse at 0% 0%, rgba(4,18,42,.72) 0%, rgba(4,18,42,.45) 45%, rgba(4,18,42,0) 72%)';
    document.body.appendChild(v);
    const d = document.createElement('div');
    d.style.cssText = 'position:fixed;left:70px;top:62px;color:#fff;text-shadow:0 3px 18px rgba(0,0,0,.55)';
    d.innerHTML = `<div style="font:600 46px InterW;letter-spacing:.24em">UNE JOURNÉE DURE</div>
      <div style="font:300 250px Serif4;line-height:1;margin:6px 0 18px;letter-spacing:-.02em;white-space:nowrap">${grand}</div>
      <div style="font:600 46px InterW;letter-spacing:.2em;color:#ffb347">${orange}</div>`;
    document.body.appendChild(d);
  }, [grand, orange]);
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: out, type: 'jpeg', quality: 95 });
  await b.close(); srv.close();
});
