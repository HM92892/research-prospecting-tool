"""
Research & Prospecting Tool v2 - Flask Web App
"""

from flask import Flask, request, jsonify, render_template_string
from scraper import scrape_website
from analyzer import run_full_pipeline
import time
import os

app = Flask(__name__)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research & Prospecting Tool</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
        colors: {
          n: {
            title:  '#191919',
            body:   '#37352F',
            sec:    '#787774',
            muted:  '#9B9A97',
            border: '#E9E9E7',
            block:  '#F7F6F3',
            blue:   '#2383E2',
          }
        }
      }
    }
  }
</script>
<style>
  /* ── Animations ── */
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes ldots {
    0%   { content: '.';   }
    33%  { content: '..';  }
    66%  { content: '...'; }
    100% { content: '';    }
  }
  .dot-anim::after { content: ''; animation: ldots 1.3s steps(3,end) infinite; }
  .spin-icon { animation: spin 0.8s linear infinite; }

  /* ── Progress bar ── */
  #progressBar {
    position: fixed; top: 0; left: 0; height: 2px;
    width: 0%; background: #2383E2; z-index: 9999;
    display: none; transition: width 0.4s ease;
  }

  /* ── Tabs ── */
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }
  .tab-btn { transition: color 0.15s, border-color 0.15s; }
  .tab-btn.active { color: #2383E2; border-bottom-color: #2383E2; font-weight: 600; }

  /* ── Toggles ── */
  .toggle-content { display: none; }
  .toggle-block.open .toggle-content { display: block; }
  .toggle-arrow { display: inline-block; transition: transform 0.15s; font-size: 10px; color: #9B9A97; }
  .toggle-block.open .toggle-arrow { transform: rotate(90deg); }

  /* ── Code copy (hover reveal) ── */
  .code-block:hover .code-copy { opacity: 1; }
  .code-copy.copied { background: #DBEDDB !important; color: #1C4428 !important; border-color: #DBEDDB !important; opacity: 1 !important; }
  .copy-email-btn.copied { background: #DBEDDB !important; color: #1C4428 !important; border-color: #DBEDDB !important; }
  .copy-email-btn { transition: all 0.15s; }
</style>
</head>
<body class="bg-white font-sans text-n-body antialiased">

<div id="progressBar"></div>

<div class="max-w-4xl mx-auto px-6">

  <!-- ── Hero ── -->
  <section class="pt-16 pb-12 border-b border-n-border">
    <p class="text-[10px] font-bold uppercase tracking-widest text-n-muted mb-3">AI-Powered SDR Tool</p>
    <h1 class="text-[32px] font-bold text-n-title tracking-tight leading-tight mb-2.5">Research &amp; Prospecting Tool</h1>
    <p class="text-base text-n-sec max-w-xl mb-10">Paste a URL. Get the brief, the offers, and the emails.</p>

    <div class="grid gap-0 items-center" style="grid-template-columns: 1fr 28px 1fr 28px 1fr;">
      <div class="bg-n-block rounded-md p-3.5">
        <div class="text-lg mb-1.5">🔍</div>
        <div class="text-[10px] font-bold uppercase tracking-wider text-n-blue mb-0.5">Step 1</div>
        <div class="text-[13px] font-semibold text-n-title mb-0.5">Research</div>
        <div class="text-[11px] text-n-muted leading-snug">Scrape website, extract customers &amp; case studies</div>
      </div>
      <div class="text-center text-n-muted text-base">›</div>
      <div class="bg-n-block rounded-md p-3.5">
        <div class="text-lg mb-1.5">🎯</div>
        <div class="text-[10px] font-bold uppercase tracking-wider text-n-blue mb-0.5">Step 2</div>
        <div class="text-[13px] font-semibold text-n-title mb-0.5">Build ICP</div>
        <div class="text-[11px] text-n-muted leading-snug">Define buyer profile, generate search queries</div>
      </div>
      <div class="text-center text-n-muted text-base">›</div>
      <div class="bg-n-block rounded-md p-3.5">
        <div class="text-lg mb-1.5">✉️</div>
        <div class="text-[10px] font-bold uppercase tracking-wider text-n-blue mb-0.5">Step 3</div>
        <div class="text-[13px] font-semibold text-n-title mb-0.5">Create Outreach</div>
        <div class="text-[11px] text-n-muted leading-snug">3 campaign angles with ready-to-send emails</div>
      </div>
    </div>
  </section>

  <!-- ── Input form ── -->
  <section class="py-10 space-y-5">

    <div class="space-y-1.5">
      <label class="block text-sm font-semibold text-n-body" for="urlInput">
        Target company URL <span class="text-n-blue">*</span>
      </label>
      <input id="urlInput" type="url" autocomplete="off"
        placeholder="https://www.company.com"
        class="w-full px-3 py-2 border border-n-border rounded-md text-sm text-n-body placeholder-[#C4C4C0] focus:outline-none focus:border-n-blue focus:ring-2 focus:ring-[#2383E2]/10 transition-colors" />
      <p class="text-xs text-n-muted">We'll scrape their site to extract customers, case studies, and GTM signals automatically.</p>
      <div class="flex items-center gap-2 mt-2 flex-wrap">
        <span class="text-[10px] font-bold uppercase tracking-wide text-n-muted">Try:</span>
        <button onclick="setUrl('https://www.keyplay.io')" class="px-3 py-1 text-xs bg-n-block border border-n-border rounded text-n-sec hover:border-n-blue hover:text-n-body transition-colors">keyplay.io</button>
        <button onclick="setUrl('https://www.ramp.com')" class="px-3 py-1 text-xs bg-n-block border border-n-border rounded text-n-sec hover:border-n-blue hover:text-n-body transition-colors">ramp.com</button>
        <button onclick="setUrl('https://www.gong.io')" class="px-3 py-1 text-xs bg-n-block border border-n-border rounded text-n-sec hover:border-n-blue hover:text-n-body transition-colors">gong.io</button>
      </div>
    </div>

    <div class="space-y-1.5">
      <label class="block text-sm font-semibold text-n-body" for="myCompanyInput">
        Your company URL <span class="text-n-blue">*</span>
      </label>
      <input id="myCompanyInput" type="url" autocomplete="off"
        placeholder="https://www.yourcompany.com"
        class="w-full px-3 py-2 border border-n-border rounded-md text-sm text-n-body placeholder-[#C4C4C0] focus:outline-none focus:border-n-blue focus:ring-2 focus:ring-[#2383E2]/10 transition-colors" />
      <p class="text-xs text-n-muted">We'll scrape your site to pull your real customers, case studies, and value props for the campaigns.</p>
    </div>

    <div class="space-y-1.5">
      <label class="block text-sm font-semibold text-n-body" for="productInput">
        What product are you selling? <span class="text-n-blue">*</span>
      </label>
      <input id="productInput" type="text"
        placeholder="e.g., AI-powered lead scoring platform"
        class="w-full px-3 py-2 border border-n-border rounded-md text-sm text-n-body placeholder-[#C4C4C0] focus:outline-none focus:border-n-blue focus:ring-2 focus:ring-[#2383E2]/10 transition-colors" />
      <p class="text-xs text-n-muted">Be specific. If your company sells multiple products, name the one you're responsible for.</p>
    </div>

    <div class="space-y-1.5">
      <label class="block text-sm font-semibold text-n-body" for="proofInput">
        Your proof points
        <span class="ml-1.5 text-[10px] font-bold uppercase tracking-wide text-n-muted bg-[#E3E2E0] rounded px-1.5 py-0.5 align-middle">optional</span>
      </label>
      <textarea id="proofInput" rows="3"
        placeholder="e.g., Helped Ramp's SDR team book 3x more meetings in 60 days. Notion cut list building from 4 hours to 20 minutes per week."
        class="w-full px-3 py-2 border border-n-border rounded-md text-sm text-n-body placeholder-[#C4C4C0] focus:outline-none focus:border-n-blue focus:ring-2 focus:ring-[#2383E2]/10 resize-y transition-colors min-h-[76px]"></textarea>
      <p class="text-xs text-n-muted">2–3 specific customer outcomes with names and numbers. Makes emails dramatically better.</p>
    </div>

    <div class="space-y-1.5">
      <label class="block text-sm font-semibold text-n-body" for="linkedinInput">
        Sample buyer LinkedIn profiles
        <span class="ml-1.5 text-[10px] font-bold uppercase tracking-wide text-n-muted bg-[#E3E2E0] rounded px-1.5 py-0.5 align-middle">optional</span>
      </label>
      <input id="linkedinInput" type="text"
        placeholder="Paste 1–3 LinkedIn profile URLs, comma-separated"
        class="w-full px-3 py-2 border border-n-border rounded-md text-sm text-n-body placeholder-[#C4C4C0] focus:outline-none focus:border-n-blue focus:ring-2 focus:ring-[#2383E2]/10 transition-colors" />
      <p class="text-xs text-n-muted">Providing example buyers improves ICP accuracy and outreach targeting.</p>
      <p class="text-xs text-n-blue">ℹ Analyzing real buyer profiles helps the tool understand your actual ICP instead of guessing.</p>
    </div>

    <button id="generateBtn" onclick="generate()"
      class="w-full bg-n-blue text-white text-sm font-semibold py-2.5 rounded hover:bg-[#1a6fc4] active:bg-[#1560b0] transition-colors">
      Generate Prospecting Kit
    </button>

    <!-- Loading step text -->
    <div id="loadingBox" class="hidden pt-1 text-center">
      <p class="text-sm text-n-sec italic">
        <span id="loadingStepText">Researching company</span><span class="dot-anim"></span>
      </p>
    </div>

  </section>

  <!-- ── Error ── -->
  <div id="errorBox" class="hidden mb-8 flex gap-3 bg-[#FFF0F0] border-l-4 border-[#E03E3E] rounded-r px-4 py-3 text-sm text-[#6E2B20]"></div>

  <!-- ── Results ── -->
  <div id="results" class="hidden">

    <div class="mb-6 pb-5 border-b border-n-border">
      <h2 class="text-[22px] font-bold text-n-title tracking-tight">Brief for <span id="resultsCompany" class="text-n-blue"></span></h2>
    </div>

    <!-- Company summary callout -->
    <div id="summaryCallout" class="flex rounded-md bg-n-block overflow-hidden mb-8"></div>

    <!-- Tab bar -->
    <div class="flex border-b border-n-border mb-7 -mx-0">
      <button class="tab-btn px-4 py-2 text-sm text-n-muted border-b-2 border-transparent hover:text-n-body -mb-px" onclick="switchTab('campaigns', this)">Campaigns</button>
      <button class="tab-btn px-4 py-2 text-sm text-n-muted border-b-2 border-transparent hover:text-n-body -mb-px" onclick="switchTab('icp', this)">ICP &amp; Targeting</button>
      <button class="tab-btn px-4 py-2 text-sm text-n-muted border-b-2 border-transparent hover:text-n-body -mb-px" onclick="switchTab('intel', this)">Company Intel</button>
      <button class="tab-btn px-4 py-2 text-sm text-n-muted border-b-2 border-transparent hover:text-n-body -mb-px" onclick="switchTab('analysis', this)">Full Analysis</button>
    </div>

    <div class="tab-pane active" id="tab-campaigns">
      <div id="campaignsGrid"></div>
    </div>

    <div class="tab-pane" id="tab-icp">
      <div id="icpContent"></div>
    </div>

    <div class="tab-pane" id="tab-intel">
      <div id="intelContent"></div>
    </div>

    <div class="tab-pane" id="tab-analysis">
      <div id="analysisContent"></div>
    </div>

    <!-- Results footer -->
    <div id="resultsFooter" class="hidden flex items-center justify-between flex-wrap gap-3 pt-5 mt-8 border-t border-n-border pb-12">
      <span id="metaText" class="text-xs text-n-muted"></span>
      <button onclick="downloadMarkdown()"
        class="inline-flex items-center gap-1.5 text-xs font-medium text-n-body border border-n-border rounded px-3 py-1.5 hover:bg-n-block transition-colors">
        ↓ Download as Markdown
      </button>
    </div>

  </div>

  <div class="text-center text-[11px] text-n-muted py-6 mt-4 border-t border-n-border">
    Powered by Claude Sonnet 4 · approx $0.04 per company · Built by <a href="https://www.linkedin.com/in/hamza-munif/" target="_blank" rel="noopener" class="text-n-sec hover:text-n-blue transition-colors">Hamza Munif</a> · <a href="https://github.com/HM92892/research-prospecting-tool" target="_blank" rel="noopener" class="text-n-sec hover:text-n-blue transition-colors">GitHub</a>
  </div>

</div><!-- container -->

<script>
let currentData = null;

function setUrl(url) {
  document.getElementById('urlInput').value = url;
  generate();
}

/* ── Utilities ── */
function esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function wc(t) {
  if (!t) return 0;
  return t.trim().split(/\s+/).filter(w => w.length).length;
}
function wcBadge(n, lo, hi) {
  const ok = n >= lo && n <= hi;
  const cls = ok
    ? 'bg-[#DBEDDB] text-[#1C4428]'
    : 'bg-[#FDECC8] text-[#5C3B00]';
  return `<span class="text-[10px] font-bold px-1.5 py-0.5 rounded ${cls}">${n} words</span>`;
}
function tag(label, colorKey) {
  const map = {
    blue:   'bg-[#D3E5EF] text-[#183B56]',
    green:  'bg-[#DBEDDB] text-[#1C4428]',
    yellow: 'bg-[#FDECC8] text-[#5C3B00]',
    purple: 'bg-[#E8DEEE] text-[#412D5A]',
    gray:   'bg-[#E3E2E0] text-[#5A5A58]',
  };
  const cls = map[colorKey] || map.gray;
  return `<span class="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-sm ${cls}">${esc(label)}</span>`;
}
function simpleMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^### (.+)$/gm,'<h3 class="text-sm font-semibold text-n-title mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm,'<h2 class="text-base font-semibold text-n-title mt-4 mb-1.5">$1</h2>')
    .replace(/^# (.+)$/gm,'<h1 class="text-lg font-bold text-n-title mt-5 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong class="font-semibold text-n-title">$1</strong>')
    .replace(/^[-*] (.+)$/gm,'<li class="ml-4 mb-1 list-disc">$1</li>')
    .replace(/\n/g,'<br>');
}
function parseAnalysisSections(text) {
  const out = {};
  const parts = text.split(/\n(?=## )/);
  for (const p of parts) {
    const m = p.match(/^## ([^\n]+)\n([\s\S]*)/);
    if (m) out[m[1].trim()] = m[2].trim();
  }
  return out;
}
function getGTMInfo(text) {
  // Use the first line of the GTM MOTION field directly (Claude is now instructed
  // to put exactly one of the three labels on line 1, so this is authoritative).
  const firstLine = (text||'').split('\n')[0].trim();
  const t = firstLine.toLowerCase();
  if (t.includes('product-led') || t.includes('plg'))
    return { label: firstLine || 'Product-Led (PLG)', color:'green' };
  if (t.includes('sales-led') || t.includes('sales led'))
    return { label: firstLine || 'Sales-Led', color:'blue' };
  if (t.includes('hybrid'))
    return { label: firstLine || 'Hybrid', color:'purple' };
  // Fallback: still try the full text (for cached/legacy analyses)
  const full = (text||'').toLowerCase();
  if (full.includes('product-led') || full.includes('plg') || full.includes('self-serve'))
    return { label:'Product-Led (PLG)', color:'green' };
  if (full.includes('sales-led') || full.includes('sales led'))
    return { label:'Sales-Led', color:'blue' };
  return { label:'Hybrid', color:'purple' };
}
function countItems(text) {
  if (!text || text.includes('Not found')) return 0;
  const lines = text.split('\n').filter(l => /^[-*•]|\d+\./.test(l.trim()));
  return Math.max(lines.length, 1);
}

/* ── Seller info ── */
function getSellerInfo() {
  const product  = document.getElementById('productInput').value.trim();
  const proof    = document.getElementById('proofInput').value.trim();
  const linkedin = document.getElementById('linkedinInput').value.trim();
  if (!product && !proof) return null;
  return {
    company_name:  'My Company',
    what_you_sell: product,
    customer_wins: proof,
    buyer_persona: linkedin ? 'Ideal buyer LinkedIn examples: ' + linkedin : '',
  };
}

/* ── Progress bar ── */
function startProgress() {
  const bar = document.getElementById('progressBar');
  bar.style.display = 'block';
  bar.style.transition = 'none';
  bar.style.width = '0%';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    bar.style.transition = 'width 55s cubic-bezier(0.1, 0.9, 0.2, 1)';
    bar.style.width = '82%';
  }));
}
function finishProgress() {
  const bar = document.getElementById('progressBar');
  bar.style.transition = 'width 0.25s ease';
  bar.style.width = '100%';
  setTimeout(() => { bar.style.display = 'none'; bar.style.width = '0%'; }, 350);
}

/* ── Loading steps ── */
const STEPS = [
  'Researching company',
  'Extracting company intelligence',
  'Building buyer profile',
  'Generating outreach campaigns',
  'Assembling your kit',
];
let stepIdx = 0, stepTimer = null;
function startSteps() {
  stepIdx = 0;
  document.getElementById('loadingStepText').textContent = STEPS[0];
  document.getElementById('loadingBox').classList.remove('hidden');
  stepTimer = setInterval(() => {
    stepIdx = Math.min(stepIdx + 1, STEPS.length - 1);
    document.getElementById('loadingStepText').textContent = STEPS[stepIdx];
  }, 9000);
}
function stopSteps() {
  if (stepTimer) { clearInterval(stepTimer); stepTimer = null; }
  document.getElementById('loadingBox').classList.add('hidden');
}

/* ── Generate ── */
async function generate() {
  const url           = document.getElementById('urlInput').value.trim();
  const myCompanyUrl  = document.getElementById('myCompanyInput').value.trim();
  const product       = document.getElementById('productInput').value.trim();
  if (!url)          { document.getElementById('urlInput').focus();       return; }
  if (!myCompanyUrl) { document.getElementById('myCompanyInput').focus(); return; }
  if (!product)      { document.getElementById('productInput').focus();   return; }

  const btn      = document.getElementById('generateBtn');
  const errorBox = document.getElementById('errorBox');
  const results  = document.getElementById('results');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  errorBox.classList.add('hidden');
  results.classList.add('hidden');
  document.getElementById('resultsFooter').classList.add('hidden');
  startProgress();
  startSteps();

  try {
    const payload = { url, my_company_url: myCompanyUrl };
    const seller = getSellerInfo();
    if (seller) payload.seller_info = seller;

    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    finishProgress();
    stopSteps();

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Something went wrong');
    }
    const data = await resp.json();
    currentData = data;
    renderResults(data);
  } catch (e) {
    finishProgress();
    stopSteps();
    errorBox.textContent = e.message;
    errorBox.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Prospecting Kit';
  }
}

/* ── Render all ── */
function renderResults(data) {
  document.getElementById('results').classList.remove('hidden');
  renderSummary(data);
  renderCampaigns(data.campaigns || []);
  renderICP(data.icp_profile || {}, data);
  renderIntel(data.brief || '');
  renderAnalysis(data.company_analysis || '');
  const cached = data.from_cache ? ' · cached' : '';
  const selCtx = data.has_seller_context ? ' · seller context applied' : '';
  const sellerMeta = data.seller_pages_scraped
    ? ` · ${data.seller_pages_scraped} pages from your site (${(data.seller_chars_scraped||0).toLocaleString()} chars)`
    : '';
  document.getElementById('metaText').textContent =
    `${data.pages_scraped} pages scraped · ${(data.chars_scraped||0).toLocaleString()} chars · ${data.duration_seconds}s${cached}${selCtx}${sellerMeta}`;
  document.getElementById('resultsCompany').textContent = data.domain || '';
  document.getElementById('resultsFooter').classList.remove('hidden');
  switchTab('campaigns', document.querySelector('.tab-btn'));
}

/* ── Summary ── */
function renderSummary(data) {
  const s = parseAnalysisSections(data.company_analysis || '');
  const name      = s['COMPANY NAME'] || data.domain || 'Company';
  const oneliner  = s['ONE-LINER'] || '';
  const gtm       = getGTMInfo(s['GTM MOTION'] || '');
  const serve     = s['WHO THEY SERVE'] || '';
  const custCt    = countItems(s['NAMED CUSTOMERS'] || '');
  const caseCt    = countItems(s['CASE STUDIES'] || '');
  const proofCt   = countItems(s['PROOF POINTS'] || '');

  document.getElementById('summaryCallout').innerHTML = `
    <div class="w-1 bg-n-blue flex-shrink-0"></div>
    <div class="p-5 flex-1">
      <h2 class="text-2xl font-bold text-n-title mb-1">${esc(name)}</h2>
      ${oneliner ? `<p class="text-sm text-n-sec mb-3">${esc(oneliner)}</p>` : ''}
      <div class="flex items-center gap-1.5 flex-wrap">
        ${tag(gtm.label, gtm.color)}
        ${custCt  ? `<span class="text-n-muted text-xs">·</span>${tag(custCt+' named customers','gray')}`  : ''}
        ${caseCt  ? `<span class="text-n-muted text-xs">·</span>${tag(caseCt+' case studies','gray')}`    : ''}
        ${proofCt ? `<span class="text-n-muted text-xs">·</span>${tag(proofCt+' proof points','gray')}`   : ''}
      </div>
      ${serve ? `<p class="text-xs text-n-sec mt-2"><strong class="text-n-body font-semibold">Serves:</strong> ${esc(serve.split('\n')[0])}</p>` : ''}
    </div>`;
}

/* ── Campaigns ── */
function renderCampaigns(campaigns) {
  const grid = document.getElementById('campaignsGrid');
  if (!campaigns.length) {
    grid.innerHTML = '<p class="text-n-muted py-8">No campaigns generated.</p>';
    return;
  }

  const badgeColorMap = { blue:'blue', green:'green', orange:'yellow' };

  grid.innerHTML = campaigns.map((c, i) => {
    const tc = badgeColorMap[c.badge_color] || 'blue';
    const n1 = wc(c.email_body), n2 = wc(c.followup_2_body), n3 = wc(c.followup_3_body);
    const border = i > 0 ? 'mt-8 pt-8 border-t border-n-border' : '';

    const objHTML = c.implicit_objection ? `
      <div class="bg-[#FDECC8] rounded px-3 py-3 flex gap-2.5 mb-4">
        <span class="flex-shrink-0 mt-0.5">⚠</span>
        <div>
          <div class="text-[10px] font-bold uppercase tracking-wide text-[#5C3B00] mb-1">Implicit Objection &amp; How This Email Handles It</div>
          <div class="text-xs text-[#4a2f00] leading-relaxed">${esc(c.implicit_objection)}</div>
        </div>
      </div>` : '';

    const emailToggle = (label, subject, body, ps, idx, lo, hi) => {
      const n = wc(body);
      return `
        <div class="toggle-block">
          <div class="toggle-header flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-n-block select-none" onclick="toggleBlock(this)">
            <span class="toggle-arrow">▶</span>
            <span class="text-sm font-semibold text-n-body">${label} —</span>
            <span class="text-sm text-n-title flex-1 min-w-0 truncate">${esc(subject)}</span>
            ${wcBadge(n, lo, hi)}
          </div>
          <div class="toggle-content pl-5 pt-2 pb-1 relative">
            <button class="copy-email-btn absolute top-1 right-0 text-[10px] font-semibold text-n-muted bg-white border border-n-border rounded px-2 py-1 hover:text-n-body hover:border-[#aaa]" onclick="copyEmail(event,${idx})">Copy</button>
            <div class="text-sm text-n-body leading-[1.75] whitespace-pre-wrap mb-2">${esc(body||'')}</div>
            ${ps ? `<div class="text-xs text-n-sec italic pt-2 border-t border-n-border">PS: ${esc(ps)}</div>` : ''}
          </div>
        </div>`;
    };

    const followupsHTML = (c.followup_2_body || c.followup_3_body) ? `
      <div class="toggle-block mt-1">
        <div class="toggle-header flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-n-block select-none" onclick="toggleBlock(this)">
          <span class="toggle-arrow">▶</span>
          <span class="text-sm text-n-sec">Show follow-up sequence (Email 2 &amp; 3)</span>
        </div>
        <div class="toggle-content pl-4 space-y-3 pt-2">
          ${c.followup_2_body ? `
            <div>
              <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">Email 2 — Flip Value Prop, Lower Ask</div>
              ${emailToggle('', c.followup_2_subject||'', c.followup_2_body, '', i, 50, 90)}
            </div>` : ''}
          ${c.followup_3_body ? `
            <div>
              <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">Email 3 — Free Value Taste</div>
              ${emailToggle('', c.followup_3_subject||'', c.followup_3_body, '', i, 40, 80)}
            </div>` : ''}
        </div>
      </div>` : '';

    return `
      <div class="campaign-block ${border}">
        <div class="flex items-center gap-2.5 mb-5 flex-wrap">
          ${tag(c.type||'', tc)}
          <span class="text-lg font-semibold text-n-title">${esc(c.offer_name||'')}</span>
        </div>

        <div class="mb-4">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">🎁 What You're Giving Away</div>
          <div class="text-sm text-n-body leading-relaxed">${esc(c.what_youre_giving||'')}</div>
        </div>

        <div class="mb-4">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">✅ Why It Converts</div>
          <div class="text-sm text-n-body leading-relaxed">${esc(c.why_it_converts||'')}</div>
        </div>

        ${objHTML}

        <div class="mb-4">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">👤 Target ICP</div>
          <div class="text-sm text-n-body leading-relaxed">${esc(c.target_icp||'')}</div>
        </div>

        <div class="mb-4">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">Apollo Search Query</div>
          <div class="code-block bg-n-block rounded px-3 py-2.5 font-mono text-xs text-n-body leading-relaxed relative">
            <button class="code-copy absolute top-2 right-2 text-[10px] font-semibold text-n-muted bg-white border border-n-border rounded px-2 py-0.5 opacity-0 hover:text-n-body transition-all" onclick="copyText(event, ${JSON.stringify(c.apollo_search||'')})">Copy</button>
            ${esc(c.apollo_search||'')}
          </div>
        </div>

        <div class="mb-4">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">LinkedIn Sales Navigator Search</div>
          <div class="code-block bg-n-block rounded px-3 py-2.5 font-mono text-xs text-n-body leading-relaxed relative">
            <button class="code-copy absolute top-2 right-2 text-[10px] font-semibold text-n-muted bg-white border border-n-border rounded px-2 py-0.5 opacity-0 hover:text-n-body transition-all" onclick="copyText(event, ${JSON.stringify(c.linkedin_search||'')})">Copy</button>
            ${esc(c.linkedin_search||'')}
          </div>
        </div>

        <div class="mb-2">
          <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-2">Emails</div>
          ${emailToggle('Email 1', c.subject_line||'', c.email_body||'', c.ps_line||'', i, 70, 90)}
          ${followupsHTML}
        </div>
      </div>`;
  }).join('');
}

/* ── ICP & Targeting ── */
function renderICP(icp, data) {
  const el = document.getElementById('icpContent');
  if (!icp || Object.keys(icp).length === 0) {
    el.innerHTML = '<p class="text-n-muted py-8">ICP data not available.</p>';
    return;
  }

  const titles     = Array.isArray(icp.target_titles)     ? icp.target_titles     : [];
  const industries = Array.isArray(icp.target_industries) ? icp.target_industries : [];
  const signals    = Array.isArray(icp.key_signals)       ? icp.key_signals       : [];
  const linkedinN    = icp.linkedin_profiles_analyzed || 0;

  const linkedinNote = linkedinN > 0 ? `
    <div class="flex items-center gap-2 bg-[#D3E5EF] text-[#183B56] text-xs font-semibold px-3 py-2 rounded mb-5">
      🔗 ICP refined using ${linkedinN} sample buyer profile${linkedinN > 1 ? 's' : ''}
    </div>` : '';

  const titlesHTML = titles.length
    ? titles.map(t => tag(t, 'blue')).join(' ')
    : tag('Not available', 'gray');

  const industriesHTML = industries.length
    ? industries.map(ind => tag(ind, 'purple')).join(' ')
    : tag('Not available', 'gray');

  const signalsHTML = signals.length
    ? `<ul class="space-y-2 mt-1">${signals.map(s =>
        `<li class="flex items-start gap-2 text-sm text-n-body py-1.5 border-b border-n-border last:border-0">
          <span class="w-1.5 h-1.5 rounded-full bg-n-blue flex-shrink-0 mt-1.5"></span>
          <span>${esc(s)}</span>
        </li>`).join('')}</ul>`
    : '<p class="text-sm text-n-muted">Not available</p>';

  el.innerHTML = `
    ${linkedinNote}

    <div class="grid grid-cols-2 gap-6 mb-6">
      <div>
        <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-2">Target Job Titles</div>
        <div class="flex flex-wrap gap-1.5">${titlesHTML}</div>
      </div>
      <div>
        <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-2">Target Industries</div>
        <div class="flex flex-wrap gap-1.5">${industriesHTML}</div>
      </div>
      <div>
        <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-2">Company Size</div>
        <div class="text-sm text-n-body">${esc(icp.company_size || 'Not specified')}</div>
      </div>
      <div>
        <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1">Key Buying Signals</div>
        ${signalsHTML}
      </div>
    </div>

    <hr class="border-n-border my-6">

    <div class="mb-5">
      <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">Apollo Search Query</div>
      <div class="code-block bg-n-block rounded px-3 py-2.5 font-mono text-xs text-n-body relative">
        <button class="code-copy absolute top-2 right-2 text-[10px] font-semibold text-n-muted bg-white border border-n-border rounded px-2 py-0.5 opacity-0 hover:text-n-body transition-all" onclick="copyText(event, ${JSON.stringify(icp.apollo_search||'')})">Copy</button>
        ${esc(icp.apollo_search || 'Not available')}
      </div>
    </div>

    <div class="mb-5">
      <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-1.5">LinkedIn Sales Navigator Search</div>
      <div class="code-block bg-n-block rounded px-3 py-2.5 font-mono text-xs text-n-body relative">
        <button class="code-copy absolute top-2 right-2 text-[10px] font-semibold text-n-muted bg-white border border-n-border rounded px-2 py-0.5 opacity-0 hover:text-n-body transition-all" onclick="copyText(event, ${JSON.stringify(icp.linkedin_search||'')})">Copy</button>
        ${esc(icp.linkedin_search || 'Not available')}
      </div>
    </div>

    ${icp.icp_reasoning ? `
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-6">
      <div class="text-[10px] font-bold uppercase tracking-wide text-n-muted mb-2">ICP Reasoning</div>
      <div class="text-sm text-n-body leading-relaxed">${esc(icp.icp_reasoning)}</div>
    </div>` : ''}
  `;
}

/* ── Company Intel ── */
function renderIntel(text) {
  const el = document.getElementById('intelContent');
  const parts = text.split(/\n(?=## )/);
  let html = '';
  for (const p of parts) {
    const m = p.match(/^## ([^\n]+)\n?([\s\S]*)/);
    if (m) {
      html += `<div class="mb-7">
        <h3 class="text-sm font-semibold text-n-title mb-3 pb-2 border-b border-n-border">${esc(m[1].trim())}</h3>
        <div class="text-sm text-n-body leading-relaxed">${simpleMarkdown(m[2].trim())}</div>
      </div>`;
    } else if (p.trim() && !p.match(/^# /)) {
      html += `<div class="text-sm text-n-body leading-relaxed mb-4">${simpleMarkdown(p.trim())}</div>`;
    }
  }
  el.innerHTML = html || `<div class="text-sm text-n-body leading-relaxed">${simpleMarkdown(text)}</div>`;
}

/* ── Full Analysis ── */
function renderAnalysis(text) {
  const el = document.getElementById('analysisContent');
  const s = parseAnalysisSections(text);
  const ORDER = [
    'COMPANY NAME','ONE-LINER','WHO THEY SERVE','NAMED CUSTOMERS',
    'CASE STUDIES','KEY VALUE PROPOSITIONS','PROOF POINTS',
    'PRICING MODEL','RECENT NEWS OR BLOG HIGHLIGHTS','GTM MOTION','LIKELY BUYERS'
  ];
  const rendered = new Set();
  let html = '';
  for (const key of ORDER) {
    if (!s[key]) continue;
    rendered.add(key);
    html += `<div class="pb-5 mb-5 border-b border-n-border last:border-0">
      <div class="text-[10px] font-bold uppercase tracking-wide text-n-blue mb-2">${esc(key)}</div>
      <div class="text-sm text-n-body leading-relaxed whitespace-pre-wrap">${esc(s[key])}</div>
    </div>`;
  }
  for (const key of Object.keys(s)) {
    if (rendered.has(key)) continue;
    html += `<div class="pb-5 mb-5 border-b border-n-border last:border-0">
      <div class="text-[10px] font-bold uppercase tracking-wide text-n-blue mb-2">${esc(key)}</div>
      <div class="text-sm text-n-body leading-relaxed whitespace-pre-wrap">${esc(s[key])}</div>
    </div>`;
  }
  el.innerHTML = html || `<div class="text-sm text-n-body whitespace-pre-wrap">${esc(text)}</div>`;
}

/* ── UI interactions ── */
function switchTab(tab, btn) {
  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const pane = document.getElementById('tab-' + tab);
  if (pane) pane.classList.add('active');
}

function toggleBlock(header) {
  header.closest('.toggle-block').classList.toggle('open');
}

function copyEmail(e, idx) {
  e.stopPropagation();
  if (!currentData || !currentData.campaigns[idx]) return;
  const c = currentData.campaigns[idx];
  let text = 'Subject: ' + (c.subject_line||'') + '\n\n' + (c.email_body||'');
  if (c.ps_line) text += '\n\nPS: ' + c.ps_line;
  if (c.followup_2_body) text += '\n\n---\nFOLLOW-UP 2:\nSubject: ' + (c.followup_2_subject||'') + '\n\n' + c.followup_2_body;
  if (c.followup_3_body) text += '\n\n---\nFOLLOW-UP 3:\nSubject: ' + (c.followup_3_subject||'') + '\n\n' + c.followup_3_body;
  const btn = e.target;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

function copyText(e, text) {
  e.stopPropagation();
  const btn = e.target;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

function downloadMarkdown() {
  if (!currentData) return;
  let md = '# ' + (currentData.domain||'Company') + ' - Prospecting Kit\n\n';
  if (currentData.offer_recommendation) {
    md += '## Offer Recommendation: ' + currentData.offer_recommendation + '\n' + (currentData.offer_reasoning||'') + '\n\n';
  }
  if (currentData.icp_profile) {
    const icp = currentData.icp_profile;
    md += '## ICP Profile\n\n';
    if (icp.target_titles?.length)     md += '**Titles:** ' + icp.target_titles.join(', ') + '\n\n';
    if (icp.target_industries?.length) md += '**Industries:** ' + icp.target_industries.join(', ') + '\n\n';
    if (icp.company_size)              md += '**Company Size:** ' + icp.company_size + '\n\n';
    if (icp.apollo_search)             md += '**Apollo Search:** ' + icp.apollo_search + '\n\n';
    if (icp.linkedin_search)           md += '**LinkedIn Search:** ' + icp.linkedin_search + '\n\n';
  }
  md += '## Company Analysis\n\n' + (currentData.company_analysis||'') + '\n\n';
  md += '## Company Intel\n\n' + (currentData.brief||'') + '\n\n';
  md += '## Campaigns\n\n';
  (currentData.campaigns||[]).forEach((c,i) => {
    md += '### ' + (c.type||'Campaign '+(i+1)) + ': ' + (c.offer_name||'') + '\n\n';
    md += '**What You Give Away:** ' + (c.what_youre_giving||'') + '\n\n';
    if (c.implicit_objection) md += '**Implicit Objection:** ' + c.implicit_objection + '\n\n';
    md += '**Target ICP:** ' + (c.target_icp||'') + '\n\n';
    md += '**Apollo:** ' + (c.apollo_search||'') + '\n\n';
    md += '**LinkedIn:** ' + (c.linkedin_search||'') + '\n\n';
    md += '**Email 1 Subject:** ' + (c.subject_line||'') + '\n\n' + (c.email_body||'') + '\n\n';
    if (c.ps_line)        md += 'PS: ' + c.ps_line + '\n\n';
    if (c.followup_2_body) md += '**Email 2 Subject:** ' + (c.followup_2_subject||'') + '\n\n' + c.followup_2_body + '\n\n';
    if (c.followup_3_body) md += '**Email 3 Subject:** ' + (c.followup_3_subject||'') + '\n\n' + c.followup_3_body + '\n\n';
    md += '---\n\n';
  });
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (currentData.domain||'company').replace(/\./g,'_') + '_prospecting_kit.md';
  a.click();
}

document.getElementById('urlInput').addEventListener('keydown', e => { if (e.key==='Enter') generate(); });
document.getElementById('productInput').addEventListener('keydown', e => { if (e.key==='Enter') generate(); });
</script>
</body>
</html>"""


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json()
    url = data.get("url", "").strip()
    my_company_url = data.get("my_company_url", "").strip()
    seller_info = data.get("seller_info", None)

    if not url:
        return jsonify({"error": "Please enter a target URL"}), 400
    if not my_company_url:
        return jsonify({"error": "Please enter your company URL"}), 400

    start = time.time()

    try:
        scraped = scrape_website(url)
        if not scraped:
            return jsonify({"error": f"Could not scrape {url}. The site may be blocking requests or the URL may be invalid."}), 400

        # Scrape the seller's own company site so campaigns reference real wins, customers, value props
        seller_scraped = scrape_website(my_company_url)
        if seller_scraped:
            if seller_info is None:
                seller_info = {}
            if not seller_info.get("company_name"):
                seller_info["company_name"] = "My Company"
            seller_info["seller_company_url"] = my_company_url
            seller_info["seller_company_text"] = seller_scraped["all_text"]

        result = run_full_pipeline(scraped, seller_info)
        result["duration_seconds"] = round(time.time() - start, 1)
        if seller_scraped:
            result["seller_pages_scraped"] = seller_scraped["pages_found"]
            result["seller_chars_scraped"] = seller_scraped["total_chars"]
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
