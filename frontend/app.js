/* ═══════════════════════════════════════════════
   APP.JS — Question → Cards → AI interpretation
   ═══════════════════════════════════════════════ */

const SPREAD_NAMES = {
  '1_carte':             'Single Card',
  'oui_non':             'Yes / No',
  'passe_present_futur': 'Past · Present · Future',
  'croix_celtique':      'Celtic Cross',
};

const CARD_ICONS = [
  '☽','★','☿','♀','♂','♃','♄','☉','⊕','⚖',
  '☽','⌛','☠','⚗','☯','⚡','★','☽','☀','🔔','🌍','✦'
];

const PREMIUM_SPREADS = new Set(['oui_non', 'passe_present_futur', 'croix_celtique']);

let currentSpread   = '1_carte';
let lastTirageData  = null;
let currentQuestion = '';

// ── STARS ─────────────────────────────────────────
function initStars() {
  const container = document.getElementById('stars');
  for (let i = 0; i < 120; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const size = Math.random() * 2 + 0.5;
    s.style.cssText = `width:${size}px;height:${size}px;top:${Math.random()*100}%;left:${Math.random()*100}%;--op:${(Math.random()*0.6+0.1).toFixed(2)};--dur:${(Math.random()*3+2).toFixed(1)}s`;
    container.appendChild(s);
  }
}

// ── VIEWS ──────────────────────────────────────────
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById(`view-${name}`);
  if (target) { target.classList.add('active'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  // Show stars everywhere except home (home has room background)
  const stars = document.getElementById('stars');
  if (stars) stars.style.display = name === 'home' ? 'none' : '';
  if (name === 'history') loadHistory();
}

// ── SPREAD SELECTOR ────────────────────────────────
function selectSpread(btn) {
  const type = btn.dataset.spread;
  if (PREMIUM_SPREADS.has(type) && (!currentUser || !currentUser.is_premium)) {
    showView('premium');
    return;
  }
  document.querySelectorAll('.spread-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentSpread = type;
}

// ── CHAR COUNT ─────────────────────────────────────
function updateCharCount(el) {
  document.getElementById('char-count').textContent = `${el.value.length} / 300`;
}

// ── ASK QUESTION ───────────────────────────────────
async function askQuestion() {
  const question = document.getElementById('question-input').value.trim();

  if (!question) {
    document.getElementById('question-input').focus();
    showToast('Please enter your question first.', 'error');
    return;
  }

  if (PREMIUM_SPREADS.has(currentSpread) && (!currentUser || !currentUser.is_premium)) {
    showView('premium');
    return;
  }

  currentQuestion = question;

  // Switch to reading view
  showView('reading');

  // Show question recap
  const recap = document.getElementById('reading-question');
  recap.innerHTML = `<span>${SPREAD_NAMES[currentSpread]}</span>"${question}"`;

  // Reset
  document.getElementById('cards-area').innerHTML = '<div class="loading-spinner"></div>';
  document.getElementById('interpretation-box').style.display = 'none';
  document.getElementById('reading-actions').style.display = 'none';

  try {
    const res = await fetch(`${API}/tirages/`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ type: currentSpread, question: currentQuestion }),
    });

    if (res.status === 429) {
      document.getElementById('cards-area').innerHTML = `
        <div class="empty-state">
          <p>You've used all your free readings for today.<br/>Come back tomorrow or upgrade to Premium.</p>
          <button class="btn-primary" onclick="showView('premium')">✦ Get Premium</button>
        </div>`;
      return;
    }
    if (res.status === 403) { showView('premium'); return; }
    if (!res.ok) throw new Error('Server error');

    const data = await res.json();
    lastTirageData = data;

    renderAndAutoFlip(data.cartes);
    fetchQuota();

  } catch {
    document.getElementById('cards-area').innerHTML =
      `<div class="empty-state"><p>Something went wrong. Please try again.</p></div>`;
  }
}

