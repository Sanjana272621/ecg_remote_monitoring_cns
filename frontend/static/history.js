// history.js
const CHUNK_MS = 10_000;
const ECG_SAMPLE_INTERVAL_MS  = 20;
const OTHER_SAMPLE_INTERVAL_MS = 20;

// How far behind "now" we assume the backend has fully ingested data.
// Bump this up if you still see empty windows at the live edge.
const SAFETY_LAG_MS = 1500;

let currentPatientId = null;

// ── Cache ─────────────────────────────────────────────────────────────────────
// cache is keyed by patientId → { startMs → { chunk, stable } }
//
// `stable` means: at the time this chunk was fetched, its window
// (startMs..startMs+CHUNK_MS) was already safely past the ingestion lag,
// so we can trust it forever. If a chunk was fetched *before* it was safely
// past the lag (e.g. via prefetch on a not-yet-fully-ingested window), it's
// marked unstable — and an unstable entry is always revalidated on the next
// access, regardless of whether the caller explicitly asked for forceFresh.
// This is what prevents a chunk from getting permanently "stuck" empty just
// because it happened to be prefetched a moment too early.
let cache = {};
let inFlight = {};

function historyFetch(url, init = {}) {
  return fetch(url, {
    cache: 'no-store',
    headers: { 'Cache-Control': 'no-store' },
    ...init,
  });
}

function isWindowStable(startMs, atTime = Date.now()) {
  return (startMs + CHUNK_MS + SAFETY_LAG_MS) <= atTime;
}

/**
 * Fetch (or return cached) chunk for [startMs, startMs+CHUNK_MS).
 * Pass forceFresh=true to explicitly bypass the cache and re-hit the API.
 *
 * Even without forceFresh, any cached entry that isn't yet "stable" (i.e.
 * it was fetched while its window could still be mid-ingestion) will be
 * revalidated rather than trusted blindly.
 */
