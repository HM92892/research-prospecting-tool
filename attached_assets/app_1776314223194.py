"""
Research & Prospecting Tool - Flask Web App
Paste a company URL. Get a full prospecting kit.
"""

from flask import Flask, request, jsonify, render_template_string
from scraper import scrape_website
from analyzer import run_full_pipeline
import time
import os
import json
import markdown

app = Flask(__name__)

# ============================================================
# HTML Template (single file, no external dependencies)
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research & Prospecting Tool</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0a0a;
    color: #e0e0e0;
    line-height: 1.6;
  }

  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 24px;
  }

  .header {
    text-align: center;
    margin-bottom: 48px;
  }

  .header h1 {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }

  .header p {
    font-size: 15px;
    color: #888;
  }

  .input-group {
    display: flex;
    gap: 12px;
    margin-bottom: 32px;
  }

  .input-group input {
    flex: 1;
    padding: 14px 18px;
    font-size: 15px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 10px;
    color: #fff;
    outline: none;
    transition: border-color 0.2s;
  }

  .input-group input:focus {
    border-color: #4f8ff7;
  }

  .input-group input::placeholder {
    color: #555;
  }

  .btn {
    padding: 14px 28px;
    font-size: 15px;
    font-weight: 600;
    background: #4f8ff7;
    color: #fff;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.2s, opacity 0.2s;
    white-space: nowrap;
  }

  .btn:hover { background: #3a7be0; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .status {
    text-align: center;
    padding: 20px;
    color: #888;
    font-size: 14px;
    display: none;
  }

  .status.active { display: block; }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #333;
    border-top-color: #4f8ff7;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 8px;
    vertical-align: middle;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .error {
    background: #2a1515;
    border: 1px solid #5a2020;
    color: #ff6b6b;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 24px;
    font-size: 14px;
    display: none;
  }

  .results { display: none; }

  .section {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 20px;
  }

  .section-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #4f8ff7;
    margin-bottom: 16px;
  }

  .section-content {
    font-size: 14px;
    color: #ccc;
    white-space: pre-wrap;
    line-height: 1.7;
  }

  .section-content h1, .section-content h2, .section-content h3 {
    color: #fff;
    margin-top: 16px;
    margin-bottom: 8px;
  }

  .section-content h1 { font-size: 20px; }
  .section-content h2 { font-size: 16px; }
  .section-content ul, .section-content ol { padding-left: 20px; margin: 8px 0; }
  .section-content li { margin-bottom: 4px; }

  .campaigns-grid {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .campaign-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 24px;
    transition: border-color 0.2s;
  }

  .campaign-card:hover { border-color: #444; }

  .campaign-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .badge {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 6px;
    white-space: nowrap;
  }

  .badge-blue { background: #1a2a4a; color: #4f8ff7; }
  .badge-green { background: #1a3a2a; color: #4fca7f; }
  .badge-orange { background: #3a2a1a; color: #f7a84f; }

  .campaign-name {
    font-size: 17px;
    font-weight: 600;
    color: #fff;
  }

  .campaign-field {
    margin-bottom: 14px;
  }

  .field-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #666;
    margin-bottom: 4px;
  }

  .field-value {
    font-size: 14px;
    color: #ccc;
    line-height: 1.6;
  }

  .email-box {
    background: #0f0f0f;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 18px;
    font-size: 14px;
    color: #ddd;
    line-height: 1.7;
    white-space: pre-wrap;
    position: relative;
  }

  .email-subject {
    font-weight: 600;
    color: #fff;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #222;
  }

  .copy-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    background: #222;
    color: #aaa;
    border: 1px solid #333;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .copy-btn:hover { background: #333; color: #fff; }
  .copy-btn.copied { background: #1a3a2a; color: #4fca7f; border-color: #2a5a3a; }

  .meta {
    text-align: center;
    color: #555;
    font-size: 13px;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #1a1a1a;
  }

  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 24px;
    background: #141414;
    padding: 4px;
    border-radius: 10px;
    border: 1px solid #222;
  }

  .tab {
    flex: 1;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #888;
    background: transparent;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }

  .tab:hover { color: #ccc; }
  .tab.active { background: #222; color: #fff; }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  .download-btn {
    display: inline-block;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    background: #1a1a1a;
    color: #4f8ff7;
    border: 1px solid #333;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    margin-top: 12px;
  }

  .download-btn:hover { background: #222; border-color: #4f8ff7; }

  @media (max-width: 640px) {
    .input-group { flex-direction: column; }
    .container { padding: 24px 16px; }
    .section { padding: 20px; }
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Research & Prospecting Tool</h1>
    <p>Paste a company URL. Get a full prospecting kit in 30 seconds.</p>
  </div>

  <div class="input-group">
    <input type="text" id="urlInput" placeholder="https://company.com" autocomplete="off" />
    <button class="btn" id="generateBtn" onclick="generate()">Generate</button>
  </div>

  <div class="error" id="errorBox"></div>

  <div class="status" id="statusBox">
    <span class="spinner"></span>
    <span id="statusText">Scraping website...</span>
  </div>

  <div class="results" id="results">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('campaigns')">Campaigns</button>
      <button class="tab" onclick="switchTab('brief')">Company Brief</button>
      <button class="tab" onclick="switchTab('analysis')">Raw Analysis</button>
    </div>

    <div class="tab-content active" id="tab-campaigns">
      <div class="campaigns-grid" id="campaignsGrid"></div>
    </div>

    <div class="tab-content" id="tab-brief">
      <div class="section">
        <div class="section-title">Company Brief</div>
        <div class="section-content" id="briefContent"></div>
      </div>
    </div>

    <div class="tab-content" id="tab-analysis">
      <div class="section">
        <div class="section-title">Company Analysis</div>
        <div class="section-content" id="analysisContent"></div>
      </div>
    </div>

    <div style="text-align: center; margin-top: 20px;">
      <button class="download-btn" onclick="downloadMarkdown()">Download as Markdown</button>
    </div>

    <div class="meta" id="metaInfo"></div>
  </div>
</div>

<script>
let currentData = null;

function wordCount(text) {
  if (!text) return 0;
  return text.trim().split(/\\s+/).filter(w => w.length > 0).length;
}

async function generate() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const btn = document.getElementById('generateBtn');
  const status = document.getElementById('statusBox');
  const errorBox = document.getElementById('errorBox');
  const results = document.getElementById('results');

  btn.disabled = true;
  btn.textContent = 'Working...';
  status.classList.add('active');
  errorBox.style.display = 'none';
  results.style.display = 'none';

  const steps = [
    'Scraping website...',
    'Extracting company intelligence...',
    'Generating campaign emails...',
    'Building prospecting brief...',
    'Assembling your kit...'
  ];

  let stepIdx = 0;
  const stepTimer = setInterval(() => {
    stepIdx = Math.min(stepIdx + 1, steps.length - 1);
    document.getElementById('statusText').textContent = steps[stepIdx];
  }, 8000);

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });

    clearInterval(stepTimer);

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Something went wrong');
    }

    const data = await resp.json();
    currentData = data;
    renderResults(data);
  } catch (e) {
    clearInterval(stepTimer);
    errorBox.textContent = e.message;
    errorBox.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate';
    status.classList.remove('active');
  }
}

function renderResults(data) {
  const results = document.getElementById('results');
  results.style.display = 'block';

  // Campaigns
  const grid = document.getElementById('campaignsGrid');
  grid.innerHTML = '';

  if (data.campaigns && data.campaigns.length > 0) {
    data.campaigns.forEach((c, i) => {
      const badgeClass = c.badge_color === 'green' ? 'badge-green' :
                         c.badge_color === 'orange' ? 'badge-orange' : 'badge-blue';
      grid.innerHTML += `
        <div class="campaign-card">
          <div class="campaign-header">
            <span class="badge ${badgeClass}">${c.type || 'Campaign ' + (i+1)}</span>
            <span class="campaign-name">${c.offer_name || ''}</span>
          </div>
          <div class="campaign-field">
            <div class="field-label">What You're Giving Away</div>
            <div class="field-value">${c.what_youre_giving || ''}</div>
          </div>
          <div class="campaign-field">
            <div class="field-label">Why It Converts</div>
            <div class="field-value">${c.why_it_converts || ''}</div>
          </div>
          <div class="campaign-field">
            <div class="field-label">Target ICP</div>
            <div class="field-value">${c.target_icp || ''}</div>
          </div>
          <div class="campaign-field">
            <div class="field-label">Apollo Search Query</div>
            <div class="field-value">${c.apollo_search || ''}</div>
          </div>
          <div class="campaign-field">
            <div class="field-label">LinkedIn Sales Nav Search</div>
            <div class="field-value">${c.linkedin_search || ''}</div>
          </div>
          <div class="campaign-field">
            <div class="field-label">Email</div>
            <div class="email-box">
              <button class="copy-btn" onclick="copyEmail(this, ${i})">Copy</button>
              <div class="email-subject">Subject: ${c.subject_line || ''} <span style="display:inline-block;margin-left:10px;font-size:12px;font-weight:600;color:${wordCount(c.email_body) >= 70 && wordCount(c.email_body) <= 90 ? '#4fca7f' : '#f7a84f'};background:${wordCount(c.email_body) >= 70 && wordCount(c.email_body) <= 90 ? '#1a3a2a' : '#3a2a1a'};padding:2px 8px;border-radius:4px;">${wordCount(c.email_body)} words</span></div>
              <div>${c.email_body || ''}</div>
              ${c.ps_line ? '<div style="margin-top:10px;color:#999;">PS: ' + c.ps_line + '</div>' : ''}
            </div>
          </div>
        </div>
      `;
    });
  }

  // Brief
  document.getElementById('briefContent').innerHTML = simpleMarkdown(data.brief || '');

  // Analysis
  document.getElementById('analysisContent').innerHTML = simpleMarkdown(data.company_analysis || '');

  // Meta
  const cached = data.from_cache ? ' (cached)' : '';
  document.getElementById('metaInfo').textContent =
    `Scraped ${data.pages_scraped} pages${cached} | ${(data.chars_scraped || 0).toLocaleString()} characters | Generated in ${data.duration_seconds}s`;
}

function simpleMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\\n/g, '<br>');
}