// ── RENDER + AUTO FLIP ─────────────────────────────
function renderAndAutoFlip(cartes) {
  const area = document.getElementById('cards-area');
  area.innerHTML = '';

  // Add magic circle behind cards
  const circle = document.createElement('div');
  circle.className = 'magic-circle';
  area.appendChild(circle);

  cartes.forEach((card, i) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'tarot-card-wrapper';

    if (cartes.length > 1) {
      const label = document.createElement('div');
      label.className = 'card-position-label';
      label.textContent = card.position;
      wrapper.appendChild(label);
    }

    const cardEl = document.createElement('div');
    cardEl.className = 'tarot-card';
    cardEl.id = `card-${i}`;
    cardEl.innerHTML = `
      <div class="tarot-card-inner">
        <div class="card-face card-back">
          <div class="card-back-symbol">✦</div>
        </div>
        <div class="card-face card-front" onclick="openCardDetail(${i})">
          <div class="card-front-number">${card.nom.split(' ').length > 2 ? card.id : card.id}</div>
          <div class="card-front-icon">${CARD_ICONS[card.id] || '✦'}</div>
          <div class="card-front-name">${card.nom}</div>
          ${card.inversee ? '<div class="card-reversed-label">↻ Reversed</div>' : ''}
          <div class="card-front-hint">tap for details</div>
        </div>
      </div>`;

    wrapper.appendChild(cardEl);
    area.appendChild(wrapper);

    // Auto flip with staggered delay + particles
    setTimeout(() => {
      cardEl.classList.add(card.inversee ? 'reversed' : 'flipped');
      spawnParticles(cardEl);
      if (i === cartes.length - 1) {
        setTimeout(() => startInterpretation(), 800);
      }
    }, 500 + i * 400);
  });
}

