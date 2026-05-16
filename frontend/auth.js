/* ═══════════════════════════════════════════════
   AUTH.JS — Login, Register, Session management
   ═══════════════════════════════════════════════ */

// API base URL — set window.API_BASE_URL before loading this script to override
const API = window.API_BASE_URL || 'http://localhost:8000';

let currentUser = null;

// ── TOKEN ─────────────────────────────────────────
function getToken() { return localStorage.getItem('arcana_token'); }
function setToken(t) { localStorage.setItem('arcana_token', t); }
function clearToken() { localStorage.removeItem('arcana_token'); }

function authHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' }
           : { 'Content-Type': 'application/json' };
}

// ── INIT ──────────────────────────────────────────
async function initAuth() {
  const token = getToken();
  if (!token) return updateUI(null);
  try {
    const res = await fetch(`${API}/auth/me`, { headers: authHeaders() });
    if (res.ok) {
      currentUser = await res.json();
      updateUI(currentUser);
    } else {
      clearToken();
      updateUI(null);
    }
  } catch {
    updateUI(null);
  }
}

// ── UPDATE UI ─────────────────────────────────────
function updateUI(user) {
  // Side menu sections
  const sectionLoggedOut = document.getElementById('side-menu-loggedout');
  const sectionLoggedIn  = document.getElementById('side-menu-loggedin');
  const sectionLogout    = document.getElementById('side-menu-logout');
  const itemHistory      = document.getElementById('side-menu-history');
  const itemSub          = document.getElementById('side-menu-subscription');
  const avatar           = document.getElementById('side-menu-avatar');
  const nameEl           = document.getElementById('side-menu-user-name');
  const statusEl         = document.getElementById('side-menu-user-status');

  if (user) {
    if (sectionLoggedOut) sectionLoggedOut.style.display = 'none';
    if (sectionLoggedIn)  sectionLoggedIn.style.display  = '';
    if (sectionLogout)    sectionLogout.style.display    = '';
    if (itemHistory)      itemHistory.style.display      = 'flex';
    if (itemSub)          itemSub.style.display          = user.is_premium ? 'flex' : 'none';
    if (avatar)           avatar.textContent             = (user.prenom || '?').charAt(0).toUpperCase();
    if (nameEl)           nameEl.textContent             = user.prenom;
    if (statusEl) {
      statusEl.textContent = user.is_premium ? '✦ Premium member' : 'Free account';
      statusEl.className   = 'side-menu-user-status' + (user.is_premium ? ' premium' : '');
    }
    updateSpreadAccess(user.is_premium);
  } else {
    if (sectionLoggedOut) sectionLoggedOut.style.display = '';
    if (sectionLoggedIn)  sectionLoggedIn.style.display  = 'none';
    if (sectionLogout)    sectionLogout.style.display    = 'none';
    if (itemHistory)      itemHistory.style.display      = 'none';
    if (itemSub)          itemSub.style.display          = 'none';
    updateSpreadAccess(false);
  }
  fetchQuota();
}

// Side menu toggle
function toggleSideMenu() {
  const menu = document.getElementById('side-menu');
  const backdrop = document.getElementById('side-menu-backdrop');
  if (!menu) return;
  const isOpen = menu.classList.toggle('open');
  if (backdrop) backdrop.classList.toggle('open', isOpen);
  document.body.style.overflow = isOpen ? 'hidden' : '';
}

// Close menu on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const menu = document.getElementById('side-menu');
    if (menu && menu.classList.contains('open')) toggleSideMenu();
  }
});

function updateSpreadAccess(isPremium) {
  document.querySelectorAll('.spread-card.premium-lock').forEach(el => {
    if (isPremium) {
      el.classList.remove('premium-lock');
      el.querySelector('.spread-tag').className = 'spread-tag free-tag';
      el.querySelector('.spread-tag').textContent = 'Premium';
    }
  });
}

