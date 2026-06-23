// =====================================================================
// history.js — waveform history viewer
// =====================================================================
//
// HOW IT WORKS
// ─────────────
// Time is divided into 30-second "chunks".  A chunk is identified by
// its start epoch (ms, floored to 30 s boundary):
//
//     chunkKey(t) = Math.floor(t / 30000) * 30000
//
// The chunk cache (Map) stores resolved sample arrays, so the same
// 30-second window is never fetched from the server twice within a
// session, no matter how many times the user scrolls back over it.
//
// On Load:
//   1. The full requested time range is divided into chunk keys.
//   2. All chunks are fetched in parallel (Promise.all).
//   3. Results are concatenated into one big typed array per channel.
//   4. uPlot is initialised (or updated) with that data.
//
// On Scroll / Zoom (uPlot setSelect / hook):
//   • The visible window is read from uPlot's x-scale.
//   • The ±1 chunks just outside the visible window are prefetched
//     into the cache so they are ready before the user scrolls there.
//
// Backend contract (what your FastAPI must return):
//   GET /history?channel=ecg&start=<ms>&end=<ms>
//   → { timestamps: [ms, ms, …], ecgI: […], ecgII: […], ecgV: […] }
//
//   GET /history?channel=resp&start=<ms>&end=<ms>
//   → { timestamps: [ms, ms, …], resp: […] }
//
//   GET /history?channel=spo2&start=<ms>&end=<ms>
//   → { timestamps: [ms, ms, …], spo2: […] }
//
// Timestamps must be epoch-milliseconds so uPlot can place them on the
// time axis.  The server should flatten each DB row's sample array and
// produce one timestamp per sample (interpolated linearly within each
// row's time range if you don't store per-sample timestamps).
// =====================================================================

// ── Constants ─────────────────────────────────────────────────────────
const CHUNK_MS    = 30_000;   // 30-second chunk size — matches backend fetch unit
const MAX_CHUNKS  = 60;       // evict oldest when cache exceeds this (30 min max in memory)
const PREFETCH_CHUNKS = 1;    // how many chunks ahead/behind to prefetch on scroll

// ── Colours matching the CSS tokens ───────────────────────────────────
const COLOR = {
  ecg:  '#00e664',
  resp: '#00c8ff',
  spo2: '#ff9900',
  grid: 'rgba(255,255,255,0.06)',
  text: '#607060',
};

// ── Chunk cache: Map<chunkKey, Promise<chunkData>> ────────────────────
// We cache the *Promise* (not the resolved value) so that a chunk
// being fetched right now won't trigger a second fetch if another
// scroll event fires before it resolves.
const chunkCache  = new Map();   // key: `${channel}_${chunkStartMs}`
const chunkOrder  = [];          // insertion order for LRU eviction

function chunkKey(channel, t) {
    const start = Math.floor(t / CHUNK_MS) * CHUNK_MS;
    return `${channel}_${start}`;
}

function chunkStart(key) {
    return parseInt(key.split('_')[1], 10);
}

// ── LRU eviction ──────────────────────────────────────────────────────
function touchChunk(key) {
    const idx = chunkOrder.indexOf(key);
    if (idx !== -1) chunkOrder.splice(idx, 1);
    chunkOrder.push(key);
    if (chunkOrder.length > MAX_CHUNKS) {
        const evict = chunkOrder.shift();
        chunkCache.delete(evict);
    }
}

// ── Fetch one 30-second chunk from the server ─────────────────────────
// Returns a promise that resolves to a plain object:
//   { timestamps: Float64Array, [channelFields]: Float32Array }
// The promise is stored in chunkCache immediately so parallel callers
// wait on the same request rather than issuing duplicate fetches.
function fetchChunk(channel, startMs) {
    const key = `${channel}_${startMs}`;
    if (chunkCache.has(key)) {
        touchChunk(key);
        return chunkCache.get(key);
    }

    const endMs = startMs + CHUNK_MS;
    const url   = `/api/history?channel=${channel}&start=${startMs}&end=${endMs}`;

    const promise = fetch(url)
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
            return r.json();
        })
        .then(data => {
            // Convert plain arrays to typed arrays for memory efficiency
            const out = {
                timestamps: new Float64Array(data.timestamps || []),
            };
            for (const field of channelFields(channel)) {
                out[field] = new Float32Array(data[field] || []);
            }
            return out;
        });

    chunkCache.set(key, promise);
    touchChunk(key);
    return promise;
}