// ── CARD DETAIL MODAL ─────────────────────────────
function openCardDetail(index) {
  if (!lastTirageData) return;
  const card = lastTirageData.cartes[index];
  const interp = card.inversee ? card.interpretation_statique : card.interpretation_statique;

  let modal = document.getElementById('card-detail-overlay');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'card-detail-overlay';
    modal.className = 'card-detail-overlay';
    modal.onclick = (e) => { if (e.target === modal) closeCardDetail(); };
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="card-detail">
      <button class="card-detail-close" onclick="closeCardDetail()">✕</button>
      <div class="card-detail-number">Arcana ${card.id}</div>
      <span class="card-detail-icon">${CARD_ICONS[card.id] || '✦'}</span>
      <div class="card-detail-name">${card.nom}</div>
      ${card.inversee ? '<div class="card-detail-reversed">↻ Reversed</div>' : ''}
      <div class="card-detail-keywords">
        ${(card.keywords || []).map(k => `<span class="keyword-pill">${k}</span>`).join('')}
      </div>
      <div class="card-detail-divider"></div>
      <div class="card-detail-interp">${card.interpretation_statique}</div>
    </div>`;

  modal.classList.add('open');
}

function closeCardDetail() {
  const modal = document.getElementById('card-detail-overlay');
  if (modal) modal.classList.remove('open');
}

// ── PARTICLES ─────────────────────────────────────
function spawnParticles(cardEl) {
  const rect = cardEl.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const symbols = ['✦', '✧', '⋆', '·', '✺', '✵', '☽'];

  for (let i = 0; i < 10; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.textContent = symbols[Math.floor(Math.random() * symbols.length)];
    p.style.left = (cx + (Math.random() - 0.5) * 80) + 'px';
    p.style.top  = (cy + (Math.random() - 0.5) * 60) + 'px';
    p.style.animationDelay = (Math.random() * 0.4) + 's';
    p.style.fontSize = (Math.random() * 0.8 + 0.5) + 'rem';
    document.body.appendChild(p);
    setTimeout(() => p.remove(), 2200);
  }
}

// ── STREAMING INTERPRETATION ───────────────────────
async function startInterpretation() {
  const box     = document.getElementById('interpretation-box');
  const textEl  = document.getElementById('interp-text');
  const cursor  = document.getElementById('interp-cursor');
  const actions = document.getElementById('reading-actions');

  box.style.display = '';
  textEl.textContent = '';
  cursor.style.display = 'inline-block';
  box.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const res = await fetch(`${API}/tirages/stream/interpret`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        type:      currentSpread,
        cartes:    lastTirageData.cartes,
        question:  currentQuestion,
        tirage_id: lastTirageData.id,
      }),
    });

    if (!res.ok) throw new Error('Stream error');

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        try {
          const json = JSON.parse(line.slice(5).trim());
          if (json.token) textEl.textContent += json.token;
          if (json.done || json.error) {
            cursor.style.display = 'none';
            actions.style.display = '';
          }
        } catch {}
      }
    }
    cursor.style.display = 'none';
    actions.style.display = '';

  } catch {
    textEl.textContent = 'Unable to generate interpretation. Please try again.';
    cursor.style.display = 'none';
    actions.style.display = '';
  }
}

// ── HISTORY ───────────────────────────────────────
let historyCache = [];

async function loadHistory() {
  const list = document.getElementById('history-list');
  list.innerHTML = '<div class="loading-spinner"></div>';
  if (!currentUser) {
    list.innerHTML = `<div class="empty-state"><p>Sign in to see your reading history.</p><button class="btn-primary" onclick="openModal('auth')">Sign in</button></div>`;
    return;
  }
  try {
    const res = await fetch(`${API}/tirages/historique`, { headers: authHeaders() });
    const data = await res.json();
    historyCache = data;
    if (!data.length) {
      list.innerHTML = `<div class="empty-state"><p>No readings yet.</p><button class="btn-primary" onclick="showView('home')">Ask a question</button></div>`;
      return;
    }
    const retentionNote = currentUser.is_premium
      ? '<div class="history-note">Readings are kept for 30 days.</div>'
      : '<div class="history-note">Readings are kept for 7 days. Upgrade to Premium for 30 days.</div>';

    list.innerHTML = retentionNote + data.map((t, idx) => {
      const date  = new Date(t.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const question = t.question || '';
      const names = t.cartes.map(c => c.nom).join(' · ');
      const expIn = t.expires_at ? Math.max(0, Math.ceil((new Date(t.expires_at) - new Date()) / 86400000)) : null;
      const expBadge = expIn !== null ? `<span class="history-item-exp">expires in ${expIn}d</span>` : '';
      const preview = t.interpretation
        ? t.interpretation.slice(0, 180) + (t.interpretation.length > 180 ? '…' : '')
        : '<em>No interpretation saved</em>';
      return `<div class="history-item" onclick="openHistoryDetail(${idx})">
        <div class="history-item-header">
          <span class="history-item-type">${SPREAD_NAMES[t.type] || t.type}</span>
          <span class="history-item-date">${date}${expBadge}</span>
        </div>
        ${question ? `<div class="history-item-question">"${question}"</div>` : ''}
        <div class="history-item-cards">${names}</div>
        <div class="history-item-preview">${preview}</div>
        <div class="history-item-cta">Tap to read full interpretation →</div>
      </div>`;
    }).join('');
  } catch {
    list.innerHTML = `<div class="empty-state"><p>Unable to load history.</p></div>`;
  }
}

function openHistoryDetail(index) {
  const t = historyCache[index];
  if (!t) return;
  const date = new Date(t.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  let modal = document.getElementById('history-detail-overlay');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'history-detail-overlay';
    modal.className = 'card-detail-overlay';
    modal.onclick = (e) => { if (e.target === modal) closeHistoryDetail(); };
    document.body.appendChild(modal);
  }

  const cardsHtml = t.cartes.map(c => `
    <div class="history-card-line">
      <span class="history-card-icon">${CARD_ICONS[c.id] || '✦'}</span>
      <div class="history-card-info">
        <strong>${c.nom}</strong>${c.inversee ? ' <em>(reversed)</em>' : ''}
        ${c.position ? `<span class="history-card-pos">— ${c.position}</span>` : ''}
      </div>
    </div>`).join('');

  modal.innerHTML = `
    <div class="card-detail history-detail">
      <button class="card-detail-close" onclick="closeHistoryDetail()">✕</button>
      <div class="history-detail-type">${SPREAD_NAMES[t.type] || t.type}</div>
      <div class="history-detail-date">${date}</div>
      ${t.question ? `<div class="history-detail-question">"${t.question}"</div>` : ''}
      <div class="card-detail-divider"></div>
      <div class="history-detail-cards">${cardsHtml}</div>
      <div class="card-detail-divider"></div>
      <div class="history-detail-interp">${t.interpretation ? t.interpretation.replace(/\n/g, '<br>') : '<em>No interpretation was saved for this reading.</em>'}</div>
    </div>`;

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeHistoryDetail() {
  const modal = document.getElementById('history-detail-overlay');
  if (modal) modal.classList.remove('active');
  document.body.style.overflow = '';
}

// ── INIT ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initStars();
  // Home uses room background — hide stars initially
  document.getElementById('stars').style.display = 'none';
  initAuth();

  // Allow Enter (Shift+Enter = newline) to submit
  document.getElementById('question-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  });
});
