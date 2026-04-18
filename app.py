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
<style>
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
    background: #F9FAFB;
    color: #111827;
    line-height: 1.6;
    font-size: 15px;
  }

  .container { max-width: 880px; margin: 0 auto; padding: 0 24px; }

  /* ── Header / Hero ── */
  .hero {
    background: #fff;
    border-bottom: 1px solid #E5E7EB;
    padding: 52px 0 44px;
    text-align: center;
  }
  .hero h1 {
    font-size: 30px;
    font-weight: 700;
    color: #111827;
    letter-spacing: -0.5px;
    margin-bottom: 10px;
  }
  .hero .subtitle {
    font-size: 16px;
    color: #6B7280;
    max-width: 560px;
    margin: 0 auto 36px;
  }

  .steps {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    gap: 0;
    max-width: 680px;
    margin: 0 auto;
  }
  .step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 16px 12px;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
  }
  .step-icon {
    font-size: 22px;
    margin-bottom: 8px;
  }
  .step-num {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #2563EB;
    margin-bottom: 3px;
  }
  .step-title {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
  }
  .step-desc {
    font-size: 12px;
    color: #9CA3AF;
    line-height: 1.4;
  }
  .step-arrow {
    font-size: 18px;
    color: #D1D5DB;
    align-self: center;
    padding: 0 10px;
    flex-shrink: 0;
  }

  /* ── Main layout ── */
  main { padding: 32px 0 60px; }

  /* ── Cards ── */
  .card {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 20px;
  }
  .card-title {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 20px;
  }

  /* ── Form ── */
  .form-group { margin-bottom: 20px; }
  .form-group:last-child { margin-bottom: 0; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
  }
  .required-dot {
    display: inline-block;
    width: 5px;
    height: 5px;
    background: #2563EB;
    border-radius: 50%;
    margin-left: 4px;
    vertical-align: middle;
    position: relative;
    top: -1px;
  }
  .helper {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 5px;
    line-height: 1.4;
  }
  input[type="text"], input[type="url"], textarea {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    font-size: 14px;
    color: #111827;
    background: #fff;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    font-family: inherit;
  }
  input[type="text"]:focus, input[type="url"]:focus, textarea:focus {
    border-color: #2563EB;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
  }
  input::placeholder, textarea::placeholder { color: #9CA3AF; }
  textarea { resize: vertical; min-height: 80px; }

  .optional-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    color: #9CA3AF;
    background: #F3F4F6;
    border-radius: 4px;
    padding: 1px 6px;
    margin-left: 6px;
    vertical-align: middle;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  .info-tip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #2563EB;
    margin-top: 5px;
    cursor: default;
  }

  /* ── Buttons ── */
  .btn-primary {
    display: block;
    width: 100%;
    background: #2563EB;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 13px 24px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    text-align: center;
    transition: background 0.15s;
    font-family: inherit;
    margin-top: 24px;
  }
  .btn-primary:hover { background: #1D4ED8; }
  .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

  .btn-outline {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fff;
    color: #374151;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
  }
  .btn-outline:hover { background: #F9FAFB; border-color: #9CA3AF; }

  /* ── Loading ── */
  #loadingBox { display: none; }
  .loading-card {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 36px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 20px;
    text-align: center;
  }
  .loading-title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 6px;
  }
  .loading-subtitle {
    font-size: 14px;
    color: #6B7280;
    margin-bottom: 32px;
  }
  .loading-steps-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 360px;
    margin: 0 auto;
    text-align: left;
  }
  .loading-step-item {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: #9CA3AF;
    transition: color 0.3s;
  }
  .loading-step-item.active { color: #111827; }
  .loading-step-item.done { color: #059669; }
  .step-icon-sm {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    flex-shrink: 0;
    border: 2px solid #E5E7EB;
    color: #D1D5DB;
    transition: all 0.3s;
  }
  .loading-step-item.active .step-icon-sm {
    border-color: #2563EB;
    background: #EFF6FF;
    color: #2563EB;
  }
  .loading-step-item.done .step-icon-sm {
    border-color: #059669;
    background: #ECFDF5;
    color: #059669;
  }
  .spinner-inline {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid #DBEAFE;
    border-top-color: #2563EB;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Error ── */
  .error-box {
    display: none;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    color: #DC2626;
    padding: 14px 18px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-size: 14px;
  }

  /* ── Results ── */
  #results { display: none; }

  /* ── Summary Card ── */
  .summary-card {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 24px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 20px;
  }
  .summary-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 16px;
  }
  .summary-name {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
  }
  .summary-oneliner {
    font-size: 14px;
    color: #6B7280;
    margin-top: 3px;
  }
  .gtm-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .gtm-plg { background: #ECFDF5; color: #059669; }
  .gtm-sales { background: #EFF6FF; color: #2563EB; }
  .gtm-hybrid { background: #F5F3FF; color: #7C3AED; }

  .summary-stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    border-top: 1px solid #F3F4F6;
    padding-top: 16px;
    margin-top: 4px;
  }
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .stat-value {
    font-size: 20px;
    font-weight: 700;
    color: #111827;
    line-height: 1;
  }
  .stat-label { font-size: 12px; color: #9CA3AF; margin-top: 3px; }
  .summary-serve {
    font-size: 13px;
    color: #6B7280;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #F3F4F6;
  }
  .summary-serve strong { color: #374151; }

  /* ── Tabs ── */
  .tabs-section { margin-bottom: 4px; }
  .tab-bar {
    display: flex;
    border-bottom: 2px solid #E5E7EB;
    margin-bottom: 20px;
    gap: 0;
  }
  .tab-btn {
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
    color: #9CA3AF;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
    font-family: inherit;
  }
  .tab-btn:hover { color: #374151; }
  .tab-btn.active { color: #2563EB; border-bottom-color: #2563EB; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }

  /* ── Campaign cards ── */
  .campaign-card {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 16px;
  }
  .campaign-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
  }
  .camp-badge {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
  }
  .camp-badge-blue { background: #EFF6FF; color: #2563EB; }
  .camp-badge-green { background: #ECFDF5; color: #059669; }
  .camp-badge-orange { background: #FFF7ED; color: #EA580C; }
  .camp-name {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
  }

  .field-section { margin-bottom: 16px; }
  .field-section:last-child { margin-bottom: 0; }
  .field-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9CA3AF;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .field-text { font-size: 14px; color: #374151; line-height: 1.6; }

  /* Objection box */
  .objection-box {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 16px;
  }
  .objection-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #B45309;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .objection-text { font-size: 13px; color: #78350F; line-height: 1.6; }

  /* Code blocks for queries */
  .code-block {
    background: #F3F4F6;
    border-radius: 6px;
    padding: 10px 14px;
    font-family: 'SF Mono', 'Fira Code', 'Fira Mono', 'Roboto Mono', monospace;
    font-size: 13px;
    color: #374151;
    line-height: 1.5;
    word-break: break-word;
  }

  /* Email sub-cards */
  .email-card {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 16px;
    position: relative;
  }
  .email-subject-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #E5E7EB;
  }
  .email-subject {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    flex: 1;
  }
  .email-body-text {
    font-size: 14px;
    color: #374151;
    line-height: 1.7;
    white-space: pre-wrap;
  }
  .ps-text {
    font-size: 13px;
    color: #6B7280;
    font-style: italic;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #F3F4F6;
  }

  .word-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    white-space: nowrap;
  }
  .word-good { background: #D1FAE5; color: #065F46; }
  .word-warn { background: #FEF3C7; color: #92400E; }

  .copy-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    background: #fff;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
    color: #374151;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
  }
  .copy-btn:hover { background: #F9FAFB; border-color: #9CA3AF; }
  .copy-btn.copied { background: #ECFDF5; color: #059669; border-color: #A7F3D0; }

  /* Follow-up accordion */
  .followup-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #2563EB;
    cursor: pointer;
    margin-top: 14px;
    padding: 6px 0;
    user-select: none;
    background: none;
    border: none;
    font-family: inherit;
  }
  .followup-toggle:hover { color: #1D4ED8; }
  .followup-toggle .arrow-icon { font-size: 10px; transition: transform 0.2s; }
  .followup-toggle.open .arrow-icon { transform: rotate(90deg); }
  .followup-area { display: none; margin-top: 12px; }
  .followup-area.open { display: block; }
  .followup-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9CA3AF;
    margin-top: 14px;
    margin-bottom: 6px;
  }
  .followup-area .email-card { border-color: #DBEAFE; }

  /* ── Brief tab ── */
  .brief-section { margin-bottom: 20px; }
  .brief-section-title {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #F3F4F6;
  }
  .brief-content { font-size: 14px; color: #374151; line-height: 1.7; }
  .brief-content h1, .brief-content h2, .brief-content h3 {
    color: #111827;
    margin-top: 14px;
    margin-bottom: 6px;
    font-size: 15px;
  }
  .brief-content ul, .brief-content ol { padding-left: 20px; margin: 6px 0; }
  .brief-content li { margin-bottom: 4px; }

  .copy-box {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 16px;
    position: relative;
  }
  .copy-box .copy-btn { top: 10px; right: 10px; }

  /* ── Analysis tab ── */
  .analysis-section {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
  }
  .analysis-section-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #2563EB;
    margin-bottom: 10px;
  }
  .analysis-content { font-size: 14px; color: #374151; line-height: 1.7; white-space: pre-wrap; }

  /* ── Footer ── */
  .footer {
    text-align: center;
    color: #9CA3AF;
    font-size: 13px;
    padding: 24px 0;
    border-top: 1px solid #E5E7EB;
    margin-top: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .footer-meta { display: none; }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .hero { padding: 36px 0 32px; }
    .hero h1 { font-size: 22px; }
    .steps { flex-direction: column; gap: 8px; }
    .step-arrow { display: none; }
    .form-row { grid-template-columns: 1fr; }
    .container { padding: 0 16px; }
    .card { padding: 20px 16px; }
    .summary-top { flex-direction: column; }
    .tab-btn { padding: 10px 14px; font-size: 13px; }
  }
</style>
</head>
<body>

<!-- Hero -->
<header class="hero">
  <div class="container">
    <h1>Research &amp; Prospecting Tool</h1>
    <p class="subtitle">Paste a company URL. Get full company intelligence, buyer profiles, and personalized outreach in seconds.</p>
    <div class="steps">
      <div class="step">
        <div class="step-icon">🔍</div>
        <div class="step-num">Step 1</div>
        <div class="step-title">Research</div>
        <div class="step-desc">Scrape website, extract customers &amp; case studies</div>
      </div>
      <div class="step-arrow">›</div>
      <div class="step">
        <div class="step-icon">🎯</div>
        <div class="step-num">Step 2</div>
        <div class="step-title">Build ICP</div>
        <div class="step-desc">Define buyer profile, generate search queries</div>
      </div>
      <div class="step-arrow">›</div>
      <div class="step">
        <div class="step-icon">✉️</div>
        <div class="step-num">Step 3</div>
        <div class="step-title">Create Outreach</div>
        <div class="step-desc">3 campaign angles with ready-to-send emails</div>
      </div>
    </div>
  </div>
</header>

<main>
  <div class="container">

    <!-- Input card -->
    <div class="card" style="margin-top: 28px;">
      <div class="card-title">Generate Prospecting Kit</div>

      <div class="form-group">
        <label>Target Company URL <span class="required-dot"></span></label>
        <input type="url" id="urlInput" placeholder="https://www.company.com" autocomplete="off" />
        <p class="helper">We'll scrape their site to extract customers, case studies, and GTM signals automatically.</p>
      </div>

      <div class="form-group">
        <label>What product are you selling? <span class="required-dot"></span></label>
        <input type="text" id="productInput" placeholder="e.g., AI-powered lead scoring platform" />
        <p class="helper">Be specific. If your company sells multiple products, name the one you're responsible for.</p>
      </div>

      <div class="form-group">
        <label>Your proof points <span class="optional-badge">optional</span></label>
        <textarea id="proofInput" rows="3" placeholder="e.g., Helped Ramp's SDR team book 3x more meetings in 60 days. Notion cut list building from 4 hours to 20 minutes per week."></textarea>
        <p class="helper">2-3 specific customer outcomes with names and numbers. Makes emails dramatically better.</p>
      </div>

      <div class="form-group">
        <label>Sample buyer LinkedIn profiles <span class="optional-badge">optional</span></label>
        <input type="text" id="linkedinInput" placeholder="Paste 1-3 LinkedIn profile URLs, comma-separated" />
        <p class="helper">Providing example buyers improves ICP accuracy and outreach targeting.</p>
        <p class="info-tip">ℹ️ Analyzing real buyer profiles helps the tool understand your actual ICP instead of guessing.</p>
      </div>

      <button class="btn-primary" id="generateBtn" onclick="generate()">Generate Prospecting Kit</button>
    </div>

    <!-- Loading state -->
    <div id="loadingBox">
      <div class="loading-card">
        <div class="loading-title">Building your prospecting kit…</div>
        <div class="loading-subtitle">This takes 30-60 seconds. Grab a coffee.</div>
        <div class="loading-steps-list" id="loadingStepsList">
          <div class="loading-step-item" id="lstep-0">
            <div class="step-icon-sm">1</div>
            <span>Scraping website</span>
          </div>
          <div class="loading-step-item" id="lstep-1">
            <div class="step-icon-sm">2</div>
            <span>Analyzing company intelligence</span>
          </div>
          <div class="loading-step-item" id="lstep-2">
            <div class="step-icon-sm">3</div>
            <span>Generating campaigns &amp; emails</span>
          </div>
          <div class="loading-step-item" id="lstep-3">
            <div class="step-icon-sm">4</div>
            <span>Building follow-up sequences</span>
          </div>
          <div class="loading-step-item" id="lstep-4">
            <div class="step-icon-sm">5</div>
            <span>Assembling your kit</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div class="error-box" id="errorBox"></div>

    <!-- Results -->
    <div id="results">

      <!-- Company Summary Card -->
      <div class="summary-card" id="summaryCard"></div>

      <!-- Tabs -->
      <div class="tabs-section">
        <div class="tab-bar">
          <button class="tab-btn active" onclick="switchTab('campaigns', this)">Campaigns</button>
          <button class="tab-btn" onclick="switchTab('brief', this)">Company Brief</button>
          <button class="tab-btn" onclick="switchTab('analysis', this)">Full Analysis</button>
        </div>

        <div class="tab-pane active" id="tab-campaigns">
          <div id="campaignsGrid"></div>
        </div>

        <div class="tab-pane" id="tab-brief">
          <div class="card">
            <div class="brief-content" id="briefContent"></div>
          </div>
        </div>

        <div class="tab-pane" id="tab-analysis">
          <div id="analysisGrid"></div>
        </div>
      </div>

    </div>

    <!-- Footer -->
    <div class="footer">
      <span class="footer-meta" id="footerMeta"></span>
      <button class="btn-outline" id="downloadBtn" onclick="downloadMarkdown()" style="display:none;">
        ↓ Download as Markdown
      </button>
    </div>

  </div>
</main>

<script>
let currentData = null;

/* ── Utilities ── */
function wordCount(text) {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(w => w.length > 0).length;
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
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

/* Parse the raw analysis text into sections */
function parseAnalysisSections(text) {
  const sections = {};
  const parts = text.split(/\n(?=## )/);
  for (const part of parts) {
    const m = part.match(/^## ([^\n]+)\n([\s\S]*)/);
    if (m) {
      sections[m[1].trim()] = m[2].trim();
    }
  }
  return sections;
}

function getGTMType(text) {
  if (!text) return { label: 'Unknown', cls: 'gtm-hybrid' };
  const t = text.toLowerCase();
  if (t.includes('product-led') || t.includes('plg') || t.includes('self-serve')) {
    return { label: 'Product-Led (PLG)', cls: 'gtm-plg', dot: '🟢' };
  }
  if (t.includes('sales-led') || t.includes('sales led')) {
    return { label: 'Sales-Led', cls: 'gtm-sales', dot: '🔵' };
  }
  return { label: 'Hybrid', cls: 'gtm-hybrid', dot: '🟣' };
}

function countListItems(text) {
  if (!text) return 0;
  const lines = text.split('\n').filter(l => l.match(/^[-*•]|\d+\./));
  return Math.max(lines.length, text.trim() !== 'Not found on website.' ? 1 : 0);
}

/* ── Seller info payload ── */
function getSellerInfo() {
  const product = document.getElementById('productInput').value.trim();
  const proof   = document.getElementById('proofInput').value.trim();
  const linkedin = document.getElementById('linkedinInput').value.trim();
  if (!product && !proof) return null;
  const buyerStr = linkedin ? 'LinkedIn profiles: ' + linkedin : '';
  return {
    company_name: 'My Company',
    what_you_sell: product,
    customer_wins: proof,
    buyer_persona: buyerStr,
  };
}

/* ── Loading state ── */
let loadingTimer = null;
let currentStep = 0;

function startLoading() {
  currentStep = 0;
  document.querySelectorAll('.loading-step-item').forEach((el, i) => {
    el.className = 'loading-step-item' + (i === 0 ? ' active' : '');
    el.querySelector('.step-icon-sm').innerHTML = i === 0
      ? '<span class="spinner-inline"></span>'
      : (i + 1);
  });

  loadingTimer = setInterval(() => {
    const prev = document.getElementById('lstep-' + currentStep);
    if (prev) {
      prev.className = 'loading-step-item done';
      prev.querySelector('.step-icon-sm').textContent = '✓';
    }
    currentStep++;
    const next = document.getElementById('lstep-' + currentStep);
    if (next) {
      next.className = 'loading-step-item active';
      next.querySelector('.step-icon-sm').innerHTML = '<span class="spinner-inline"></span>';
    }
  }, 9000);
}

function stopLoading() {
  if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; }
}

/* ── Generate ── */
async function generate() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) {
    document.getElementById('urlInput').focus();
    return;
  }
  const product = document.getElementById('productInput').value.trim();
  if (!product) {
    document.getElementById('productInput').focus();
    return;
  }

  const btn = document.getElementById('generateBtn');
  const loadingBox = document.getElementById('loadingBox');
  const errorBox = document.getElementById('errorBox');
  const results = document.getElementById('results');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  loadingBox.style.display = 'block';
  errorBox.style.display = 'none';
  results.style.display = 'none';
  document.getElementById('downloadBtn').style.display = 'none';
  startLoading();

  try {
    const payload = { url };
    const seller = getSellerInfo();
    if (seller) payload.seller_info = seller;

    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    stopLoading();
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Something went wrong');
    }
    const data = await resp.json();
    currentData = data;
    renderResults(data);
  } catch (e) {
    stopLoading();
    errorBox.textContent = e.message;
    errorBox.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Prospecting Kit';
    loadingBox.style.display = 'none';
  }
}

/* ── Render Results ── */
function renderResults(data) {
  const results = document.getElementById('results');
  results.style.display = 'block';

  renderSummaryCard(data);
  renderCampaigns(data.campaigns || []);
  renderBrief(data.brief || '');
  renderAnalysis(data.company_analysis || '');

  const cached = data.from_cache ? ' · cached' : '';
  const sellerCtx = data.has_seller_context ? ' · seller context applied' : '';
  const meta = document.getElementById('footerMeta');
  meta.textContent = `${data.pages_scraped} pages scraped · ${(data.chars_scraped||0).toLocaleString()} chars · ${data.duration_seconds}s${cached}${sellerCtx}`;
  meta.style.display = 'block';
  document.getElementById('downloadBtn').style.display = 'inline-flex';

  // Reset to campaigns tab
  switchTab('campaigns', document.querySelector('.tab-btn'));
}

/* ── Summary Card ── */
function renderSummaryCard(data) {
  const sections = parseAnalysisSections(data.company_analysis || '');
  const companyName = sections['COMPANY NAME'] || data.domain || 'Company';
  const oneliner    = sections['ONE-LINER'] || '';
  const gtmText     = sections['GTM MOTION'] || '';
  const serveText   = sections['WHO THEY SERVE'] || '';
  const customersText = sections['NAMED CUSTOMERS'] || '';
  const caseText    = sections['CASE STUDIES'] || '';
  const proofText   = sections['PROOF POINTS'] || '';

  const gtm = getGTMType(gtmText);
  const custCount  = countListItems(customersText);
  const caseCount  = countListItems(caseText);
  const proofCount = countListItems(proofText);

  const offerHTML = data.offer_recommendation ? `
    <div style="margin-top:12px;padding-top:12px;border-top:1px solid #F3F4F6;display:flex;align-items:center;gap:10px;">
      <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#9CA3AF;">Recommended Approach</span>
      <span style="font-size:13px;font-weight:700;padding:3px 12px;border-radius:20px;background:${data.offer_recommendation.toUpperCase().includes('SQL')?'#EFF6FF':'#ECFDF5'};color:${data.offer_recommendation.toUpperCase().includes('SQL')?'#2563EB':'#059669'};">${esc(data.offer_recommendation)}</span>
      <span style="font-size:13px;color:#6B7280;">${esc(data.offer_reasoning||'')}</span>
    </div>` : '';

  document.getElementById('summaryCard').innerHTML = `
    <div class="summary-top">
      <div>
        <div class="summary-name">${esc(companyName)}</div>
        ${oneliner ? `<div class="summary-oneliner">${esc(oneliner)}</div>` : ''}
      </div>
      <span class="gtm-badge ${gtm.cls}">${gtm.dot || ''} ${esc(gtm.label)}</span>
    </div>
    <div class="summary-stats">
      <div class="stat-item">
        <div class="stat-value">${custCount}</div>
        <div class="stat-label">Named Customers</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">${caseCount}</div>
        <div class="stat-label">Case Studies</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">${proofCount}</div>
        <div class="stat-label">Proof Points</div>
      </div>
    </div>
    ${serveText ? `<div class="summary-serve"><strong>Serves:</strong> ${esc(serveText.split('\n')[0])}</div>` : ''}
    ${offerHTML}
  `;
}

/* ── Campaigns ── */
function renderCampaigns(campaigns) {
  const grid = document.getElementById('campaignsGrid');
  grid.innerHTML = '';

  if (!campaigns.length) {
    grid.innerHTML = '<p style="color:#9CA3AF;text-align:center;padding:32px;">No campaigns generated.</p>';
    return;
  }

  campaigns.forEach((c, i) => {
    const badgeMap = { green: 'camp-badge-green', orange: 'camp-badge-orange', blue: 'camp-badge-blue' };
    const badgeCls = badgeMap[c.badge_color] || 'camp-badge-blue';
    const wc = wordCount(c.email_body);
    const wcCls = (wc >= 70 && wc <= 90) ? 'word-good' : 'word-warn';

    const objHTML = c.implicit_objection ? `
      <div class="objection-box">
        <div class="objection-label">⚠ Implicit Objection &amp; How This Email Handles It</div>
        <div class="objection-text">${esc(c.implicit_objection)}</div>
      </div>` : '';

    const hasFollowups = c.followup_2_body || c.followup_3_body;
    const wc2 = wordCount(c.followup_2_body);
    const wc3 = wordCount(c.followup_3_body);
    const wc2Cls = (wc2 >= 50 && wc2 <= 90) ? 'word-good' : 'word-warn';
    const wc3Cls = (wc3 >= 40 && wc3 <= 80) ? 'word-good' : 'word-warn';

    const followupHTML = hasFollowups ? `
      <button class="followup-toggle" onclick="toggleFollowup(this, 'fu-${i}')">
        <span class="arrow-icon">▶</span> Show follow-up sequence (Email 2 &amp; 3)
      </button>
      <div class="followup-area" id="fu-${i}">
        <div class="followup-label">Email 2 — Flip Value Prop, Lower Ask</div>
        <div class="email-card">
          <div class="email-subject-row">
            <span class="email-subject">Subject: ${esc(c.followup_2_subject || '')}</span>
            <span class="word-badge ${wc2Cls}">${wc2} words</span>
          </div>
          <div class="email-body-text">${esc(c.followup_2_body || '')}</div>
        </div>
        <div class="followup-label">Email 3 — Free Value Taste</div>
        <div class="email-card">
          <div class="email-subject-row">
            <span class="email-subject">Subject: ${esc(c.followup_3_subject || '')}</span>
            <span class="word-badge ${wc3Cls}">${wc3} words</span>
          </div>
          <div class="email-body-text">${esc(c.followup_3_body || '')}</div>
        </div>
      </div>` : '';

    grid.innerHTML += `
      <div class="campaign-card">
        <div class="campaign-header">
          <span class="camp-badge ${badgeCls}">${esc(c.type || '')}</span>
          <span class="camp-name">${esc(c.offer_name || '')}</span>
        </div>

        <div class="field-section">
          <div class="field-label">🎁 What You're Giving Away</div>
          <div class="field-text">${esc(c.what_youre_giving || '')}</div>
        </div>

        <div class="field-section">
          <div class="field-label">✅ Why It Converts</div>
          <div class="field-text">${esc(c.why_it_converts || '')}</div>
        </div>

        ${objHTML}

        <div class="field-section">
          <div class="field-label">👤 Target ICP</div>
          <div class="field-text">${esc(c.target_icp || '')}</div>
        </div>

        <div class="field-section">
          <div class="field-label">🔎 Apollo Search Query</div>
          <div class="code-block">${esc(c.apollo_search || '')}</div>
        </div>

        <div class="field-section">
          <div class="field-label">🔗 LinkedIn Sales Nav Search</div>
          <div class="code-block">${esc(c.linkedin_search || '')}</div>
        </div>

        <div class="field-section">
          <div class="field-label">✉ Email 1</div>
          <div class="email-card">
            <button class="copy-btn" onclick="copyEmail(this, ${i})">Copy</button>
            <div class="email-subject-row">
              <span class="email-subject">Subject: ${esc(c.subject_line || '')}</span>
              <span class="word-badge ${wcCls}">${wc} words</span>
            </div>
            <div class="email-body-text">${esc(c.email_body || '')}</div>
            ${c.ps_line ? `<div class="ps-text">PS: ${esc(c.ps_line)}</div>` : ''}
          </div>
        </div>

        ${followupHTML}
      </div>`;
  });
}

/* ── Brief ── */
function renderBrief(text) {
  document.getElementById('briefContent').innerHTML = simpleMarkdown(text);
}

/* ── Full Analysis ── */
function renderAnalysis(text) {
  const grid = document.getElementById('analysisGrid');
  const sections = parseAnalysisSections(text);
  const order = [
    'COMPANY NAME','ONE-LINER','WHO THEY SERVE','NAMED CUSTOMERS',
    'CASE STUDIES','KEY VALUE PROPOSITIONS','PROOF POINTS',
    'PRICING MODEL','RECENT NEWS OR BLOG HIGHLIGHTS','GTM MOTION'
  ];

  let html = '';
  for (const key of order) {
    if (!sections[key]) continue;
    html += `
      <div class="analysis-section">
        <div class="analysis-section-title">${esc(key)}</div>
        <div class="analysis-content">${esc(sections[key])}</div>
      </div>`;
  }
  // Any extra sections not in order
  for (const key of Object.keys(sections)) {
    if (!order.includes(key)) {
      html += `
        <div class="analysis-section">
          <div class="analysis-section-title">${esc(key)}</div>
          <div class="analysis-content">${esc(sections[key])}</div>
        </div>`;
    }
  }
  grid.innerHTML = html || `<div class="analysis-section"><div class="analysis-content">${simpleMarkdown(text)}</div></div>`;
}

/* ── UI interactions ── */
function switchTab(tab, btn) {
  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const pane = document.getElementById('tab-' + tab);
  if (pane) pane.classList.add('active');
}

function toggleFollowup(btn, id) {
  btn.classList.toggle('open');
  const area = document.getElementById(id);
  if (area) area.classList.toggle('open');
}

function copyEmail(btn, idx) {
  if (!currentData || !currentData.campaigns[idx]) return;
  const c = currentData.campaigns[idx];
  let text = 'Subject: ' + (c.subject_line || '') + '\n\n' + (c.email_body || '');
  if (c.ps_line) text += '\n\nPS: ' + c.ps_line;
  if (c.followup_2_body) text += '\n\n---\nFOLLOW-UP 2:\nSubject: ' + (c.followup_2_subject || '') + '\n\n' + c.followup_2_body;
  if (c.followup_3_body) text += '\n\n---\nFOLLOW-UP 3:\nSubject: ' + (c.followup_3_subject || '') + '\n\n' + c.followup_3_body;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

function downloadMarkdown() {
  if (!currentData) return;
  let md = '# ' + (currentData.domain || 'Company') + ' - Prospecting Kit\n\n';
  if (currentData.offer_recommendation) {
    md += '## Offer Recommendation: ' + currentData.offer_recommendation + '\n' + (currentData.offer_reasoning || '') + '\n\n';
  }
  md += '## Company Analysis\n\n' + (currentData.company_analysis || '') + '\n\n';
  md += '## Company Brief\n\n' + (currentData.brief || '') + '\n\n';
  md += '## Campaigns\n\n';
  (currentData.campaigns || []).forEach((c, i) => {
    md += '### ' + (c.type || 'Campaign ' + (i+1)) + ': ' + (c.offer_name || '') + '\n\n';
    md += '**What You Give Away:** ' + (c.what_youre_giving || '') + '\n\n';
    if (c.implicit_objection) md += '**Implicit Objection:** ' + c.implicit_objection + '\n\n';
    md += '**Target ICP:** ' + (c.target_icp || '') + '\n\n';
    md += '**Apollo Search:** ' + (c.apollo_search || '') + '\n\n';
    md += '**LinkedIn Search:** ' + (c.linkedin_search || '') + '\n\n';
    md += '**Email 1 Subject:** ' + (c.subject_line || '') + '\n\n' + (c.email_body || '') + '\n\n';
    if (c.ps_line) md += 'PS: ' + c.ps_line + '\n\n';
    if (c.followup_2_body) md += '**Email 2 Subject:** ' + (c.followup_2_subject || '') + '\n\n' + c.followup_2_body + '\n\n';
    if (c.followup_3_body) md += '**Email 3 Subject:** ' + (c.followup_3_subject || '') + '\n\n' + c.followup_3_body + '\n\n';
    md += '---\n\n';
  });
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (currentData.domain || 'company').replace(/\./g, '_') + '_prospecting_kit.md';
  a.click();
}

document.getElementById('urlInput').addEventListener('keydown', e => { if (e.key === 'Enter') generate(); });
document.getElementById('productInput').addEventListener('keydown', e => { if (e.key === 'Enter') generate(); });
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
