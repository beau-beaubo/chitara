/* ═══════════════════════════════════════════════════════════
   CHITARA — app.js
   ═══════════════════════════════════════════════════════════ */

// ── TOKEN ─────────────────────────────────────────────────
const getToken  = () => localStorage.getItem('chitara_token');
const setToken  = t  => localStorage.setItem('chitara_token', t);
const clearToken = () => localStorage.removeItem('chitara_token');

// ── API CLIENT ────────────────────────────────────────────
const API = {
  async request(method, path, body) {
    const token = getToken();
    const opts = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    };
    if (body) opts.body = JSON.stringify(body);
    const res  = await fetch(path, opts);
    if (res.status === 401) { clearToken(); setLoggedOut(); throw new Error('Session expired'); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
    return data;
  },
  get:    (p)    => API.request('GET',    p),
  post:   (p, b) => API.request('POST',   p, b),
  patch:  (p, b) => API.request('PATCH',  p, b),
  delete: (p)    => API.request('DELETE', p),

  getMe:          ()      => API.get('/api/user/me/'),
  login:          (d)     => API.post('/api/user/login/', d),
  register:       (d)     => API.post('/api/user/register/', d),
  logout:         ()      => API.post('/api/user/logout/'),
  getTags:        ()      => API.get('/api/tags/'),
  getSongs:       ()      => API.get('/api/songs/'),
  getSong:        (id)    => API.get(`/api/songs/${id}/`),
  createSong:     (d)     => API.post('/api/songs/', d),
  deleteSong:     (id)    => API.delete(`/api/songs/${id}/`),
  generateSong:   (id)    => API.post(`/api/songs/${id}/generate/`),
  pollGeneration: (id)    => API.get(`/api/songs/${id}/generate/`),
  shareSong:      (id)    => API.post(`/api/songs/${id}/share/`),
  unshareSong:    (id)    => API.delete(`/api/songs/${id}/share/`),
  getSharedSong:  (hash)  => API.get(`/api/shared/${hash}/`),
};

// ── STATIC TAG FALLBACK ───────────────────────────────────
const STATIC_TAGS = {
  // Must mirror the domain model exactly
  genres: [
    { id: 1, name: 'Pop' },       { id: 2, name: 'Rock' },
    { id: 3, name: 'Classical' }, { id: 4, name: 'R&B' },
    { id: 5, name: 'Lo-fi' },     { id: 6, name: 'Jazz' },
    { id: 7, name: 'Electronic' },
  ],
  moods: [
    { id: 1, name: 'Happy' },     { id: 2, name: 'Sad' },
    { id: 3, name: 'Energetic' }, { id: 4, name: 'Calm' },
    { id: 5, name: 'Aggressive' },{ id: 6, name: 'Focus' },
  ],
  occasions: [
    { id: 1, name: 'Birthday' },  { id: 2, name: 'Graduation' },
    { id: 3, name: 'Workout' },   { id: 4, name: 'Study' },
    { id: 5, name: 'Party' },
  ],
};

// ── STATE ─────────────────────────────────────────────────
const State = {
  user: null,
  songs: [],
  tags: { ...STATIC_TAGS },
  selectedGenres: new Set(),
  selectedMoods: new Set(),
  selectedOccasions: new Set(),
  pollingTimers: {},
};

// ── TOAST ─────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${escHtml(String(msg))}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── AUTH STATE ────────────────────────────────────────────
function setLoggedIn(user) {
  State.user = user;
  const initials = ((user.first_name?.[0] ?? '') + (user.last_name?.[0] ?? '')).toUpperCase()
    || user.email?.[0]?.toUpperCase() || '?';
  const btn = document.getElementById('authBtn');
  btn.textContent = initials;
  btn.title = user.email ?? user.username ?? '';
  btn.style.cssText = 'border-radius:50%;width:32px;height:32px;padding:0;font-weight:600';
  loadSongs();
}

