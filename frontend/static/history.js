// history.js
const CHUNK_MS = 10_000;
const ECG_SAMPLE_INTERVAL_MS  = 20;
const OTHER_SAMPLE_INTERVAL_MS = 20;

let currentPatientId = null;

// ── Cache ─────────────────────────────────────────────────────────────────────
// cache is now keyed by patientId → { startMs → chunk }
let cache = {};
let inFlight = {};

async function fetchChunk(patientId, startMs) {
  cache[patientId] = cache[patientId] || {};
  inFlight[patientId] = inFlight[patientId] || {};

  if (cache[patientId][startMs]) return cache[patientId][startMs];
  if (inFlight[patientId][startMs]) return inFlight[patientId][startMs];

  const endMs = startMs + CHUNK_MS;
  const promise = Promise.all([
    fetch(`/api/ecg_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
    fetch(`/api/resp_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
    fetch(`/api/spo2_history?patient_id=${patientId}&start=${startMs}&end=${endMs}`).then(r => r.json()),
  ]).then(([ecg, resp, spo2]) => {
    const chunk = { ecg, resp, spo2 };
    cache[patientId][startMs] = chunk;
    delete inFlight[patientId][startMs];
    return chunk;
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

// ── State + navigation ────────────────────────────────────────────────────────
let currentStart = Date.now() - CHUNK_MS;

async function loadAndRender(startMs) {
  if (!currentPatientId) return;

  document.getElementById('status').textContent = 'Loading…';
  document.getElementById('prevBtn').disabled = true;
  document.getElementById('nextBtn').disabled = true;

  try {
    const chunk = await fetchChunk(currentPatientId, startMs);

    renderWave('ecgI',  flattenEcg(chunk.ecg, 'ecgI'),   '#00e676');
    renderWave('ecgII', flattenEcg(chunk.ecg, 'ecgII'),  '#40c4ff');
    renderWave('ecgV',  flattenEcg(chunk.ecg, 'ecgV'),   '#ea80fc');
    renderWave('resp',  flattenOther(chunk.resp),         '#ffd740');
    renderWave('spo2',  flattenOther(chunk.spo2),         '#ff6e40');

    const from = new Date(startMs).toLocaleTimeString();
    const to   = new Date(startMs + CHUNK_MS).toLocaleTimeString();
    document.getElementById('time-display').textContent = `${from} → ${to}`;
    document.getElementById('status').textContent = '';

    prefetch(currentPatientId, startMs + CHUNK_MS);
    prefetch(currentPatientId, startMs - CHUNK_MS);
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

// ── Patient dropdown ───────────────────────────────────────────────────────────
async function loadPatients() {
  const select = document.getElementById('patientSelect');
  try {
    const patients = await fetch('/api/patients').then(r => r.json());
    select.innerHTML = patients
      .map(p => `<option value="${p.id}">${p.name}${p.bedno ? ' (' + p.bedno + ')' : ''}</option>`)
      .join('');

    if (patients.length) {
      currentPatientId = patients[0].id;
      loadAndRender(currentStart);
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
  currentStart = Date.now() - CHUNK_MS;  // reset window on patient switch
  loadAndRender(currentStart);
});

// Start: load patient list, then last 10 seconds for the first patient
loadPatients();