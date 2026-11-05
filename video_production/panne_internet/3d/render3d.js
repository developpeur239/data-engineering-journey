// Rend une scène three.js image par image en vidéo MP4.
// node render3d.js ville.html sortie.mp4 [durée_s=8] [largeur=1280] [fps=24]
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");
(async () => {
  const [html, out, dur = "8", w = "1280", fps = "24"] = process.argv.slice(2);
  const W = +w, H = Math.round(W * 9 / 16), N = Math.round(+dur * +fps);
  const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto("file://" + path.resolve(html) + "?w=" + W);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", fps, "-i", "-",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
  for (let i = 0; i < N; i++) {
    await page.evaluate(([t, d]) => window.renderAt(t, d), [i / +fps, +dur]);
    ff.stdin.write(await page.screenshot({ type: "jpeg", quality: 92 }));
    if (i % 24 === 0) process.stdout.write(`image ${i}/${N}\n`);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r)); await browser.close();
  console.log("Terminé :", out);
})();