function setLoggedOut() {
  State.user  = null;
  State.songs = [];
  const btn = document.getElementById('authBtn');
  btn.textContent = 'Sign in';
  btn.title = '';
  btn.style.cssText = '';
  Object.values(State.pollingTimers).forEach(clearInterval);
  State.pollingTimers = {};

  document.getElementById('songCount').textContent = '0 songs';
  document.getElementById('songsArea').innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">♪</div>
      <p class="empty-title">Your library</p>
      <p class="empty-auth">Sign in to access your songs.</p>
      <button class="btn-primary" style="margin-top:0.5rem" onclick="openAuthModal()">Sign in</button>
    </div>`;
}

function handleAuthClick() {
  if (State.user) {
    if (confirm(`Sign out of ${State.user.email ?? State.user.username}?`)) doLogout();
  } else {
    openAuthModal();
  }
}

// ── INIT ──────────────────────────────────────────────────
async function init() {
  // OAuth redirect token
  const params   = new URLSearchParams(window.location.search);
  const urlToken = params.get('token');
  if (urlToken) { setToken(urlToken); window.history.replaceState({}, '', '/'); }

  // Shared page
  const shareHash = window.location.pathname.match(/^\/shared\/([^/]+)/)?.[1];
  if (shareHash) { showSharedPage(shareHash); return; }

  // Tags (pre-filled with static; API overrides if available)
  try {
    const apiTags = await API.getTags();
    State.tags = {
      genres:    apiTags.genres?.length    ? apiTags.genres    : STATIC_TAGS.genres,
      moods:     apiTags.moods?.length     ? apiTags.moods     : STATIC_TAGS.moods,
      occasions: apiTags.occasions?.length ? apiTags.occasions : STATIC_TAGS.occasions,
    };
  } catch (_) {}

  if (!getToken()) { setLoggedOut(); return; }

  try {
    const data = await API.getMe();
    if (data.authenticated) setLoggedIn(data.user);
    else { clearToken(); setLoggedOut(); }
  } catch (_) { clearToken(); setLoggedOut(); }
}

// ── AUTH MODAL ────────────────────────────────────────────
function openAuthModal() {
  document.getElementById('authModal').classList.add('open');
  setTimeout(() => document.getElementById('loginUsername')?.focus(), 60);
}

function closeAuthModal(e) {
  if (!e || e.target === document.getElementById('authModal'))
    document.getElementById('authModal').classList.remove('open');
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.auth-tab[data-tab="${tab}"]`).classList.add('active');
  document.getElementById('loginForm').style.display    = tab === 'login'    ? 'block' : 'none';
  document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('loginError').textContent    = '';
  document.getElementById('registerError').textContent = '';
}

async function doLogin() {
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errEl    = document.getElementById('loginError');
  const btn      = document.getElementById('btnLogin');
  errEl.textContent = '';
  if (!username || !password) { errEl.textContent = 'Username and password are required'; return; }
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Signing in…';
  try {
    const data = await API.login({ username, password });
    setToken(data.token);
    closeAuthModal();
    setLoggedIn(data.user);
    toast('Signed in!', 'success');
  } catch (e) {
    errEl.textContent = e.message || 'Invalid credentials';
  } finally {
    btn.disabled = false; btn.textContent = 'Sign In';
  }
}

async function doRegister() {
  const first_name = document.getElementById('regFirstName').value.trim();
  const last_name  = document.getElementById('regLastName').value.trim();
  const username   = document.getElementById('regUsername').value.trim();
  const email      = document.getElementById('regEmail').value.trim();
  const password   = document.getElementById('regPassword').value;
  const errEl      = document.getElementById('registerError');
  const btn        = document.getElementById('btnRegister');
  errEl.textContent = '';
  if (!first_name || !last_name || !username || !email || !password) {
    errEl.textContent = 'All fields are required'; return;
  }
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Creating…';
  try {
    const data = await API.register({ username, email, password, first_name, last_name });
    setToken(data.token);
    closeAuthModal();
    setLoggedIn(data.user);
    toast('Account created!', 'success');
  } catch (e) {
    errEl.textContent = e.message || 'Registration failed';
  } finally {
    btn.disabled = false; btn.textContent = 'Create Account';
  }
}

async function doLogout() {
  try { await API.logout(); } catch (_) {}
  clearToken(); closePlayer(); setLoggedOut();
}