// ── Which JSON fields does a given channel return? ────────────────────
function channelFields(channel) {
    if (channel === 'ecg')  return ['ecgI', 'ecgII', 'ecgV'];
    if (channel === 'resp') return ['resp'];
    if (channel === 'spo2') return ['spo2'];
    return [];
}

// ── Fetch all chunks covering [startMs, endMs] ────────────────────────
async function fetchRange(channel, startMs, endMs) {
    const keys = [];
    for (let t = Math.floor(startMs / CHUNK_MS) * CHUNK_MS; t < endMs; t += CHUNK_MS) {
        keys.push(t);
    }

    const chunks = await Promise.all(keys.map(t => fetchChunk(channel, t)));

    // Concatenate typed arrays from all chunks into single arrays
    const totalLen = chunks.reduce((s, c) => s + c.timestamps.length, 0);
    const merged = { timestamps: new Float64Array(totalLen) };
    for (const f of channelFields(channel)) {
        merged[f] = new Float32Array(totalLen);
    }

    let offset = 0;
    for (const chunk of chunks) {
        merged.timestamps.set(chunk.timestamps, offset);
        for (const f of channelFields(channel)) {
            merged[f].set(chunk[f], offset);
        }
        offset += chunk.timestamps.length;
    }

    return merged;
}

// ── Prefetch chunks just outside the visible window ───────────────────
// Called on every uPlot zoom/pan so data is ready before the user
// scrolls/zooms to it.
function prefetch(visibleMinMs, visibleMaxMs) {
    for (let n = 1; n <= PREFETCH_CHUNKS; n++) {
        const before = visibleMinMs - n * CHUNK_MS;
        const after  = visibleMaxMs + (n - 1) * CHUNK_MS;
        for (const ch of ['ecg', 'resp', 'spo2']) {
            fetchChunk(ch, Math.floor(before / CHUNK_MS) * CHUNK_MS);
            fetchChunk(ch, Math.floor(after  / CHUNK_MS) * CHUNK_MS);
        }
    }
}

// ── Status bar helpers ────────────────────────────────────────────────
const statusDot  = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

function setStatus(state, msg) {
    statusDot.className  = `dot ${state}`;  // '', 'loading', 'ok', 'error'
    statusText.textContent = msg;
}

// ── uPlot chart instances (one per waveform row) ──────────────────────
const plots   = {};   // { ecgI, ecgII, ecgV, resp, spo2 }
let   globalMin = 0, globalMax = 0;

// Shared uPlot x-axis options — used on every chart so they all pan in sync
function makeXAxis() {
    return {
        space: 60,
        values: (u, vals) => vals.map(v => fmtTime(v * 1000)),  // uPlot passes seconds
        stroke: COLOR.text,
        grid:  { stroke: COLOR.grid, width: 1 },
        ticks: { stroke: COLOR.grid, width: 1 },
    };
}

function makeYAxis(color) {
    return {
        stroke: color,
        grid:   { stroke: COLOR.grid, width: 1 },
        ticks:  { stroke: COLOR.grid, width: 1 },
        size:   40,
    };
}

// uPlot config factory for a single-series chart (ECG I/II/V, RESP, SPO2)
function makePlotOpts(containerId, seriesColor, yLabel) {
    const wrap = document.getElementById(containerId);
    return {
        width:  wrap.clientWidth  || 800,
        height: wrap.clientHeight || 128,
        padding: [6, 4, 0, 0],
        cursor: { show: true, drag: { x: true, y: false, setScale: false } },
        select: { show: false },
        legend: { show: false },
        scales: {
            x: { time: true },
            y: { auto: true },
        },
        axes: [
            makeXAxis(),
            makeYAxis(seriesColor),
        ],
        series: [
            {},   // x (timestamps)
            {
                stroke: seriesColor,
                width:  1.5,
                label:  yLabel,
                points: { show: false },
            },
        ],
    };
}

