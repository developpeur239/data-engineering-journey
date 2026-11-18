// Audit des sites des cibles (relance de devis) avec un vrai navigateur mobile.
// Usage : node prospection/audit_sites.js prospection/cibles_audit.json
// Sortie : prospection/audit_brut.json + captures du 1er écran mobile dans
//          prospection/audit_captures/
// Pour chaque site : chargement, téléphone cliquable, bouton devis/RDV et
// à combien d'écrans il se trouve, formulaire, prise de RDV en ligne, chat,
// avis Google affichés, simulateur/aides, pub (Google Ads, Meta), CRM/emailing.

const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const input = process.argv[2];
const dir = path.dirname(input);
const shots = path.join(dir, 'audit_captures');
fs.mkdirSync(shots, { recursive: true });
const targets = JSON.parse(fs.readFileSync(input, 'utf8'));

const TOOLS = {
  google_ads: /googleadservices|gtag\/js\?id=AW-|['"]AW-\d{6,}|googleads\.g\.doubleclick/i,
  meta_pixel: /connect\.facebook\.net\/[^"']*fbevents|fbq\(['"]init/i,
  analytics: /googletagmanager\.com\/(gtm|gtag)|google-analytics\.com|['"]G-[A-Z0-9]{6,}/i,
  chat: /crisp\.chat|tawk\.to|intercom|livechatinc|zopim|zendesk|smartsupp|tidio|chatra|js\.usemessages|hubspot\.com\/conversations|wa\.me\/|api\.whatsapp|whatsapp\.com\/send|messenger/i,
  rdv_en_ligne: /calendly\.com|cal\.com\/|zcal\.co|simplybook|setmore|acuityscheduling|youcanbook|agenda\.|prise-de-rendez-vous|rendez-vous en ligne|réserver en ligne|prendre rendez-vous en ligne|planity|meetings\.hubspot/i,
  crm_emailing: /hs-scripts\.com|hsforms|hubspot|sendinblue|brevo|mailchimp|activecampaign|pipedrive|salesforce|zoho|sellsy|axonaut|klaviyo|plezi|webmecanik|mautic|lemlist|gohighlevel|leadconnector/i,
  widget_avis: /trustindex|elfsight|embedsocial|guest-suite|custplace|avis-verifies|trustpilot|reviews-widget|google-reviews|wpreviewslider|richplugins|grw-|widget.*avis/i,
};
const CMS = [
  ['WordPress', /wp-content|wp-includes/i], ['Wix', /wix\.com|wixstatic/i],
  ['Jimdo', /jimdo/i], ['Webflow', /webflow/i], ['Squarespace', /squarespace/i],
  ['Shopify', /shopify/i], ['Solocal/PagesJaunes', /solocal|pagesjaunes|site-solocal/i],
  ['Duda', /dudaone|multiscreensite/i], ['Joomla', /joomla/i], ['Drupal', /drupal/i],
];
const CTA = /devis|estimation|estimez|rendez-vous|\brdv\b|rappel|contactez|nous contacter|contact|demande|étude|offert|gratuit|éligib|projet|simul/i;
const SIMU = /simulat|simulez|estimez|calculez|maprimer|ma prime r|aides? (de l'état|financi)|cee\b|prime énergie|éligib/i;
const RATING_TXT = /(\d[,.]\d)\s*\/\s*5|avis google|google reviews|avis clients|\d+\s+avis/i;

async function analyse(page, url, out, prefix) {
  const reqs = [];
  page.on('request', r => reqs.push(r.url()));
  const t0 = Date.now();
  const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  out[prefix + 'chargement_s'] = ((Date.now() - t0) / 1000).toFixed(1);
  await page.waitForTimeout(5000); // laisse se charger chat, pixels, widgets
  out[prefix + 'statut_http'] = resp ? resp.status() : '';
  out[prefix + 'url_finale'] = page.url();
  const html = await page.content();
  const blob = html + '\n' + reqs.join('\n');
  return { html, blob };
}

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const t of targets) {
    const out = { nom: t.nom, site: t.site_web };
    console.log('→', t.nom, t.site_web);
    const ctx = await browser.newContext({ ...devices['iPhone 13'], locale: 'fr-FR' });
    const page = await ctx.newPage();
    try {
      const { html, blob } = await analyse(page, t.site_web, out, '');
      out.https = page.url().startsWith('https');
      for (const [k, re] of Object.entries(TOOLS)) out[k] = re.test(blob);
      out.cms = (CMS.find(([, re]) => re.test(blob)) || ['?'])[0];
      const text = await page.evaluate(() => document.body ? document.body.innerText : '');
      out.simulateur_aides = SIMU.test(text);
      out.avis_affiches = RATING_TXT.test(text) || out.widget_avis;
      out.prix_affiches = /à partir de\s*\d|\d[\d\s]*\s?€/i.test(text);
      const vh = page.viewportSize().height;
      // Liens et boutons visibles : téléphone cliquable, CTA devis/RDV.
      const els = await page.evaluate((ctaSrc) => {
        const cta = new RegExp(ctaSrc, 'i');
        const res = [];
        for (const el of document.querySelectorAll('a, button, input[type=submit]')) {
          const r = el.getBoundingClientRect();
          const st = getComputedStyle(el);
          if (r.width < 5 || r.height < 5 || st.visibility === 'hidden' || st.display === 'none') continue;
          const txt = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 60);
          const href = el.getAttribute('href') || '';
          res.push({ txt, href, y: r.top + window.scrollY, tel: href.startsWith('tel:'), cta: cta.test(txt) });
        }
        return res;
      }, CTA.source);
      const tels = els.filter(e => e.tel);
      out.tel_cliquable = tels.length > 0;
      out.tel_1er_ecran = tels.some(e => e.y < vh);
      const ctas = els.filter(e => e.cta && !e.tel).sort((a, b) => a.y - b.y);
      out.cta_principal = ctas.length ? ctas[0].txt : '';
      out.cta_ecrans = ctas.length ? +(ctas[0].y / vh).toFixed(1) : '';
      out.formulaire_accueil = await page.evaluate(() =>
        [...document.querySelectorAll('form')].filter(f =>
          f.querySelectorAll('input:not([type=hidden]):not([type=search]), textarea, select').length >= 3).length > 0);
      await page.screenshot({ path: path.join(shots, t.siren + '.png') });
      // Page devis/contact : formulaire et nombre de champs.
      const target = ctas.find(e => e.href && !e.href.startsWith('#') && !e.href.startsWith('tel:') && !e.href.startsWith('mailto:'))
        || els.find(e => /contact|devis/i.test(e.href) && !e.href.startsWith('mailto:'));
      if (target) {
        const p2 = await ctx.newPage();
        try {
          const url2 = new URL(target.href, page.url()).toString();
          const r2 = await analyse(p2, url2, out, 'page_devis_');
          out.page_devis = url2;
          out.page_devis_champs = await p2.evaluate(() => {
            const forms = [...document.querySelectorAll('form')];
            return Math.max(0, ...forms.map(f => f.querySelectorAll('input:not([type=hidden]):not([type=search]), textarea, select').length));
          });
          out.rdv_en_ligne = out.rdv_en_ligne || TOOLS.rdv_en_ligne.test(r2.blob);
          out.crm_emailing = out.crm_emailing || TOOLS.crm_emailing.test(r2.blob);
          out.google_ads = out.google_ads || TOOLS.google_ads.test(r2.blob);
          out.meta_pixel = out.meta_pixel || TOOLS.meta_pixel.test(r2.blob);
        } catch (e) { out.page_devis_erreur = String(e).slice(0, 120); }
        await p2.close();
      }
    } catch (e) {
      out.erreur = String(e).slice(0, 200);
    }
    results.push(out);
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(dir, 'audit_brut.json'), JSON.stringify(results, null, 1));
  console.log('ok', results.length);
})();