function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + tab).classList.add('active');
}

function copyEmail(btn, idx) {
  if (!currentData || !currentData.campaigns[idx]) return;
  const c = currentData.campaigns[idx];
  const text = 'Subject: ' + (c.subject_line || '') + '\\n\\n' + (c.email_body || '') +
    (c.ps_line ? '\\n\\nPS: ' + c.ps_line : '');
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

function downloadMarkdown() {
  if (!currentData) return;
  let md = '# ' + (currentData.domain || 'Company') + ' - Prospecting Kit\\n\\n';
  md += '## Company Analysis\\n\\n' + (currentData.company_analysis || '') + '\\n\\n';
  md += '## Company Brief\\n\\n' + (currentData.brief || '') + '\\n\\n';
  md += '## Campaigns\\n\\n';
  (currentData.campaigns || []).forEach((c, i) => {
    md += '### ' + (c.type || 'Campaign ' + (i+1)) + ': ' + (c.offer_name || '') + '\\n\\n';
    md += '**What You Give Away:** ' + (c.what_youre_giving || '') + '\\n\\n';
    md += '**Target ICP:** ' + (c.target_icp || '') + '\\n\\n';
    md += '**Apollo Search:** ' + (c.apollo_search || '') + '\\n\\n';
    md += '**LinkedIn Search:** ' + (c.linkedin_search || '') + '\\n\\n';
    md += '**Subject:** ' + (c.subject_line || '') + '\\n\\n';
    md += (c.email_body || '') + '\\n\\n';
    if (c.ps_line) md += 'PS: ' + c.ps_line + '\\n\\n';
    md += '---\\n\\n';
  });

  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (currentData.domain || 'company').replace(/\\./g, '_') + '_prospecting_kit.md';
  a.click();
}

// Enter key triggers generate
document.getElementById('urlInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') generate();
});
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

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    start = time.time()

    try:
        # Step 1: Scrape
        scraped = scrape_website(url)
        if not scraped:
            return jsonify({"error": f"Could not scrape {url}. The site may be blocking requests or the URL may be invalid."}), 400

        # Step 2: Run full pipeline
        result = run_full_pipeline(scraped)
        result["duration_seconds"] = round(time.time() - start, 1)

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