// ── Build or rebuild all five uPlot instances ─────────────────────────
function initPlots() {
    const configs = [
        { id: 'ecgI',  wrap: 'wrap-ecgI',  color: COLOR.ecg,  label: 'ECG I'  },
        { id: 'ecgII', wrap: 'wrap-ecgII', color: COLOR.ecg,  label: 'ECG II' },
        { id: 'ecgV',  wrap: 'wrap-ecgV',  color: COLOR.ecg,  label: 'ECG V'  },
        { id: 'resp',  wrap: 'wrap-resp',  color: COLOR.resp, label: 'Resp'   },
        { id: 'spo2',  wrap: 'wrap-spo2',  color: COLOR.spo2, label: 'SpO₂'  },
    ];

    for (const cfg of configs) {
        if (plots[cfg.id]) { plots[cfg.id].destroy(); }
        const opts = makePlotOpts(cfg.wrap, cfg.color, cfg.label);
        const el   = document.getElementById(cfg.wrap);
        // uPlot needs empty initial data
        plots[cfg.id] = new uPlot(opts, [[], []], el);

        // hook: when user drags to pan this chart, update timeline label
        // and prefetch chunks around the new view
        plots[cfg.id].over.addEventListener('mousemove', () => {
            const sc = plots[cfg.id].scales.x;
            if (sc.min != null) {
                prefetch(sc.min * 1000, sc.max * 1000);
                updateTimelineLabel(sc.min * 1000, sc.max * 1000);
            }
        });
    }
}

// ── Push loaded data into uPlot ───────────────────────────────────────
// uPlot expects timestamps in *seconds*, data in Float32/64 arrays.
function setChartData(channelId, timestamps, values) {
    const plot = plots[channelId];
    if (!plot) return;

    // uPlot wants arrays; typed arrays work fine
    // timestamps from DB are epoch-ms → convert to epoch-s for uPlot
    const ts = new Float64Array(timestamps.length);
    for (let i = 0; i < timestamps.length; i++) ts[i] = timestamps[i] / 1000;

    plot.setData([ts, values], true);

    // Hide overlay once we have real data
    const overlay = document.getElementById(`overlay-${channelId}`);
    if (overlay) overlay.classList.add('hidden');
}

// ── Show overlays (NO DATA / loading state) ───────────────────────────
function showOverlay(channelId, msg) {
    const overlay = document.getElementById(`overlay-${channelId}`);
    if (!overlay) return;
    overlay.textContent = msg;
    overlay.classList.remove('hidden');
}

function showAllOverlays(msg) {
    for (const id of ['ecgI', 'ecgII', 'ecgV', 'resp', 'spo2']) {
        showOverlay(id, msg);
    }
}

// ── Timeline scrubber ─────────────────────────────────────────────────
const slider        = document.getElementById('timeline-slider');
const timelineLabel = document.getElementById('timeline-label');
let   loadedMin = 0, loadedMax = 0;

function updateTimelineLabel(minMs, maxMs) {
    timelineLabel.textContent =
        `${fmtDatetime(minMs)}  –  ${fmtDatetime(maxMs)}`;
}

slider.addEventListener('input', () => {
    if (loadedMax <= loadedMin) return;
    const totalMs  = loadedMax - loadedMin;
    const winMs    = currentWindowMs();
    const fraction = slider.value / 100;
    const startMs  = loadedMin + fraction * (totalMs - winMs);
    const endMs    = startMs + winMs;

    // Pan all charts to the scrubbed position synchronously
    for (const p of Object.values(plots)) {
        p.setScale('x', { min: startMs / 1000, max: endMs / 1000 });
    }

    updateTimelineLabel(startMs, endMs);
    prefetch(startMs, endMs);
});

function currentWindowMs() {
    const sc = plots.ecgI?.scales?.x;
    if (!sc || sc.min == null) return 10_000;
    return (sc.max - sc.min) * 1000;
}

// ── Zoom buttons ──────────────────────────────────────────────────────
document.getElementById('btn-zoom-in').addEventListener('click', () => zoomBy(0.5));
document.getElementById('btn-zoom-out').addEventListener('click', () => zoomBy(2));
document.getElementById('btn-zoom-fit').addEventListener('click', () => {
    if (loadedMax > loadedMin) {
        for (const p of Object.values(plots)) {
            p.setScale('x', { min: loadedMin / 1000, max: loadedMax / 1000 });
        }
        updateTimelineLabel(loadedMin, loadedMax);
        slider.value = 0;
    }
});