// ── SONGS ─────────────────────────────────────────────────
async function loadSongs() {
  document.getElementById('songsArea').innerHTML =
    '<div class="empty-state"><span class="spinner"></span></div>';
  try {
    const data  = await API.getSongs();
    State.songs = data.results ?? [];
    renderSongs();
    // Auto-resume polling for any songs still stuck in Processing
    State.songs
      .filter(s => s.status?.toLowerCase() === 'processing' && s.generation_task_id)
      .forEach(s => startPolling(s.id));
  } catch (e) { toast(e.message, 'error'); }
}

function renderSongs() {
  const count = State.songs.length;
  document.getElementById('songCount').textContent = `${count} song${count !== 1 ? 's' : ''}`;
  const area = document.getElementById('songsArea');

  // ── Empty state ────────────────────────────────────────
  if (!count) {
    area.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">♪</div>
        <p class="empty-title">Your library is empty</p>
        <p class="empty-desc">Create your first AI-generated song to get started.</p>
        <button class="btn-primary" style="margin-top:0.25rem" onclick="openCreateModal()">
          Create your first song
        </button>
      </div>`;
    return;
  }

  // ── Track list ─────────────────────────────────────────
  const sorted = [...State.songs].sort((a, b) => new Date(b.creation_date) - new Date(a.creation_date));

  area.innerHTML = `
    <div class="songs-header">
      <span class="songs-title">Songs</span>
      <span class="songs-hint">Click a row to view details · Generate to start AI creation.</span>
      <button class="btn-new-song" onclick="openCreateModal()">+ New Song</button>
    </div>

    <div class="track-list">
      <div class="track-header-row">
        <span class="col-num">#</span>
        <span class="col-info">Title</span>
        <span class="col-voice">Voice</span>
        <span class="col-status">Status</span>
        <span class="col-date">Added</span>
        <span class="col-actions"></span>
      </div>
      ${sorted.map((song, i) => trackRowHTML(song, i + 1)).join('')}
    </div>`;
}

function trackRowHTML(song, index) {
  const status   = (song.status ?? '').toLowerCase();
  const badgeCls = { pending:'badge-pending', processing:'badge-processing',
                     completed:'badge-completed', failed:'badge-failed' }[status] ?? '';
  const date     = song.creation_date
    ? new Date(song.creation_date).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' })
    : '';
  const canPlay  = status === 'completed' && song.file_path;
  const canGen   = status === 'pending' || status === 'failed';
  const isStuck  = status === 'processing';
  const prompt   = (song.prompt_text ?? '').slice(0, 65);

  return `
    <div class="track-row" id="song-card-${song.id}" onclick="openDetail(${song.id})">
      <span class="col-num">
        <span class="track-num">${index}</span>
        ${canPlay
          ? `<button class="track-play-btn" title="Play" onclick="event.stopPropagation();playSong(${song.id})">▶</button>`
          : `<span class="track-play-btn" style="color:#333;cursor:default">♪</span>`}
      </span>
      <span class="col-info">
        <div class="track-title">${escHtml(song.title)}</div>
        ${prompt ? `<div class="track-sub">${escHtml(prompt)}${song.prompt_text?.length > 65 ? '…' : ''}</div>` : ''}
      </span>
      <span class="col-voice">${escHtml((song.voice_type ?? '—').toUpperCase())}</span>
      <span class="col-status">
        <span class="badge ${badgeCls}" id="badge-${song.id}">${status.toUpperCase() || '—'}</span>
      </span>
      <span class="col-date">${date}</span>
      <span class="col-actions" onclick="event.stopPropagation()">
        ${canPlay  ? `<button class="action-btn" title="Play"     onclick="playSong(${song.id})">▶</button>` : ''}
        ${canGen   ? `<button class="action-btn" id="gen-btn-${song.id}" title="Generate" onclick="generateSong(${song.id})">⚡</button>` : ''}
        ${isStuck  ? `<button class="action-btn" title="Stuck? Reset to Pending" onclick="resetSong(${song.id})">↺</button>` : ''}
        <button class="action-btn" title="Share"  onclick="toggleShare(${song.id})">⇧</button>
        <button class="action-btn danger" title="Delete" onclick="deleteSong(${song.id})">✕</button>
      </span>
    </div>`;
}

async function doRefresh() {
  if (!State.user) return;
  try {
    const data  = await API.getSongs();
    State.songs = data.results ?? [];
    renderSongs();
    toast('Refreshed', 'info');
  } catch (e) { toast(e.message, 'error'); }
}

// ── CREATE SONG MODAL ─────────────────────────────────────
function openCreateModal() {
  if (!State.user) { openAuthModal(); return; }

  // Reset form
  document.getElementById('fieldTitle').value  = '';
  document.getElementById('fieldPrompt').value = '';
  document.getElementById('fieldVoice').value  = 'female';
  State.selectedGenres.clear();
  State.selectedMoods.clear();
  State.selectedOccasions.clear();
  renderTagPickers();

  document.getElementById('createModal').classList.add('open');
  setTimeout(() => document.getElementById('fieldTitle').focus(), 60);
}

function closeCreateModal(e) {
  if (!e || e.target === document.getElementById('createModal'))
    document.getElementById('createModal').classList.remove('open');
}

function renderTagPickers() {
  renderTagPicker('genrePicker',    State.tags.genres    ?? [], State.selectedGenres,    'genre');
  renderTagPicker('moodPicker',     State.tags.moods     ?? [], State.selectedMoods,     'mood');
  renderTagPicker('occasionPicker', State.tags.occasions ?? [], State.selectedOccasions, 'occasion');
}

function renderTagPicker(id, tags, selected, type) {
  const el = document.getElementById(id);
  if (!tags.length) {
    el.innerHTML = `<span style="color:#252525;font-size:0.72rem">No ${type}s</span>`;
    return;
  }
  el.innerHTML = tags.map(t => `
    <div class="tag-chip ${selected.has(t.id) ? 'selected' : ''}"
         onclick="toggleTag('${type}',${t.id},this)">${escHtml(t.name)}</div>`).join('');
}

function toggleTag(type, id, el) {
  const map = { genre: State.selectedGenres, mood: State.selectedMoods, occasion: State.selectedOccasions };
  const set = map[type];
  if (set.has(id)) { set.delete(id); el.classList.remove('selected'); }
  else             { set.add(id);    el.classList.add('selected'); }
}

async function submitSongForm() {
  const title       = document.getElementById('fieldTitle').value.trim();
  const prompt_text = document.getElementById('fieldPrompt').value.trim();
  const voice_type  = document.getElementById('fieldVoice').value;

  if (!title || !prompt_text) { toast('Title and prompt are required', 'error'); return; }

  const btn = document.getElementById('btnCreate');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Creating…';

  try {
    const song = await API.createSong({
      title, prompt_text, voice_type,
      genre_ids:    [...State.selectedGenres],
      mood_ids:     [...State.selectedMoods],
      occasion_ids: [...State.selectedOccasions],
    });
    State.songs.unshift(song);
    closeCreateModal();
    renderSongs();
    toast('Song created! Click ⚡ Generate to start AI generation.', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Create song';
  }
}

// ── GENERATE ──────────────────────────────────────────────
async function generateSong(id) {
  const btn = document.getElementById(`gen-btn-${id}`);
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }

  try {
    const data = await API.generateSong(id);
    const song = data.song;
    updateSongInState(song);

    if (song.status?.toLowerCase() === 'completed') {
      toast('Song generated!', 'success');
      renderSongs();
    } else {
      toast('Generation started…', 'info');
      startPolling(id);
    }
  } catch (e) {
    toast(e.message, 'error');
    if (btn) { btn.disabled = false; btn.textContent = '⚡'; }
  }
}

function startPolling(id) {
  if (State.pollingTimers[id]) return;
  State.pollingTimers[id] = setInterval(async () => {
    try {
      const data  = await API.pollGeneration(id);
      const song  = data.song;
      updateSongInState(song);

      const badge  = document.getElementById(`badge-${id}`);
      const status = (song.status ?? '').toLowerCase();
      const cls    = { pending:'badge-pending', processing:'badge-processing',
                       completed:'badge-completed', failed:'badge-failed' }[status] ?? '';
      if (badge) { badge.className = `badge ${cls}`; badge.textContent = status.toUpperCase(); }

      if (status === 'completed' || status === 'failed') {
        clearInterval(State.pollingTimers[id]);
        delete State.pollingTimers[id];
        toast(status === 'completed' ? 'Song is ready! ▶' : 'Generation failed',
              status === 'completed' ? 'success' : 'error');
        renderSongs();
      }
    } catch (_) {
      clearInterval(State.pollingTimers[id]);
      delete State.pollingTimers[id];
    }
  }, 3000);
}

function updateSongInState(song) {
  const i = State.songs.findIndex(s => s.id === song.id);
  if (i !== -1) State.songs[i] = song;
}

// ── DETAIL MODAL ──────────────────────────────────────────
async function openDetail(id) {
  try {
    const song = await API.getSong(id);
    updateSongInState(song);
    renderDetail(song);
    document.getElementById('detailModal').classList.add('open');
  } catch (e) { toast(e.message, 'error'); }
}

function renderDetail(song) {
  const status   = (song.status ?? '').toLowerCase();
  const badgeCls = { pending:'badge-pending', processing:'badge-processing',
                     completed:'badge-completed', failed:'badge-failed' }[status] ?? '';
  const canPlay  = status === 'completed' && song.file_path;
  const canGen   = status === 'pending' || status === 'failed';
  const isStuck  = status === 'processing';

  const tagChips = (ids, list) => (ids ?? []).map(id => {
    const t = list?.find(x => x.id === id);
    return t ? `<span class="badge" style="background:#161616;border:1px solid #222;color:#666">${escHtml(t.name)}</span>` : '';
  }).join('');

  document.getElementById('detailTitle').textContent = song.title;
  document.getElementById('detailContent').innerHTML = `
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span class="badge ${badgeCls}">${status.toUpperCase()}</span>
      <span style="font-size:0.72rem;color:#444">
        ${song.creation_date ? new Date(song.creation_date).toLocaleString() : ''}
      </span>
    </div>

    <div class="detail-actions">
      ${canPlay  ? `<button class="card-btn play" onclick="playSong(${song.id})">▶ Play</button>` : ''}
      ${canGen   ? `<button class="card-btn" onclick="generateSong(${song.id})">⚡ Generate</button>` : ''}
      ${isStuck  ? `<button class="card-btn" title="Stuck? Reset back to Pending so you can Generate again" onclick="resetSong(${song.id}, true)">↺ Reset</button>` : ''}
      ${canPlay  ? `<a href="/api/songs/${song.id}/download/" class="card-btn" download>↓ Download</a>` : ''}
      <button class="card-btn" onclick="toggleShare(${song.id})">${song.is_shared ? '✕ Unshare' : '⇧ Share'}</button>
      <button class="card-btn danger" onclick="deleteSong(${song.id}, true)">✕ Delete</button>
    </div>

    ${song.is_shared ? `
      <div class="share-url-row">
        <span>${window.location.origin}/shared/${song.share_hash}/</span>
        <button class="card-btn" onclick="copyShareUrl('${escHtml(song.share_hash)}')">Copy</button>
      </div>` : ''}

    <div class="detail-row">
      <div class="detail-row-label">Prompt</div>
      <div class="detail-row-value">${escHtml(song.prompt_text || '—')}</div>
    </div>
    <div class="detail-row">
      <div class="detail-row-label">Voice Type</div>
      <div class="detail-row-value" style="text-transform:uppercase">${escHtml(song.voice_type || '—')}</div>
    </div>
    ${(song.genre_ids?.length || song.mood_ids?.length || song.occasion_ids?.length) ? `
    <div class="detail-row">
      <div class="detail-row-label">Tags</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.35rem;margin-top:0.25rem">
        ${tagChips(song.genre_ids, State.tags.genres)}
        ${tagChips(song.mood_ids,  State.tags.moods)}
        ${tagChips(song.occasion_ids, State.tags.occasions)}
      </div>
    </div>` : ''}
    ${song.duration ? `
    <div class="detail-row">
      <div class="detail-row-label">Duration</div>
      <div class="detail-row-value">${formatDuration(song.duration)}</div>
    </div>` : ''}
  `;
}

function closeDetailModal(e) {
  if (!e || e.target === document.getElementById('detailModal'))
    document.getElementById('detailModal').classList.remove('open');
}

// ── SHARE ─────────────────────────────────────────────────
async function toggleShare(id) {
  const song = State.songs.find(s => s.id === id);
  try {
    let data;
    if (song?.is_shared) {
      data = await API.unshareSong(id);
      toast('Share link revoked', 'info');
    } else {
      data = await API.shareSong(id);
      await navigator.clipboard.writeText(`${window.location.origin}/shared/${data.song.share_hash}/`).catch(() => {});
      toast('Share link copied to clipboard!', 'success');
    }
    updateSongInState(data.song);
    renderSongs();
    if (document.getElementById('detailModal').classList.contains('open')) renderDetail(data.song);
  } catch (e) { toast(e.message, 'error'); }
}

function copyShareUrl(hash) {
  navigator.clipboard.writeText(`${window.location.origin}/shared/${hash}/`)
    .then(() => toast('Copied!', 'success'));
}

// ── DELETE ────────────────────────────────────────────────
async function deleteSong(id, closeModal = false) {
  if (!confirm('Delete this song permanently?')) return;
  try {
    await API.deleteSong(id);
    State.songs = State.songs.filter(s => s.id !== id);
    if (closeModal) document.getElementById('detailModal').classList.remove('open');
    renderSongs();
    toast('Song deleted', 'info');
  } catch (e) { toast(e.message, 'error'); }
}

// ── RESET STUCK SONG ─────────────────────────────────────
async function resetSong(id, closeModal = false) {
  try {
    const song = await API.request('PATCH', `/api/songs/${id}/`, {
      status: 'Pending',
      generation_task_id: null,
    });
    // Stop any active polling for this song
    if (State.pollingTimers[id]) {
      clearInterval(State.pollingTimers[id]);
      delete State.pollingTimers[id];
    }
    updateSongInState(song);
    if (closeModal) {
      document.getElementById('detailModal').classList.remove('open');
    }
    renderSongs();
    toast('Song reset to Pending — click ⚡ Generate to try again', 'info');
  } catch (e) { toast(e.message, 'error'); }
}

// ── AUDIO PLAYER ──────────────────────────────────────────
let audio = null;

function playSong(id) {
  const song = State.songs.find(s => s.id === id);
  if (!song?.file_path) return;
  if (audio) { audio.pause(); audio = null; }

  document.getElementById('playerTitle').textContent = song.title;
  document.getElementById('playerSub').textContent   = (song.voice_type ?? 'AI').toUpperCase();
  document.getElementById('audioBar').classList.add('visible');

  audio = new Audio(song.file_path);
  audio.play().catch(() => {
    audio = new Audio(`/api/songs/${id}/download/`);
    audio.play().catch(() => toast('Cannot play this audio', 'error'));
  });
  audio.addEventListener('timeupdate', updateProgress);
  audio.addEventListener('play',  () => document.getElementById('playBtn').textContent = '⏸');
  audio.addEventListener('pause', () => document.getElementById('playBtn').textContent = '▶');
  audio.addEventListener('ended', () => {
    document.getElementById('playBtn').textContent = '▶';
    document.getElementById('progressFill').style.width = '0%';
  });
}

function updateProgress() {
  if (!audio?.duration) return;
  document.getElementById('progressFill').style.width = `${(audio.currentTime / audio.duration) * 100}%`;
  document.getElementById('timeLabel').textContent =
    `${formatDuration(audio.currentTime)} / ${formatDuration(audio.duration)}`;
}

function togglePlay() { if (audio) audio.paused ? audio.play() : audio.pause(); }

function seekProgress(e) {
  if (!audio?.duration) return;
  const r = e.currentTarget.getBoundingClientRect();
  audio.currentTime = ((e.clientX - r.left) / r.width) * audio.duration;
}

function closePlayer() {
  if (audio) { audio.pause(); audio = null; }
  document.getElementById('audioBar').classList.remove('visible');
}

// ── SHARED PAGE ───────────────────────────────────────────
async function showSharedPage(hash) {
  document.querySelector('.app-shell').style.display = 'none';

  const wrap = document.createElement('div');
  wrap.style.cssText = 'min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem;background:#0a0a0a';
  const card = document.createElement('div');
  card.style.cssText = 'background:#111;border:1px solid #1a1a1a;border-radius:12px;padding:2.5rem;max-width:480px;width:100%;text-align:center';
  card.innerHTML = '<span class="spinner"></span>';
  wrap.appendChild(card);
  document.body.appendChild(wrap);

  try {
    const { song } = await API.getSharedSong(hash);
    const date = song.creation_date ? new Date(song.creation_date).toLocaleDateString() : '';
    card.innerHTML = `
      <div style="font-size:2.5rem;margin-bottom:0.5rem">🎵</div>
      <h1 style="font-size:1.25rem;font-weight:600;margin-bottom:0.2rem">${escHtml(song.title)}</h1>
      <p style="font-size:0.72rem;color:#444;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1.5rem">
        ${escHtml((song.voice_type ?? 'AI').toUpperCase())} · ${date}
      </p>
      ${song.file_path
        ? `<button class="btn-primary" style="margin:0 auto 1.25rem;display:block"
                   onclick="playSharedAudio(this,'${escHtml(song.file_path)}','${escHtml(song.title)}')">
             ▶ Play Song
           </button>`
        : '<p style="color:#444;font-size:0.85rem;margin-bottom:1rem">Audio not available yet</p>'}
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:1rem;text-align:left">
        <div style="font-size:0.63rem;color:#444;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem">Prompt</div>
        <p style="font-size:0.85rem;color:#888;line-height:1.6">${escHtml(song.prompt_text || '—')}</p>
      </div>
      <a href="/" style="display:inline-block;margin-top:1.5rem;font-size:0.72rem;color:#333;text-decoration:none">← Back to Chitara</a>`;
  } catch (_) {
    card.innerHTML = `
      <div style="font-size:2.5rem;opacity:0.15;margin-bottom:1rem">✕</div>
      <h2 style="font-size:1.1rem;margin-bottom:0.5rem">Song not found</h2>
      <p style="color:#444;font-size:0.85rem">This link may have expired or been revoked.</p>
      <a href="/" style="display:inline-block;margin-top:1.5rem;font-size:0.72rem;color:#333;text-decoration:none">← Back to Chitara</a>`;
  }

  // Inject audio bar for shared playback
  const bar = document.createElement('div');
  bar.className = 'audio-bar'; bar.id = 'audioBar';
  bar.innerHTML = `
    <div class="player-info">
      <div class="player-title" id="playerTitle">—</div>
      <div class="player-sub"   id="playerSub">SHARED</div>
    </div>
    <button class="play-btn" id="playBtn" onclick="togglePlay()">▶</button>
    <div class="progress-wrap">
      <div class="progress-bar" onclick="seekProgress(event)">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <span class="time-label" id="timeLabel">0:00 / 0:00</span>
    </div>
    <button class="close-player" onclick="closePlayer()">✕</button>`;
  document.body.appendChild(bar);
}

function playSharedAudio(btnEl, filePath, title) {
  document.getElementById('playerTitle').textContent = title;
  document.getElementById('audioBar').classList.add('visible');
  if (audio) audio.pause();
  audio = new Audio(filePath);
  audio.play().catch(() => {});
  audio.addEventListener('play',       () => { document.getElementById('playBtn').textContent = '⏸'; });
  audio.addEventListener('pause',      () => { document.getElementById('playBtn').textContent = '▶'; });
  audio.addEventListener('timeupdate', updateProgress);
  btnEl.textContent = '⏸ Playing…';
}

// ── NAV ───────────────────────────────────────────────────
function navigate(view) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`[data-nav="${view}"]`)?.classList.add('active');
  if (view === 'create') openCreateModal();
  else window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── HELPERS ───────────────────────────────────────────────
function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatDuration(s) {
  if (!s) return '0:00';
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
}

// ── BOOT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  init();
  document.getElementById('loginPassword')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') doLogin();
  });
  document.getElementById('fieldTitle')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('fieldPrompt')?.focus();
  });
});
