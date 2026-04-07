/**
 * lookingglass.js – Traceroute-visualisering
 *
 * Animerer hopp-for-hopp visning av traceroute-resultater.
 * Klikk på et hopp for detaljer i modal.
 */

const LookingGlass = (() => {
  const API = '';
  let lastResult = null;

  /**
   * Kjør traceroute mot server og animer hoppene.
   */
  async function run(serverId, source) {
    const container = document.getElementById('tracerouteContainer');
    container.innerHTML = buildProgressBar() + '<div class="hop-list" id="hopList"></div>';

    try {
      const res = await fetch(`${API}/api/traceroute?target=${encodeURIComponent(serverId)}&source=${encodeURIComponent(source)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      lastResult = data;

      if (data.error) {
        container.innerHTML = `<p style="color:var(--slow);padding:16px">⚠️ ${data.error}</p>`;
        return;
      }

      await animateHops(data.hops, data);
    } catch (e) {
      container.innerHTML = `<p style="color:var(--slow);padding:16px">❌ Feil: ${e.message}</p>`;
    }
  }

  function buildProgressBar() {
    return `
      <div class="trace-progress" id="traceProgress">
        <div class="trace-progress-bar" id="traceProgressBar" style="width:0%"></div>
      </div>
    `;
  }

  async function animateHops(hops, data) {
    const hopList = document.getElementById('hopList');
    hopList.innerHTML = '';

    for (let i = 0; i < hops.length; i++) {
      const hop = hops[i];
      const el  = buildHopElement(hop, i + 1);
      hopList.appendChild(el);

      // Oppdater progress bar
      const pct = Math.round(((i + 1) / hops.length) * 100);
      const bar = document.getElementById('traceProgressBar');
      if (bar) bar.style.width = `${pct}%`;

      // Trigger animasjon etter litt delay
      await sleep(30);
      el.classList.add('visible');
      await sleep(280);
    }

    // Fullfør progress bar
    const bar = document.getElementById('traceProgressBar');
    if (bar) {
      bar.style.width = '100%';
      bar.style.background = 'linear-gradient(90deg, var(--good), #00e5ff)';
    }

    // Legg til oppsummering
    hopList.appendChild(buildSummary(data));
  }

  function buildHopElement(hop, hopNum) {
    const item = document.createElement('div');
    item.className = 'hop-item';

    const statusClass = hop.status === 'good' ? 'status-good' : hop.status === 'warn' ? 'status-warn' : 'status-slow';
    const msLabel     = `${hop.ms.toFixed(1)}<span class="hop-ms-unit"> ms</span>`;

    item.innerHTML = `
      <div class="hop-connector"></div>
      <div class="hop-number-col">
        <div class="hop-num-badge ${statusClass}">${hopNum}</div>
      </div>
      <div class="hop-card" data-hop-index="${hopNum - 1}">
        <div class="hop-card-main">
          <span class="hop-emoji">${hop.emoji}</span>
          <div class="hop-info">
            <div class="hop-label">${hop.label}</div>
            <div class="hop-location">${hop.flag} ${hop.city}, ${hop.country}</div>
          </div>
          <div class="hop-ms ${statusClass}">${msLabel}</div>
        </div>
        <div class="hop-desc">${hop.description}</div>
      </div>
    `;

    // Klikk → åpne detalj-modal
    item.querySelector('.hop-card').addEventListener('click', () => openHopModal(hop));

    return item;
  }

  function buildSummary(data) {
    const el = document.createElement('div');
    el.style.cssText = 'padding:16px 0 4px 56px;animation:fadeIn 0.4s ease;';
    el.innerHTML = `
      <div style="background:var(--good-bg);border:1px solid var(--good);border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span style="font-size:24px">✅</span>
        <div>
          <div style="font-weight:700;color:var(--good)">Nett-reise fullført!</div>
          <div style="font-size:13px;color:var(--text-secondary)">${data.hops.length} hopp &mdash; Total tid: ${data.total_ms.toFixed(1)} ms</div>
        </div>
      </div>
    `;
    return el;
  }

  function openHopModal(hop) {
    if (!window.AppModal) return;

    const statusClass = hop.status === 'good' ? 'status-good' : hop.status === 'warn' ? 'status-warn' : 'status-slow';
    const statusLabel = hop.status === 'good' ? '✅ Bra' : hop.status === 'warn' ? '⚠️ OK' : '🔴 Tregt';

    const content = `
      <div class="modal-hop-icon">${hop.emoji}</div>
      <div class="modal-hop-name">${hop.label}</div>
      <div class="modal-hop-location">${hop.flag} ${hop.city}, ${hop.country} &mdash; ${statusLabel}</div>
      <div class="modal-hop-ms ${statusClass}">${hop.ms.toFixed(1)} ms</div>
      <div class="modal-desc">${hop.long_description}</div>
      <div class="modal-funfact">${hop.fun_fact}</div>
      <div class="modal-ip">🖥️ IP: ${hop.ip} &nbsp;|&nbsp; Hostname: ${hop.hostname}</div>
    `;

    window.AppModal.open(content);
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  return { run, get lastResult() { return lastResult; } };
})();

window.LookingGlass = LookingGlass;