function zoomBy(factor) {
    const sc = plots.ecgI?.scales?.x;
    if (!sc || sc.min == null) return;
    const mid   = (sc.min + sc.max) / 2;
    const half  = ((sc.max - sc.min) * factor) / 2;
    const newMin = Math.max(loadedMin / 1000, mid - half);
    const newMax = Math.min(loadedMax / 1000, mid + half);
    for (const p of Object.values(plots)) {
        p.setScale('x', { min: newMin, max: newMax });
    }
    updateTimelineLabel(newMin * 1000, newMax * 1000);
}

// ── Main load ─────────────────────────────────────────────────────────
const btnLoad = document.getElementById('btn-load');
const dtFrom  = document.getElementById('dt-from');
const dtTo    = document.getElementById('dt-to');

btnLoad.addEventListener('click', async () => {
    const fromMs = new Date(dtFrom.value).getTime();
    const toMs   = new Date(dtTo.value).getTime();

    if (!fromMs || !toMs || toMs <= fromMs) {
        setStatus('error', 'Invalid time range — "To" must be after "From".');
        return;
    }
    if (toMs - fromMs > 60 * 60 * 1000) {
        setStatus('error', 'Maximum range is 1 hour at a time.');
        return;
    }

    btnLoad.disabled = true;
    setStatus('loading', 'Fetching waveforms…');
    showAllOverlays('LOADING…');

    try {
        // Fetch all three channel groups in parallel
        const [ecgData, respData, spo2Data] = await Promise.all([
            fetchRange('ecg',  fromMs, toMs),
            fetchRange('resp', fromMs, toMs),
            fetchRange('spo2', fromMs, toMs),
        ]);

        // Initialise (or rebuild) the five uPlot charts
        initPlots();

        // Push data into charts
        setChartData('ecgI',  ecgData.timestamps, ecgData.ecgI);
        setChartData('ecgII', ecgData.timestamps, ecgData.ecgII);
        setChartData('ecgV',  ecgData.timestamps, ecgData.ecgV);
        setChartData('resp',  respData.timestamps, respData.resp);
        setChartData('spo2',  spo2Data.timestamps, spo2Data.spo2);

        loadedMin = fromMs;
        loadedMax = toMs;

        // Set the initial view to the full requested range
        for (const p of Object.values(plots)) {
            p.setScale('x', { min: fromMs / 1000, max: toMs / 1000 });
        }

        updateTimelineLabel(fromMs, toMs);
        slider.value = 0;

        // Start prefetching chunks one step outside the loaded range
        prefetch(fromMs, toMs);

        const totalSamples =
            ecgData.timestamps.length +
            respData.timestamps.length +
            spo2Data.timestamps.length;

        setStatus('ok', `Loaded ${fmtCount(totalSamples)} samples · ${fmtDuration(toMs - fromMs)}`);

    } catch (err) {
        console.error('[History]', err);
        setStatus('error', `Load failed: ${err.message}`);
        showAllOverlays('ERROR — see console');
    } finally {
        btnLoad.disabled = false;
    }
});

// ── Datetime helpers ──────────────────────────────────────────────────
function fmtTime(ms) {
    const d = new Date(ms);
    return d.toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtDatetime(ms) {
    const d = new Date(ms);
    return d.toLocaleString('en-GB', {
        day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
}

function fmtDuration(ms) {
    const s = Math.round(ms / 1000);
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60), rem = s % 60;
    return `${m}m ${rem}s`;
}

function fmtCount(n) {
    return n.toLocaleString();
}

// ── Default the datetime pickers to "last 2 minutes" ─────────────────
(function setDefaultRange() {
    const now   = new Date();
    const from  = new Date(now.getTime() - 2 * 60 * 1000);
    const toISO = s => s.toISOString().slice(0, 19);   // "YYYY-MM-DDTHH:MM:SS"
    dtFrom.value = toISO(from);
    dtTo.value   = toISO(now);
})();

// ── Resize: rebuild plots when the window is resized ─────────────────
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (loadedMax > loadedMin) btnLoad.click();
    }, 300);
});