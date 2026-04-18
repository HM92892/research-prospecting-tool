"""
Research & Prospecting Tool v2 - Flask Web App
Paste a company URL. Optionally add your seller context. Get a full prospecting kit.
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
<style>
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --text-primary:   #37352F;
    --text-title:     #191919;
    --text-secondary: #787774;
    --text-muted:     #9B9A97;
    --border:         #E9E9E7;
    --bg-page:        #FFFFFF;
    --bg-hover:       #F7F6F3;
    --bg-block:       #F7F6F3;
    --blue:           #2383E2;
    --blue-light:     #D3E5EF;
    --blue-dark:      #183B56;
    --green-light:    #DBEDDB;
    --green-dark:     #1C4428;
    --yellow-light:   #FDECC8;
    --yellow-dark:    #5C3B00;
    --purple-light:   #E8DEEE;
    --purple-dark:    #412D5A;
    --gray-light:     #E3E2E0;
    --gray-dark:      #5A5A58;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-page);
    color: var(--text-primary);
    font-size: 15px;
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }

  /* ── Progress bar ── */
  #progressBar {
    position: fixed;
    top: 0; left: 0;
    height: 2px;
    width: 0%;
    background: var(--blue);
    z-index: 9999;
    display: none;
    transition: width 0.4s ease;
  }

  /* ── Layout ── */
  .page { max-width: 900px; margin: 0 auto; padding: 0 24px; }

  /* ── Hero ── */
  .hero {
    padding: 64px 0 48px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 48px;
  }
  .hero-eyebrow {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 12px;
  }
  .hero h1 {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-title);
    letter-spacing: -0.5px;
    margin-bottom: 10px;
    line-height: 1.2;
  }
  .hero-sub {
    font-size: 16px;
    color: var(--text-secondary);
    max-width: 580px;
    margin-bottom: 40px;
  }

  .steps-row {
    display: grid;
    grid-template-columns: 1fr 24px 1fr 24px 1fr;
    align-items: center;
    gap: 0;
  }
  .step-card {
    background: var(--bg-hover);
    border-radius: 6px;
    padding: 14px 16px;
  }
  .step-icon-lg { font-size: 18px; margin-bottom: 6px; }
  .step-num-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--blue);
    margin-bottom: 2px;
  }
  .step-card-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-title);
    margin-bottom: 2px;
  }
  .step-card-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
  .step-sep { text-align: center; color: var(--text-muted); font-size: 16px; }

  /* ── Input form ── */
  .input-section { margin-bottom: 48px; }
  .section-heading {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-title);
    margin-bottom: 24px;
  }
  .form-group { margin-bottom: 22px; }
  .form-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
  }
  .form-label .req { color: var(--blue); margin-left: 2px; }
  .opt-tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--text-muted);
    background: var(--gray-light);
    border-radius: 3px;
    padding: 1px 5px;
    margin-left: 6px;
    vertical-align: middle;
  }
  .form-input, .form-textarea {
    width: 100%;
    padding: 9px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 14px;
    font-family: inherit;
    color: var(--text-primary);
    background: #fff;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .form-input::placeholder, .form-textarea::placeholder { color: #C4C4C0; }
  .form-input:focus, .form-textarea:focus {
    border-color: var(--blue);
    box-shadow: 0 0 0 2px rgba(35,131,226,0.14);
  }
  .form-textarea { resize: vertical; min-height: 76px; }
  .form-helper {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 5px;
    line-height: 1.4;
  }
  .form-tip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--blue);
    margin-top: 4px;
  }

  .btn-primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: var(--blue);
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: background 0.15s;
    width: 100%;
    margin-top: 8px;
  }
  .btn-primary:hover { background: #1a6fc4; }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

  /* ── Loading ── */
  .loading-indicator {
    display: none;
    padding: 16px 0 8px;
    text-align: center;
  }
  .loading-step-text {
    font-size: 13px;
    color: var(--text-secondary);
    font-style: italic;
  }
  .loading-dot-anim::after {
    content: '';
    animation: dots 1.2s steps(3,end) infinite;
  }
  @keyframes dots {
    0%   { content: '.'; }
    33%  { content: '..'; }
    66%  { content: '...'; }
    100% { content: ''; }
  }

  /* ── Error ── */
  .error-block {
    display: none;
    background: #FFF0F0;
    border-left: 3px solid #E03E3E;
    border-radius: 4px;
    padding: 12px 16px;
    font-size: 14px;
    color: #6E2B20;
    margin-bottom: 32px;
  }

  /* ── Divider ── */
  .divider { border: none; border-top: 1px solid var(--border); margin: 32px 0; }
  .divider-sm { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

  /* ── Results ── */
  #results { display: none; }

  /* ── Summary block ── */
  .summary-callout {
    display: flex;
    gap: 0;
    background: var(--bg-block);
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 32px;
  }
  .summary-accent { width: 4px; background: var(--blue); flex-shrink: 0; }
  .summary-body { padding: 20px 24px; flex: 1; }
  .summary-company-name {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-title);
    margin-bottom: 4px;
    letter-spacing: -0.3px;
  }
  .summary-oneliner {
    font-size: 15px;
    color: var(--text-secondary);
    margin-bottom: 12px;
  }
  .props-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .prop-sep { color: var(--text-muted); font-size: 12px; }
  .summary-serve { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
  .summary-serve strong { color: var(--text-primary); }
  .summary-offer { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }

  /* ── Notion tags ── */
  .tag {
    display: inline-flex;
    align-items: center;
    font-size: 12px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 3px;
    line-height: 1.5;
    white-space: nowrap;
  }
  .tag-blue   { background: var(--blue-light);   color: var(--blue-dark); }
  .tag-green  { background: var(--green-light);  color: var(--green-dark); }
  .tag-yellow { background: var(--yellow-light); color: var(--yellow-dark); }
  .tag-purple { background: var(--purple-light); color: var(--purple-dark); }
  .tag-gray   { background: var(--gray-light);   color: var(--gray-dark); }

  /* ── Tabs ── */
  .tab-bar {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
  }
  .tab-btn {
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-muted);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    cursor: pointer;
    font-family: inherit;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab-btn:hover { color: var(--text-primary); }
  .tab-btn.active { color: var(--blue); border-bottom-color: var(--blue); font-weight: 600; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }

  /* ── Campaign section (Notion doc style) ── */
  .campaign-block { padding: 4px 0; }
  .campaign-block + .campaign-block { border-top: 1px solid var(--border); padding-top: 32px; margin-top: 4px; }
  .campaign-top {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .campaign-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-title);
  }

  .field-block { margin-bottom: 18px; }
  .field-cap {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    margin-bottom: 5px;
  }
  .field-body { font-size: 14px; color: var(--text-primary); line-height: 1.65; }

  /* Objection callout */
  .objection-callout {
    background: var(--yellow-light);
    border-radius: 4px;
    padding: 12px 14px;
    margin-bottom: 18px;
    display: flex;
    gap: 10px;
  }
  .objection-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
  .objection-inner { flex: 1; }
  .objection-cap {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--yellow-dark);
    margin-bottom: 4px;
  }
  .objection-text { font-size: 13px; color: #4a2f00; line-height: 1.6; }

  /* Code block */
  .code-block {
    background: var(--bg-block);
    border-radius: 4px;
    padding: 10px 12px;
    font-family: 'SF Mono', 'Fira Code', 'Roboto Mono', monospace;
    font-size: 12.5px;
    color: var(--text-primary);
    line-height: 1.6;
    word-break: break-word;
    position: relative;
  }
  .code-block:hover .code-copy { opacity: 1; }
  .code-copy {
    position: absolute;
    top: 6px; right: 6px;
    font-size: 11px;
    font-weight: 600;
    font-family: inherit;
    color: var(--text-muted);
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 2px 8px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .code-copy:hover { color: var(--text-primary); }
  .code-copy.copied { color: var(--green-dark); border-color: var(--green-light); background: var(--green-light); opacity: 1; }

  /* Toggle blocks */
  .toggle-block { margin-bottom: 8px; }
  .toggle-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.1s;
    user-select: none;
    flex-wrap: wrap;
  }
  .toggle-header:hover { background: var(--bg-hover); }
  .toggle-arrow {
    display: inline-block;
    font-size: 10px;
    color: var(--text-muted);
    transition: transform 0.15s;
    width: 14px;
    flex-shrink: 0;
  }
  .toggle-block.open .toggle-arrow { transform: rotate(90deg); }
  .toggle-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    flex-shrink: 0;
  }
  .toggle-subject { font-size: 14px; color: var(--text-title); flex: 1; min-width: 0; }
  .toggle-content {
    display: none;
    padding: 12px 8px 8px 22px;
    position: relative;
  }
  .toggle-block.open .toggle-content { display: block; }

  .email-body-text {
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.75;
    white-space: pre-wrap;
    margin-bottom: 10px;
  }
  .ps-line {
    font-size: 13px;
    color: var(--text-secondary);
    padding-top: 8px;
    border-top: 1px solid var(--border);
    margin-top: 4px;
  }
  .copy-email-btn {
    position: absolute;
    top: 8px; right: 0;
    font-size: 11px;
    font-weight: 600;
    font-family: inherit;
    color: var(--text-muted);
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 3px 10px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .copy-email-btn:hover { color: var(--text-primary); border-color: #aaa; }
  .copy-email-btn.copied { color: var(--green-dark); background: var(--green-light); border-color: var(--green-light); }

  .word-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 3px;
    flex-shrink: 0;
  }
  .wb-good { background: var(--green-light); color: var(--green-dark); }
  .wb-warn { background: var(--yellow-light); color: var(--yellow-dark); }

  /* ── ICP tab ── */
.icp-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}
.icp-block { }
.icp-signal-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.icp-signal-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  padding: 5px 0;
  border-bottom: 1px solid var(--border);
  line-height: 1.5;
}
.icp-signal-list li:last-child { border-bottom: none; }
.signal-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--blue);
  flex-shrink: 0;
  margin-top: 6px;
}
.tags-row { display: flex; flex-wrap: wrap; gap: 6px; }
.icp-note {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--blue-light);
  color: var(--blue-dark);
  font-size: 13px;
  font-weight: 500;
  padding: 8px 14px;
  border-radius: 4px;
  margin-bottom: 20px;
}
@media (max-width: 640px) { .icp-grid { grid-template-columns: 1fr; } }

/* ── Brief / Analysis sections ── */
  .content-section { margin-bottom: 28px; }
  .content-section-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-title);
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  .content-body { font-size: 14px; color: var(--text-primary); line-height: 1.7; }
  .content-body h1 { font-size: 20px; font-weight: 700; margin: 16px 0 6px; }
  .content-body h2 { font-size: 16px; font-weight: 600; margin: 14px 0 6px; color: var(--text-title); }
  .content-body h3 { font-size: 14px; font-weight: 600; margin: 12px 0 4px; }
  .content-body ul, .content-body ol { padding-left: 22px; margin: 6px 0; }
  .content-body li { margin-bottom: 4px; }
  .content-body strong { font-weight: 600; color: var(--text-title); }

  .analysis-section {
    padding-bottom: 20px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }
  .analysis-section:last-child { border-bottom: none; }
  .analysis-cap {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--blue);
    margin-bottom: 8px;
  }
  .analysis-body { font-size: 14px; color: var(--text-primary); line-height: 1.7; white-space: pre-wrap; }

  /* ── Download / footer ── */
  .results-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 20px 0 48px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
  }
  .meta-text { font-size: 12px; color: var(--text-muted); }
  .btn-outline {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    font-family: inherit;
    transition: background 0.12s, border-color 0.12s;
  }
  .btn-outline:hover { background: var(--bg-hover); border-color: #aaa; }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .hero { padding: 40px 0 32px; }
    .hero h1 { font-size: 24px; }
    .steps-row { grid-template-columns: 1fr; gap: 8px; }
    .step-sep { display: none; }
    .page { padding: 0 16px; }
    .tab-btn { padding: 8px 10px; font-size: 13px; }
    .campaign-top { flex-direction: column; align-items: flex-start; }
  }
</style>
</head>
<body>

<div id="progressBar"></div>

<div class="page">

  <!-- Hero -->
  <section class="hero">
    <div class="hero-eyebrow">AI-Powered SDR Tool</div>
    <h1>Research &amp; Prospecting Tool</h1>
    <p class="hero-sub">Paste a company URL. Get full company intelligence, buyer profiles, and personalized outreach in seconds.</p>
    <div class="steps-row">
      <div class="step-card">
        <div class="step-icon-lg">🔍</div>
        <div class="step-num-label">Step 1</div>
        <div class="step-card-title">Research</div>
        <div class="step-card-desc">Scrape website, extract customers &amp; case studies</div>
      </div>
      <div class="step-sep">›</div>
      <div class="step-card">
        <div class="step-icon-lg">🎯</div>
        <div class="step-num-label">Step 2</div>
        <div class="step-card-title">Build ICP</div>
        <div class="step-card-desc">Define buyer profile, generate search queries</div>
      </div>
      <div class="step-sep">›</div>
      <div class="step-card">
        <div class="step-icon-lg">✉️</div>
        <div class="step-num-label">Step 3</div>
        <div class="step-card-title">Create Outreach</div>
        <div class="step-card-desc">3 campaign angles with ready-to-send emails</div>
      </div>
    </div>
  </section>

  <!-- Input -->
  <section class="input-section">

    <div class="form-group">
      <label class="form-label" for="urlInput">Target company URL <span class="req">*</span></label>
      <input class="form-input" type="url" id="urlInput" placeholder="https://www.company.com" autocomplete="off" />
      <p class="form-helper">We'll scrape their site to extract customers, case studies, and GTM signals automatically.</p>
    </div>

    <div class="form-group">
      <label class="form-label" for="productInput">What product are you selling? <span class="req">*</span></label>
      <input class="form-input" type="text" id="productInput" placeholder="e.g., AI-powered lead scoring platform" />
      <p class="form-helper">Be specific. If your company sells multiple products, name the one you're responsible for.</p>
    </div>

    <div class="form-group">
      <label class="form-label" for="proofInput">Your proof points <span class="opt-tag">optional</span></label>
      <textarea class="form-textarea" id="proofInput" rows="3" placeholder="e.g., Helped Ramp's SDR team book 3x more meetings in 60 days. Notion cut list building from 4 hours to 20 minutes per week."></textarea>
      <p class="form-helper">2-3 specific customer outcomes with names and numbers. Makes emails dramatically better.</p>
    </div>

    <div class="form-group">
      <label class="form-label" for="linkedinInput">Sample buyer LinkedIn profiles <span class="opt-tag">optional</span></label>
      <input class="form-input" type="text" id="linkedinInput" placeholder="Paste 1-3 LinkedIn profile URLs, comma-separated" />
      <p class="form-helper">Providing example buyers improves ICP accuracy and outreach targeting.</p>
      <p class="form-tip">ℹ Analyzing real buyer profiles helps the tool understand your actual ICP instead of guessing.</p>
    </div>

    <button class="btn-primary" id="generateBtn" onclick="generate()">Generate Prospecting Kit</button>

    <div class="loading-indicator" id="loadingBox">
      <p class="loading-step-text"><span id="loadingStepText">Scraping website</span><span class="loading-dot-anim"></span></p>
    </div>

  </section>

  <!-- Error -->
  <div class="error-block" id="errorBox"></div>

  <!-- Results -->
  <div id="results">

    <!-- Summary callout -->
    <div class="summary-callout" id="summaryCallout"></div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('campaigns', this)">Campaigns</button>
      <button class="tab-btn" onclick="switchTab('icp', this)">ICP &amp; Targeting</button>
      <button class="tab-btn" onclick="switchTab('intel', this)">Company Intel</button>
      <button class="tab-btn" onclick="switchTab('analysis', this)">Full Analysis</button>
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

    <div class="results-footer" id="resultsFooter" style="display:none;">
      <span class="meta-text" id="metaText"></span>
      <button class="btn-outline" onclick="downloadMarkdown()">↓ Download as Markdown</button>
    </div>

  </div>

</div><!-- .page -->

<script>
let currentData = null;

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
  return `<span class="word-badge ${ok?'wb-good':'wb-warn'}">${n} words</span>`;
}

function simpleMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/^[-*] (.+)$/gm,'<li>$1</li>')
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
  const t = (text||'').toLowerCase();
  if (t.includes('product-led') || t.includes('plg') || t.includes('self-serve'))
    return { label:'Product-Led (PLG)', cls:'tag-green' };
  if (t.includes('sales-led') || t.includes('sales led'))
    return { label:'Sales-Led', cls:'tag-blue' };
  return { label:'Hybrid', cls:'tag-purple' };
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
let pbTimer = null;
function startProgress() {
  const bar = document.getElementById('progressBar');
  bar.style.display = 'block';
  bar.style.transition = 'none';
  bar.style.width = '0%';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    bar.style.transition = 'width 50s cubic-bezier(0.1, 0.9, 0.2, 1)';
    bar.style.width = '82%';
  }));
}
function finishProgress() {
  const bar = document.getElementById('progressBar');
  bar.style.transition = 'width 0.25s ease';
  bar.style.width = '100%';
  setTimeout(() => {
    bar.style.display = 'none';
    bar.style.width = '0%';
  }, 350);
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
  document.getElementById('loadingBox').style.display = 'block';
  stepTimer = setInterval(() => {
    stepIdx = Math.min(stepIdx + 1, STEPS.length - 1);
    document.getElementById('loadingStepText').textContent = STEPS[stepIdx];
  }, 9000);
}
function stopSteps() {
  if (stepTimer) { clearInterval(stepTimer); stepTimer = null; }
  document.getElementById('loadingBox').style.display = 'none';
}

/* ── Generate ── */
async function generate() {
  const url     = document.getElementById('urlInput').value.trim();
  const product = document.getElementById('productInput').value.trim();
  if (!url) { document.getElementById('urlInput').focus(); return; }
  if (!product) { document.getElementById('productInput').focus(); return; }

  const btn = document.getElementById('generateBtn');
  const errorBox = document.getElementById('errorBox');
  const results  = document.getElementById('results');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  errorBox.style.display = 'none';
  results.style.display = 'none';
  document.getElementById('resultsFooter').style.display = 'none';
  startProgress();
  startSteps();

  try {
    const payload = { url };
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
    errorBox.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Prospecting Kit';
  }
}

/* ── Render all ── */
function renderResults(data) {
  document.getElementById('results').style.display = 'block';
  renderSummary(data);
  renderCampaigns(data.campaigns || []);
  renderICP(data.icp_profile || {}, data);
  renderIntel(data.brief || '');
  renderAnalysis(data.company_analysis || '');
  const cached = data.from_cache ? ' · cached' : '';
  const selCtx = data.has_seller_context ? ' · seller context applied' : '';
  document.getElementById('metaText').textContent =
    `${data.pages_scraped} pages scraped · ${(data.chars_scraped||0).toLocaleString()} chars · ${data.duration_seconds}s${cached}${selCtx}`;
  document.getElementById('resultsFooter').style.display = 'flex';
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

  let offerLine = '';
  if (data.offer_recommendation) {
    const isSQL = data.offer_recommendation.toUpperCase().includes('SQL');
    const offerCls = isSQL ? 'tag-blue' : 'tag-green';
    offerLine = `<div class="summary-offer">
      <strong>Recommended approach:</strong>
      <span class="tag ${offerCls}" style="margin-left:6px;">${esc(data.offer_recommendation)}</span>
      <span style="font-size:13px;color:var(--text-secondary);margin-left:6px;">${esc(data.offer_reasoning||'')}</span>
    </div>`;
  }

  document.getElementById('summaryCallout').innerHTML = `
    <div class="summary-accent"></div>
    <div class="summary-body">
      <div class="summary-company-name">${esc(name)}</div>
      ${oneliner ? `<div class="summary-oneliner">${esc(oneliner)}</div>` : ''}
      <div class="props-row">
        <span class="tag ${gtm.cls}">${esc(gtm.label)}</span>
        ${custCt  ? `<span class="prop-sep">·</span><span class="tag tag-gray">${custCt} named customers</span>` : ''}
        ${caseCt  ? `<span class="prop-sep">·</span><span class="tag tag-gray">${caseCt} case studies</span>` : ''}
        ${proofCt ? `<span class="prop-sep">·</span><span class="tag tag-gray">${proofCt} proof points</span>` : ''}
      </div>
      ${serve ? `<div class="summary-serve"><strong>Serves:</strong> ${esc(serve.split('\n')[0])}</div>` : ''}
      ${offerLine}
    </div>`;
}

/* ── Campaigns ── */
function renderCampaigns(campaigns) {
  const grid = document.getElementById('campaignsGrid');
  if (!campaigns.length) {
    grid.innerHTML = '<p style="color:var(--text-muted);padding:32px 0;">No campaigns generated.</p>';
    return;
  }

  const tagMap = { blue:'tag-blue', green:'tag-green', orange:'tag-yellow' };

  grid.innerHTML = campaigns.map((c, i) => {
    const tagCls = tagMap[c.badge_color] || 'tag-blue';
    const n1 = wc(c.email_body);
    const n2 = wc(c.followup_2_body);
    const n3 = wc(c.followup_3_body);

    const objHTML = c.implicit_objection ? `
      <div class="objection-callout">
        <div class="objection-icon">⚠</div>
        <div class="objection-inner">
          <div class="objection-cap">Implicit Objection &amp; How This Email Handles It</div>
          <div class="objection-text">${esc(c.implicit_objection)}</div>
        </div>
      </div>` : '';

    const email1 = `
      <div class="toggle-block">
        <div class="toggle-header" onclick="toggleBlock(this)">
          <span class="toggle-arrow">▶</span>
          <span class="toggle-label">Email 1 —</span>
          <span class="toggle-subject">${esc(c.subject_line || '')}</span>
          ${wcBadge(n1,70,90)}
        </div>
        <div class="toggle-content">
          <button class="copy-email-btn" onclick="copyEmail(event,${i})">Copy</button>
          <div class="email-body-text">${esc(c.email_body || '')}</div>
          ${c.ps_line ? `<div class="ps-line">PS: ${esc(c.ps_line)}</div>` : ''}
        </div>
      </div>`;

    const followups = (c.followup_2_body || c.followup_3_body) ? `
      <div class="toggle-block" style="margin-top:4px;">
        <div class="toggle-header" onclick="toggleBlock(this)">
          <span class="toggle-arrow">▶</span>
          <span class="toggle-label" style="color:var(--text-secondary);">Show follow-up sequence (Email 2 &amp; 3)</span>
        </div>
        <div class="toggle-content" style="padding-left:8px;">
          ${c.followup_2_body ? `
            <div style="margin-bottom:14px;">
              <div class="field-cap" style="margin-bottom:6px;">Email 2 — Flip Value Prop, Lower Ask</div>
              <div class="toggle-block">
                <div class="toggle-header" onclick="toggleBlock(this)">
                  <span class="toggle-arrow">▶</span>
                  <span class="toggle-subject">${esc(c.followup_2_subject||'')}</span>
                  ${wcBadge(n2,50,90)}
                </div>
                <div class="toggle-content">
                  <div class="email-body-text">${esc(c.followup_2_body)}</div>
                </div>
              </div>
            </div>` : ''}
          ${c.followup_3_body ? `
            <div>
              <div class="field-cap" style="margin-bottom:6px;">Email 3 — Free Value Taste</div>
              <div class="toggle-block">
                <div class="toggle-header" onclick="toggleBlock(this)">
                  <span class="toggle-arrow">▶</span>
                  <span class="toggle-subject">${esc(c.followup_3_subject||'')}</span>
                  ${wcBadge(n3,40,80)}
                </div>
                <div class="toggle-content">
                  <div class="email-body-text">${esc(c.followup_3_body)}</div>
                </div>
              </div>
            </div>` : ''}
        </div>
      </div>` : '';

    return `
      <div class="campaign-block">
        <div class="campaign-top">
          <span class="tag ${tagCls}">${esc(c.type||'')}</span>
          <span class="campaign-title">${esc(c.offer_name||'')}</span>
        </div>

        <div class="field-block">
          <div class="field-cap">🎁 What You're Giving Away</div>
          <div class="field-body">${esc(c.what_youre_giving||'')}</div>
        </div>

        <div class="field-block">
          <div class="field-cap">✅ Why It Converts</div>
          <div class="field-body">${esc(c.why_it_converts||'')}</div>
        </div>

        ${objHTML}

        <div class="field-block">
          <div class="field-cap">👤 Target ICP</div>
          <div class="field-body">${esc(c.target_icp||'')}</div>
        </div>

        <div class="field-block">
          <div class="field-cap">Apollo Search Query</div>
          <div class="code-block">
            <button class="code-copy" onclick="copyText(event, ${JSON.stringify(c.apollo_search||'')})">Copy</button>
            ${esc(c.apollo_search||'')}
          </div>
        </div>

        <div class="field-block">
          <div class="field-cap">LinkedIn Sales Navigator Search</div>
          <div class="code-block">
            <button class="code-copy" onclick="copyText(event, ${JSON.stringify(c.linkedin_search||'')})">Copy</button>
            ${esc(c.linkedin_search||'')}
          </div>
        </div>

        <div class="field-block">
          <div class="field-cap">Emails</div>
          ${email1}
          ${followups}
        </div>
      </div>`;
  }).join('');
}

/* ── ICP & Targeting ── */
function renderICP(icp, data) {
  const el = document.getElementById('icpContent');
  if (!icp || Object.keys(icp).length === 0) {
    el.innerHTML = '<p style="color:var(--text-muted);padding:24px 0;">ICP data not available.</p>';
    return;
  }

  const titles     = Array.isArray(icp.target_titles)     ? icp.target_titles     : [];
  const industries = Array.isArray(icp.target_industries) ? icp.target_industries : [];
  const signals    = Array.isArray(icp.key_signals)       ? icp.key_signals       : [];
  const linkedinCount = icp.linkedin_profiles_analyzed || 0;

  const linkedinNote = linkedinCount > 0
    ? `<div class="icp-note">🔗 ICP refined using ${linkedinCount} sample buyer profile${linkedinCount > 1 ? 's' : ''}</div>`
    : '';

  const titlesHTML = titles.length
    ? titles.map(t => `<span class="tag tag-blue">${esc(t)}</span>`).join('')
    : '<span class="tag tag-gray">Not available</span>';

  const industriesHTML = industries.length
    ? industries.map(i => `<span class="tag tag-purple">${esc(i)}</span>`).join('')
    : '<span class="tag tag-gray">Not available</span>';

  const signalsHTML = signals.length
    ? `<ul class="icp-signal-list">${signals.map(s => `<li><span class="signal-dot"></span><span>${esc(s)}</span></li>`).join('')}</ul>`
    : '<p class="field-body">Not available</p>';

  el.innerHTML = `
    ${linkedinNote}

    <div class="icp-grid">
      <div class="icp-block">
        <div class="field-cap">TARGET JOB TITLES</div>
        <div class="tags-row" style="margin-top:6px;">${titlesHTML}</div>
      </div>
      <div class="icp-block">
        <div class="field-cap">TARGET INDUSTRIES</div>
        <div class="tags-row" style="margin-top:6px;">${industriesHTML}</div>
      </div>
      <div class="icp-block">
        <div class="field-cap">COMPANY SIZE</div>
        <div class="field-body" style="margin-top:6px;">${esc(icp.company_size || 'Not specified')}</div>
      </div>
      <div class="icp-block">
        <div class="field-cap">KEY BUYING SIGNALS</div>
        <div style="margin-top:6px;">${signalsHTML}</div>
      </div>
    </div>

    <hr class="divider">

    <div class="field-block">
      <div class="field-cap">Apollo Search Query</div>
      <div class="code-block">
        <button class="code-copy" onclick="copyText(event, ${JSON.stringify(icp.apollo_search||'')})">Copy</button>
        ${esc(icp.apollo_search || 'Not available')}
      </div>
    </div>

    <div class="field-block">
      <div class="field-cap">LinkedIn Sales Navigator Search</div>
      <div class="code-block">
        <button class="code-copy" onclick="copyText(event, ${JSON.stringify(icp.linkedin_search||'')})">Copy</button>
        ${esc(icp.linkedin_search || 'Not available')}
      </div>
    </div>

    ${icp.icp_reasoning ? `
    <hr class="divider">
    <div class="field-block">
      <div class="field-cap">ICP Reasoning</div>
      <div class="field-body">${esc(icp.icp_reasoning)}</div>
    </div>` : ''}
  `;
}

/* ── Company Intel ── */
function renderIntel(text) {
  const el = document.getElementById('intelContent');
  // Parse into sections
  const parts = text.split(/\n(?=## )/);
  let html = '';
  for (const p of parts) {
    const m = p.match(/^## ([^\n]+)\n?([\s\S]*)/);
    if (m) {
      html += `<div class="content-section">
        <div class="content-section-title">${esc(m[1].trim())}</div>
        <div class="content-body">${simpleMarkdown(m[2].trim())}</div>
      </div>`;
    } else if (p.match(/^# ([^\n]+)/)) {
      // Page title — skip or render as super heading
    } else if (p.trim()) {
      html += `<div class="content-body" style="margin-bottom:16px;">${simpleMarkdown(p.trim())}</div>`;
    }
  }
  el.innerHTML = html || `<div class="content-body">${simpleMarkdown(text)}</div>`;
}

/* ── Analysis ── */
function renderAnalysis(text) {
  const el = document.getElementById('analysisContent');
  const s = parseAnalysisSections(text);
  const ORDER = [
    'COMPANY NAME','ONE-LINER','WHO THEY SERVE','NAMED CUSTOMERS',
    'CASE STUDIES','KEY VALUE PROPOSITIONS','PROOF POINTS',
    'PRICING MODEL','RECENT NEWS OR BLOG HIGHLIGHTS','GTM MOTION','LIKELY BUYERS'
  ];
  let html = '';
  const rendered = new Set();
  for (const key of ORDER) {
    if (!s[key]) continue;
    rendered.add(key);
    html += `<div class="analysis-section">
      <div class="analysis-cap">${esc(key)}</div>
      <div class="analysis-body">${esc(s[key])}</div>
    </div>`;
  }
  for (const key of Object.keys(s)) {
    if (rendered.has(key)) continue;
    html += `<div class="analysis-section">
      <div class="analysis-cap">${esc(key)}</div>
      <div class="analysis-body">${esc(s[key])}</div>
    </div>`;
  }
  el.innerHTML = html || `<div class="analysis-body">${esc(text)}</div>`;
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
  md += '## Company Analysis\n\n' + (currentData.company_analysis||'') + '\n\n';
  md += '## Company Brief\n\n' + (currentData.brief||'') + '\n\n';
  md += '## Campaigns\n\n';
  (currentData.campaigns||[]).forEach((c,i) => {
    md += '### ' + (c.type||'Campaign '+(i+1)) + ': ' + (c.offer_name||'') + '\n\n';
    md += '**What You Give Away:** ' + (c.what_youre_giving||'') + '\n\n';
    if (c.implicit_objection) md += '**Implicit Objection:** ' + c.implicit_objection + '\n\n';
    md += '**Target ICP:** ' + (c.target_icp||'') + '\n\n';
    md += '**Apollo Search:** ' + (c.apollo_search||'') + '\n\n';
    md += '**LinkedIn Search:** ' + (c.linkedin_search||'') + '\n\n';
    md += '**Email 1 Subject:** ' + (c.subject_line||'') + '\n\n' + (c.email_body||'') + '\n\n';
    if (c.ps_line) md += 'PS: ' + c.ps_line + '\n\n';
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
    seller_info = data.get("seller_info", None)

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    start = time.time()

    try:
        scraped = scrape_website(url)
        if not scraped:
            return jsonify({"error": f"Could not scrape {url}. The site may be blocking requests or the URL may be invalid."}), 400

        result = run_full_pipeline(scraped, seller_info)
        result["duration_seconds"] = round(time.time() - start, 1)
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