async function fetchChunk(patientId, startMs, forceFresh = false) {
  cache[patientId] = cache[patientId] || {};
  inFlight[patientId] = inFlight[patientId] || {};

  const entry = cache[patientId][startMs];
  const canTrustCache = !forceFresh && entry && entry.stable;

  if (canTrustCache) return entry.chunk;

  if (!forceFresh && inFlight[patientId][startMs]) {
    return inFlight[patientId][startMs];
  }

  if (forceFresh) {
    // Don't let a stale in-flight promise from an earlier "too early" fetch
    // shadow this fresh request.
    delete inFlight[patientId][startMs];
  }

  const endMs = startMs + CHUNK_MS;
  const promise = Promise.all([
    historyFetch(`/api/ecg_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
    historyFetch(`/api/resp_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
    historyFetch(`/api/spo2_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
  ]).then(([ecg, resp, spo2]) => {
    const chunk = { ecg, resp, spo2 };
    // Only trust this result long-term if the window was already safely
    // past the ingestion lag by the time the fetch resolved. Otherwise,
    // leave it marked unstable so the next access re-fetches it instead of
    // trusting a possibly-incomplete result forever.
    cache[patientId][startMs] = { chunk, stable: isWindowStable(startMs) };
    delete inFlight[patientId][startMs];
    return chunk;
  }).catch(err => {
    delete inFlight[patientId][startMs];
    throw err;
  });

  inFlight[patientId][startMs] = promise;
  return promise;
}

function prefetch(patientId, startMs) {
  fetchChunk(patientId, startMs).catch(() => {});
  fetchChunk(patientId, startMs - CHUNK_MS).catch(() => {});
}

// ── Flatten rows → sample array ───────────────────────────────────────────────
function flattenEcg(rows, field) {
  return rows.flatMap(row =>
    (row[field] || []).map((v, i) => ({
      t: row.timestamp + i * ECG_SAMPLE_INTERVAL_MS,
      v,
    }))
  );
}

function flattenOther(rows) {
  return rows.flatMap(row =>
    (row.waveform || []).map((v, i) => ({
      t: row.timestamp + i * OTHER_SAMPLE_INTERVAL_MS,
      v,
    }))
  );
}

// ── Canvas rendering ──────────────────────────────────────────────────────────
function renderWave(canvasId, samples, color = '#00e676') {
  const canvas = document.getElementById(canvasId);
  const ctx    = canvas.getContext('2d');
  const dpr    = window.devicePixelRatio || 1;

  canvas.width  = canvas.offsetWidth  * dpr;
  canvas.height = canvas.offsetHeight * dpr;
  ctx.scale(dpr, dpr);

  const W = canvas.offsetWidth;
  const H = canvas.offsetHeight;

  ctx.clearRect(0, 0, W, H);

  if (!samples.length) {
    ctx.fillStyle = '#555';
    ctx.font = '12px sans-serif';
    ctx.fillText('No data for this window', W / 2 - 70, H / 2);
    return;
  }

  const vals = samples.map(s => s.v);
  const min  = Math.min(...vals);
  const max  = Math.max(...vals);
  const range = max - min || 1;

  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth   = 1.2;

  samples.forEach((pt, i) => {
    const x = (i / (samples.length - 1)) * W;
    const y = H - ((pt.v - min) / range) * (H - 8) - 4;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });

  ctx.stroke();
}

// ── Window helpers ─────────────────────────────────────────────────────────────
// The most recent window we're willing to request, given ingestion lag.
function latestWindowStart() {
  return Date.now() - SAFETY_LAG_MS - CHUNK_MS;
}

function isAtLatestWindow() {
  return currentStart >= latestWindowStart();
}

// ── State + navigation ────────────────────────────────────────────────────────
let currentStart = latestWindowStart();
let liveMode = true;      // whether we auto-advance to the newest window
let liveTimer = null;

async function loadAndRender(startMs, forceFresh = false) {
  if (!currentPatientId) return;

  document.getElementById('status').textContent = 'Loading…';
  document.getElementById('prevBtn').disabled = true;
  document.getElementById('nextBtn').disabled = true;

  try {
    const chunk = await fetchChunk(currentPatientId, startMs, forceFresh);

    renderWave('ecgI',  flattenEcg(chunk.ecg, 'ecgI'),   '#00e676');
    renderWave('ecgII', flattenEcg(chunk.ecg, 'ecgII'),  '#40c4ff');
    renderWave('ecgV',  flattenEcg(chunk.ecg, 'ecgV'),   '#ea80fc');
    renderWave('resp',  flattenOther(chunk.resp),         '#ffd740');
    renderWave('spo2',  flattenOther(chunk.spo2),         '#ff6e40');

    const from = new Date(startMs).toLocaleTimeString();
    const to   = new Date(startMs + CHUNK_MS).toLocaleTimeString();
    document.getElementById('time-display').textContent = `${from} → ${to}` + (liveMode ? '  •  LIVE' : '');
    document.getElementById('status').textContent = '';

    prefetch(currentPatientId, startMs + CHUNK_MS);
    prefetch(currentPatientId, startMs - CHUNK_MS);
  } catch (err) {
    document.getElementById('status').textContent = 'Error loading data.';
    console.error(err);
  } finally {
    document.getElementById('prevBtn').disabled = false;
    document.getElementById('nextBtn').disabled = isAtLatestWindow();
  }
}

document.getElementById('prevBtn').addEventListener('click', () => {
  currentStart -= CHUNK_MS;
  liveMode = false;
  loadAndRender(currentStart);
});

document.getElementById('nextBtn').addEventListener('click', () => {
  if (isAtLatestWindow()) return;
  currentStart += CHUNK_MS;
  liveMode = isAtLatestWindow();
  // No need to force it here anymore — fetchChunk() will automatically
  // revalidate this window on its own if it was cached before it was stable.
  loadAndRender(currentStart);
});

// ── Live refresh ───────────────────────────────────────────────────────────────
// Keep refreshing the visible window and advance it forward as the live edge
// moves, so the next chunk keeps updating instead of staying stuck on an old
// window while new data arrives.
function startLiveRefresh() {
  clearInterval(liveTimer);
  liveTimer = setInterval(() => {
    if (!currentPatientId) return;

    const latestStart = latestWindowStart();

    if (liveMode) {
      // Auto-following the live edge: advance the window forward.
      currentStart = latestStart;
    }
    // else: leave currentStart alone — don't push the user to the live page.

    // Always refresh whatever window is currently on screen.
    loadAndRender(currentStart, /* forceFresh */ true);
  }, CHUNK_MS);
}
// ── Patient dropdown ───────────────────────────────────────────────────────────
async function loadPatients() {
  const select = document.getElementById('patientSelect');
  try {
    const patients = await historyFetch('/api/patients').then(r => r.json());
    select.innerHTML = patients
      .map(p => `<option value="${p.id}">${p.name}${p.bedno ? ' (' + p.bedno + ')' : ''}</option>`)
      .join('');

    if (patients.length) {
      currentPatientId = patients[0].id;
      currentStart = latestWindowStart();
      liveMode = true;
      loadAndRender(currentStart);
      startLiveRefresh();
    } else {
      document.getElementById('status').textContent = 'No patients found.';
    }
  } catch (err) {
    document.getElementById('status').textContent = 'Error loading patients.';
    console.error(err);
  }
}

document.getElementById('patientSelect').addEventListener('change', (e) => {
  currentPatientId = e.target.value;
  currentStart = latestWindowStart(); // reset window on patient switch
  liveMode = true;
  loadAndRender(currentStart);
});

// Start: load patient list, then last 10 seconds (minus safety lag) for the
// first patient, and begin live polling.
loadPatients();