// ── QUOTA ─────────────────────────────────────────
async function fetchQuota() {
  try {
    const res = await fetch(`${API}/tirages/quota`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('quota-badge');
    if (data.is_premium) {
      badge.textContent = '∞ readings';
      badge.style.display = '';
    } else if (data.quota_restant !== null) {
      badge.innerHTML = `${data.quota_restant}/${data.quota_total}<span class="quota-suffix"> free today</span>`;
      badge.style.display = data.quota_restant > 0 ? '' : 'none';
    }
  } catch {}
}

// ── MODAL ─────────────────────────────────────────
function openModal(name) {
  document.getElementById(`modal-${name}`).classList.add('open');
}
function closeModal(name) {
  document.getElementById(`modal-${name}`).classList.remove('open');
  document.getElementById('login-error').textContent = '';
  document.getElementById('reg-error').textContent = '';
}
function closeModalOnOverlay(e) {
  if (e.target === e.currentTarget) closeModal('auth');
}

function switchTab(tab) {
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
  document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('form-register').classList.toggle('hidden', tab !== 'register');
}

// ── LOGIN ─────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const email    = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const errEl    = document.getElementById('login-error');
  errEl.textContent = '';

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || 'Login failed'; return; }
    setToken(data.access_token);
    currentUser = data.user;
    updateUI(data.user);
    closeModal('auth');
    showToast(`Welcome back, ${data.user.prenom}!`, 'success');
  } catch {
    errEl.textContent = 'Connection error. Please try again.';
  }
}

// ── REGISTER ──────────────────────────────────────
async function handleRegister(e) {
  e.preventDefault();
  const prenom   = document.getElementById('reg-prenom').value;
  const email    = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const errEl    = document.getElementById('reg-error');
  errEl.textContent = '';

  try {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prenom, email, password }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || 'Registration failed'; return; }
    setToken(data.access_token);
    currentUser = data.user;
    updateUI(data.user);
    closeModal('auth');
    showToast(`Welcome, ${data.user.prenom}! ✦`, 'success');
  } catch {
    errEl.textContent = 'Connection error. Please try again.';
  }
}

// ── LOGOUT ────────────────────────────────────────
function logout() {
  clearToken();
  currentUser = null;
  updateUI(null);
  showView('home');
  showToast('Signed out.', 'success');
}

// Legacy compatibility (old user-menu was replaced by side menu)
function toggleUserMenu() { /* no-op — kept for old onclick refs */ }
document.addEventListener('click', (e) => {
  // Legacy listener — old user-menu DOM removed, kept guard against null
  const menu = document.getElementById('user-menu');
  if (menu && !menu.contains(e.target)) menu.style.display = 'none';
});

// ── STRIPE ────────────────────────────────────────
async function subscribePremium() {
  if (!currentUser) { openModal('auth'); return; }
  try {
    const res = await fetch(`${API}/stripe/checkout`, {
      method: 'POST',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (data.checkout_url) window.location.href = data.checkout_url;
  } catch {
    showToast('Unable to start checkout. Please try again.', 'error');
  }
}

async function manageSubscription() {
  // Hide user menu if open
  const menu = document.getElementById('user-menu');
  if (menu) menu.style.display = 'none';

  // Not logged in → invite to sign in
  if (!currentUser) {
    showToast('Please sign in first.', 'error');
    openModal('auth');
    return;
  }

  // Logged in but no active subscription → go to Premium page to subscribe
  if (!currentUser.is_premium) {
    showToast('You have no active subscription. Subscribe to Premium first.', 'error');
    showView('premium');
    return;
  }

  // Has subscription → open Stripe Customer Portal
  try {
    const res = await fetch(`${API}/stripe/portal`, {
      method: 'POST',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (data.portal_url) {
      window.location.href = data.portal_url;
    } else {
      showToast(data.detail || 'Unable to open subscription portal.', 'error');
    }
  } catch {
    showToast('Unable to open subscription portal.', 'error');
  }
}

// ── TOAST ─────────────────────────────────────────
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 3000);
}
