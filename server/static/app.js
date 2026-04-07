/**
 * app.js – Hoved-applikasjonslogikk for Looking Glass
 * Ingen eksterne biblioteker – ren vanilla JS
 */

const API = '';  // Samme opprinnelse

let activeSource = 'local';
let sourcesData  = [];
let serversData  = [];
let selectedServer = null;

/* ─── Initialisering ─────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([loadSources(), loadServers()]);
  setupNavTabs();
  setupAiTab();
  updateCompareSource();
});

/* ─── Kilde-velger ───────────────────────────────── */
async function loadSources() {
  try {
    const res = await fetch(`${API}/api/sources`);
    const data = await res.json();
    sourcesData = data.sources;
    renderSourceTabs();
  } catch (e) {
    console.error('Klarte ikke hente kilder:', e);
  }
}

function renderSourceTabs() {
  const container = document.getElementById('sourceTabs');
  container.innerHTML = '';

  sourcesData.forEach(src => {
    const btn = document.createElement('button');
    btn.className = `source-tab${src.id === activeSource ? ' active' : ''}${!src.available ? ' disabled' : ''}`;
    btn.innerHTML = `${src.emoji} ${src.label}`;
    if (src.location) btn.title = src.location;

    if (src.available) {
      btn.addEventListener('click', () => {
        activeSource = src.id;
        document.querySelectorAll('.source-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        updateCompareSource();
        // Tilbakestill valgt server når kilde endres
        if (selectedServer) runTraceroute(selectedServer);
      });
    } else {
      btn.title = `${src.location} – ikke tilgjengelig`;
    }

    container.appendChild(btn);
  });
}

/* ─── Server-grid ────────────────────────────────── */
async function loadServers() {
  try {
    const res = await fetch(`${API}/api/servers`);
    const data = await res.json();
    serversData = data.categories;
    renderServerGrid();
  } catch (e) {
    document.getElementById('serverGrid').innerHTML =
      '<p style="color:var(--slow);padding:16px">Klarte ikke hente servere.</p>';
  }
}

function renderServerGrid() {
  const grid = document.getElementById('serverGrid');
  grid.innerHTML = '';

  serversData.forEach(cat => {
    const block = document.createElement('div');
    block.className = 'category-block';

    const header = document.createElement('div');
    header.className = 'category-header';
    header.innerHTML = `
      <span class="category-emoji">${cat.emoji}</span>
      <span class="category-title">${cat.label}</span>
      <span class="category-desc">${cat.description}</span>
    `;
    block.appendChild(header);

    const serverRow = document.createElement('div');
    serverRow.className = 'category-servers';

    cat.servers.forEach(srv => {
      const card = document.createElement('div');
      card.className = 'server-card';
      card.dataset.id = srv.id;
      card.innerHTML = `
        <div class="server-card-top">
          <span class="server-emoji">${srv.emoji}</span>
          <span class="server-name">${srv.label}</span>
        </div>
        <div class="server-location">${srv.flag} ${srv.location}</div>
      `;
      card.addEventListener('click', () => selectServer(srv));
      serverRow.appendChild(card);
    });

    block.appendChild(serverRow);
    grid.appendChild(block);
  });
}

function selectServer(srv) {
  selectedServer = srv;

  // Marker valgt kort
  document.querySelectorAll('.server-card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector(`.server-card[data-id="${srv.id}"]`);
  if (card) card.classList.add('selected');

  runTraceroute(srv);
}

/* ─── Traceroute ─────────────────────────────────── */
async function runTraceroute(srv) {
  const panel = document.getElementById('traceroutePanel');
  const grid  = document.getElementById('serverGrid');

  // Vis traceroute-panel, skjul grid
  grid.style.display = 'none';
  panel.style.display = 'block';

  const infoEl = document.getElementById('trTargetInfo');
  infoEl.innerHTML = `${srv.emoji} ${srv.label} <span style="color:var(--text-muted);font-size:14px">${srv.flag} ${srv.location}</span>`;

  document.getElementById('reportCardSection').style.display = 'none';
  document.getElementById('reportCard').style.display = 'none';

  // Ber lookingglass.js om å kjøre
  if (window.LookingGlass) {
    await window.LookingGlass.run(srv.id, activeSource);
    document.getElementById('reportCardSection').style.display = 'block';
  }
}

document.getElementById('btnNewTrace').addEventListener('click', () => {
  document.getElementById('traceroutePanel').style.display = 'none';
  document.getElementById('serverGrid').style.display = 'block';
  document.querySelectorAll('.server-card').forEach(c => c.classList.remove('selected'));
  selectedServer = null;
});

/* ─── Rapport-kort ───────────────────────────────── */
document.getElementById('btnGenerateReport').addEventListener('click', () => {
  if (!window.LookingGlass || !window.LookingGlass.lastResult) return;
  const report = generateReportCard(window.LookingGlass.lastResult);
  const el = document.getElementById('reportCard');
  el.textContent = report;
  el.style.display = 'block';
  el.scrollIntoView({ behavior: 'smooth' });
});

function generateReportCard(result) {
  const now = new Date().toLocaleString('no-NO');
  const src = sourcesData.find(s => s.id === result.source);
  const srcLabel = src ? src.label : result.source;

  let lines = [
    '╔══════════════════════════════════════════════╗',
    '║  🔭 LOOKING GLASS – NETT-REISE RAPPORT       ║',
    '╚══════════════════════════════════════════════╝',
    '',
    `📅 Tidspunkt : ${now}`,
    `📡 Kilde     : ${srcLabel}`,
    `🎯 Mål       : ${result.target}`,
    `⏱️  Total tid  : ${result.total_ms} ms`,
    '',
    '─── HOPP ──────────────────────────────────────',
  ];

  result.hops.forEach(hop => {
    const status = hop.status === 'good' ? '🟢' : hop.status === 'warn' ? '🟡' : '🔴';
    lines.push(`  ${String(hop.hop).padStart(2, '0')}. ${status} ${hop.ms.toFixed(1).padStart(6)} ms  ${hop.flag} ${hop.label}`);
  });

  lines.push('');
  lines.push('─── OM SYSTEMET ──────────────────────────────');
  lines.push('  Generert av Looking Glass for vanlig folk');
  lines.push('  Mock-data – kun for demonstrasjon');
  lines.push('══════════════════════════════════════════════');

  return lines.join('\n');
}

/* ─── Tab-navigasjon ────────────────────────────── */
function setupNavTabs() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tabId}`).classList.add('active');
    });
  });
}

/* ─── Sammenlign-tab ─────────────────────────────── */
function updateCompareSource() {
  const src = sourcesData.find(s => s.id === activeSource);
  document.getElementById('compareSource').textContent = src ? `${src.emoji} ${src.label}` : activeSource;
}

document.getElementById('btnRunAll').addEventListener('click', runCompareAll);

async function runCompareAll() {
  const allIds = serversData.flatMap(cat => cat.servers.map(s => s.id));
  const targets = allIds.join(',');

  document.getElementById('compareResults').style.display = 'none';
  document.getElementById('compareLoading').style.display = 'block';

  try {
    const res = await fetch(`${API}/api/ping/multi?targets=${encodeURIComponent(targets)}&source=${activeSource}`);
    const data = await res.json();

    document.getElementById('compareLoading').style.display = 'none';
    renderCompareResults(data);
  } catch (e) {
    document.getElementById('compareLoading').innerHTML =
      '<p style="color:var(--slow)">Feil ved henting av data.</p>';
  }
}

function scoreClass(s) {
  if (s >= 85) return 'great';
  if (s >= 70) return 'good';
  if (s >= 50) return 'ok';
  return 'bad';
}

function renderCompareResults(data) {
  const sum = data.summary;

  // Score-kort
  const scoreCards = document.getElementById('scoreCards');
  scoreCards.innerHTML = `
    <div class="score-card">
      <div class="score-card-label">🎮 Gaming</div>
      <div class="score-card-value score-${scoreClass(sum.gaming_score)}">${sum.gaming_score}</div>
      <div class="score-card-sub">/ 100</div>
    </div>
    <div class="score-card">
      <div class="score-card-label">📺 Streaming</div>
      <div class="score-card-value score-${scoreClass(sum.streaming_score)}">${sum.streaming_score}</div>
      <div class="score-card-sub">/ 100</div>
    </div>
    <div class="score-card">
      <div class="score-card-label">💼 Jobb</div>
      <div class="score-card-value score-${scoreClass(sum.work_score)}">${sum.work_score}</div>
      <div class="score-card-sub">/ 100</div>
    </div>
    <div class="score-card">
      <div class="score-card-label">⭐ Totalt</div>
      <div class="score-card-value score-${scoreClass(sum.overall_score)}">${sum.overall_score}</div>
      <div class="score-card-sub">/ 100</div>
    </div>
  `;

  // Bygg oppslagstabeller for server-metadata
  const serverMap = {};
  serversData.forEach(cat => cat.servers.forEach(s => { serverMap[s.id] = s; }));

  const tbody = document.getElementById('resultsBody');
  tbody.innerHTML = '';

  data.results.forEach(r => {
    const srv = serverMap[r.server_id] || { label: r.server_id, emoji: '🔵', flag: '' };
    const msClass = r.status === 'good' ? 'good' : r.status === 'warn' ? 'warn' : r.status === 'bad' ? 'slow' : 'ok';
    const sc = scoreClass(r.score);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="result-server-cell">
          <span>${srv.emoji}</span>
          <span>${srv.label}</span>
          <span style="font-size:11px;color:var(--text-muted)">${srv.flag}</span>
        </div>
      </td>
      <td><span class="result-ms ${msClass}">${r.ms} ms</span></td>
      <td><span class="result-ms ok">${r.jitter_ms} ms</span></td>
      <td><span class="result-ms ${r.packet_loss_pct > 0 ? 'warn' : 'good'}">${r.packet_loss_pct}%</span></td>
      <td><div class="score-pill ${sc}">${r.score}</div></td>
      <td><span class="status-badge ${msClass}">${r.verdict}</span></td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('compareResults').style.display = 'block';
}

/* ─── AI-tab ─────────────────────────────────────── */
function setupAiTab() {
  document.querySelectorAll('.use-case-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.use-case-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  document.getElementById('btnAiRun').addEventListener('click', runAi);
}

async function runAi() {
  const useCase = document.querySelector('.use-case-btn.active')?.dataset.case || 'gaming';
  const srcA = document.getElementById('aiSourceA').value;
  const srcB = document.getElementById('aiSourceB').value;

  const btn = document.getElementById('btnAiRun');
  btn.textContent = '⏳ Analyserer…';
  btn.disabled = true;

  try {
    const res = await fetch(`${API}/api/recommend?use_case=${useCase}&source_a=${srcA}&source_b=${srcB}`);
    const data = await res.json();
    renderAiResult(data);
  } catch (e) {
    document.getElementById('aiResult').innerHTML =
      '<p style="color:var(--slow)">Feil ved AI-analyse.</p>';
    document.getElementById('aiResult').style.display = 'block';
  } finally {
    btn.textContent = '🧠 Analyser';
    btn.disabled = false;
  }
}

function renderAiResult(data) {
  const src = sourcesData.find(s => s.id === data.best_source);
  const emoji = src ? src.emoji : '🔵';
  const confPct = Math.round(data.confidence * 100);
  const mi = data.model_info;

  const html = `
    <div class="ai-winner-card">
      <div class="ai-winner-top">
        <span class="ai-winner-icon">${emoji}</span>
        <div>
          <div class="ai-winner-label">✅ Anbefalt kilde</div>
          <div class="ai-winner-name">${data.best_source_label}</div>
        </div>
        <div class="ai-winner-ping">
          <div class="ai-winner-ping-val">${data.predicted_ping_ms}</div>
          <div class="ai-winner-ping-unit">ms estimert</div>
        </div>
      </div>
      <div class="ai-confidence-bar">
        <span style="font-size:12px;color:var(--text-muted)">Konfidens</span>
        <div class="ai-confidence-track">
          <div class="ai-confidence-fill" style="width:${confPct}%"></div>
        </div>
        <span class="ai-confidence-label">${confPct}%</span>
      </div>
    </div>

    <div class="ai-reason-card">
      <strong>🧠 ${data.reason}</strong>
      ${data.reason_long}
    </div>

    ${data.alternatives.length ? `
    <h4 style="margin-bottom:10px;color:var(--text-secondary);font-size:13px;text-transform:uppercase;letter-spacing:0.5px">Alternativer</h4>
    <div class="ai-alternatives">
      ${data.alternatives.map(alt => `
        <div class="ai-alt-card">
          <div class="ai-alt-label">Alternativ</div>
          <div class="ai-alt-name">${alt.label}</div>
          <div class="ai-alt-ping">${alt.predicted_ping_ms} ms</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${alt.reason}</div>
        </div>
      `).join('')}
    </div>
    ` : ''}

    <div class="ai-model-info">
      <span>🤖 Algoritme: ${mi.algorithm}</span>
      <span>📊 Treningsdata: ${mi.training_samples.toLocaleString()} målinger</span>
      <span>📅 Sist trent: ${mi.last_trained.split('T')[0]}</span>
      <span>🔧 Features: ${mi.features_used.length}</span>
    </div>
  `;

  const el = document.getElementById('aiResult');
  el.innerHTML = html;
  el.style.display = 'block';
}

/* ─── Modal ──────────────────────────────────────── */
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalOverlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeModal();
});

function openModal(content) {
  document.getElementById('modalContent').innerHTML = content;
  document.getElementById('modalOverlay').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').style.display = 'none';
  document.body.style.overflow = '';
}

// Eksporter til global scope for lookingglass.js
window.AppModal = { open: openModal, close: closeModal };
