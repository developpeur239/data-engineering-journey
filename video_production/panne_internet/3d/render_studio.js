// Rend une liste de scènes du studio 3D (studio/index.html) en vidéos, image par image.
// node render_studio.js jobs.json <dossier_assets> [largeur=1920] [fps=24]
// jobs.json : [{ "scene": {...}, "out": "seg.mp4", "frames": 240, "stills": [1.5, 4] (facultatif : images de contrôle) }]
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");
const path = require("path");

const TYPES = { ".html": "text/html", ".css": "text/css", ".wasm": "application/wasm", ".js": "text/javascript", ".json": "application/json", ".geojson": "application/json",
  ".jpg": "image/jpeg", ".png": "image/png", ".woff2": "font/woff2" };
function serve(studio, assets) {
  return new Promise((ok) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split("?")[0]);
      const file = url.startsWith("/assets/") ? path.join(assets, url.slice(8)) : path.join(studio, url === "/" ? "index.html" : url);
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" }); res.end(data);
      });
    });
    srv.listen(0, "127.0.0.1", () => ok(srv));
  });
}

(async () => {
  const [jobsPath, assets, w = "1920", fps = "24"] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jobsPath, "utf8"));
  const srv = await serve(path.join(__dirname, "studio"), path.resolve(assets));
  const port = srv.address().port;
  const W = +w, H = Math.round(W * 9 / 16);
  const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-proxy-server"] });
  for (const job of jobs) {
    const t0 = Date.now();
    const page = await browser.newPage({ viewport: { width: W, height: H } });
    let failed = null;
    page.on("pageerror", (e) => { failed = e.message; });
    page.on("console", (m) => { if (m.type() === "error") console.error(`  [scène ${job.scene.n}] console :`, m.text()); });
    await page.goto(`http://127.0.0.1:${port}/index.html?w=${W}`);
    await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
    try { await page.evaluate((s) => window.init(s), job.scene); } catch (e) { failed = e.message.split("\n").slice(0, 3).join(" | "); }
    if (failed) { console.error(`Erreur scène ${job.scene.n} :`, failed); process.exitCode = 2; await page.close(); continue; }
    if (job.stills) {
      for (const t of job.stills) { try { await page.evaluate((x) => window.renderAt(x), t); } catch (e) { console.error(`Erreur scène ${job.scene.n} à ${t} s :`, e.message.split("\n")[0]); process.exitCode = 2; break; }
        await page.screenshot({ path: `${job.out}_${t.toFixed(2)}.jpg`, type: "jpeg", quality: 88 }); }
      await page.close(); console.log(`scène ${job.scene.n} : images de contrôle`); continue;
    }
    const tmp = job.out + ".part.mp4";
    const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", fps, "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", fps, tmp], { stdio: ["pipe", "inherit", "inherit"] });
    for (let i = 0; i < job.frames; i++) {
      try { await page.evaluate((t) => window.renderAt(t), i / +fps); } catch (e) { failed = e.message.split("\n")[0]; }
      if (failed) break;
      ff.stdin.write(await page.screenshot({ type: "jpeg", quality: 93 }));
    }
    ff.stdin.end(); await new Promise((r) => ff.on("close", r));
    await page.close();
    if (failed) { console.error(`Erreur scène ${job.scene.n} :`, failed); process.exitCode = 2; fs.rmSync(tmp, { force: true }); continue; }
    fs.renameSync(tmp, job.out);
    console.log(`scène ${job.scene.n} rendue (${job.frames} images, ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  await browser.close(); srv.close();
})();
