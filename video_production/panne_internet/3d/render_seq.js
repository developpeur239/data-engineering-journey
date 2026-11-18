// Rend une séquence three.js pilotée par une chronologie (window.init(timeline), window.renderAt(t)).
// node render_seq.js page.html timeline.json sortie.mp4 [largeur=1920] [fps=24] [--frames a-b]
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
(async () => {
  const [html, tlPath, out, w = "1920", fps = "24", only] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(tlPath, "utf8"));
  const W = +w, H = Math.round(W * 9 / 16), N = Math.round(tl.total * +fps);
  const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on("pageerror", (e) => { console.error("Erreur page :", e.message); process.exit(2); });
  await page.goto("file://" + path.resolve(html) + "?w=" + W);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  await page.evaluate((t) => window.init(t), tl);
  // --frames : liste d'images isolées (aperçu), sinon toute la séquence en vidéo
  if (only) {
    for (const s of only.split(",")) {
      const t = +s; await page.evaluate((x) => window.renderAt(x), t);
      await page.screenshot({ path: `${out}_${t.toFixed(2)}.jpg`, type: "jpeg", quality: 90 });
    }
    await browser.close(); return;
  }
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", fps, "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    await page.evaluate((t) => window.renderAt(t), i / +fps);
    ff.stdin.write(await page.screenshot({ type: "jpeg", quality: 93 }));
    if (i % 48 === 0) console.log(`image ${i}/${N} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  ff.stdin.end(); await new Promise((r) => ff.on("close", r)); await browser.close();
  console.log("Terminé :", out);
})();
