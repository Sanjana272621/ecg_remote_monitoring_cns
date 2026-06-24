// history.js
const CHUNK_MS = 10_000;   // 10 seconds per page
const ECG_SAMPLE_INTERVAL_MS  = 20;   // your loop runs every 20 ms → 33 samples/row × 20 ms = 660 ms/row
const OTHER_SAMPLE_INTERVAL_MS = 20;

// ── Cache ─────────────────────────────────────────────────────────────────────
// key = chunkStart (ms), value = { ecg: [...], resp: [...], spo2: [...] }
const cache = {};
let inFlight = {};  // prevent duplicate fetches

async function fetchChunk(startMs) {
  if (cache[startMs]) return cache[startMs];
  if (inFlight[startMs]) return inFlight[startMs];

  const endMs = startMs + CHUNK_MS;
  const promise = Promise.all([
    fetch(`/api/ecg_history?start=${startMs}&end=${endMs}`).then(r => r.json()),
    fetch(`/api/resp_history?start=${startMs}&end=${endMs}`).then(r => r.json()),
    fetch(`/api/spo2_history?start=${startMs}&end=${endMs}`).then(r => r.json()),
  ]).then(([ecg, resp, spo2]) => {
    const chunk = { ecg, resp, spo2 };
    cache[startMs] = chunk;
    delete inFlight[startMs];
    return chunk;
  });

  inFlight[startMs] = promise;
  return promise;
}

function prefetch(startMs) {
  fetchChunk(startMs).catch(() => {});               // next
  fetchChunk(startMs - CHUNK_MS).catch(() => {});    // prev
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

// ── State + navigation ────────────────────────────────────────────────────────
let currentStart = Date.now() - CHUNK_MS;  // start 10 s ago

async function loadAndRender(startMs) {
  document.getElementById('status').textContent = 'Loading…';
  document.getElementById('prevBtn').disabled = true;
  document.getElementById('nextBtn').disabled = true;

  try {
    const chunk = await fetchChunk(startMs);

    renderWave('ecgI',  flattenEcg(chunk.ecg, 'ecgI'),   '#00e676');
    renderWave('ecgII', flattenEcg(chunk.ecg, 'ecgII'),  '#40c4ff');
    renderWave('ecgV',  flattenEcg(chunk.ecg, 'ecgV'),   '#ea80fc');
    renderWave('resp',  flattenOther(chunk.resp),         '#ffd740');
    renderWave('spo2',  flattenOther(chunk.spo2),         '#ff6e40');

    const from = new Date(startMs).toLocaleTimeString();
    const to   = new Date(startMs + CHUNK_MS).toLocaleTimeString();
    document.getElementById('time-display').textContent = `${from} → ${to}`;
    document.getElementById('status').textContent = '';

    // Pre-fetch neighbours so the next click is instant
    prefetch(startMs + CHUNK_MS);
    prefetch(startMs - CHUNK_MS);
  } catch (err) {
    document.getElementById('status').textContent = 'Error loading data.';
    console.error(err);
  } finally {
    document.getElementById('prevBtn').disabled = false;
    document.getElementById('nextBtn').disabled = currentStart + CHUNK_MS >= Date.now();
  }
}

document.getElementById('prevBtn').addEventListener('click', () => {
  currentStart -= CHUNK_MS;
  loadAndRender(currentStart);
});

document.getElementById('nextBtn').addEventListener('click', () => {
  if (currentStart + CHUNK_MS >= Date.now()) return;
  currentStart += CHUNK_MS;
  loadAndRender(currentStart);
});

// Start: last 10 seconds
loadAndRender(currentStart);