from __future__ import annotations
import asyncio
from collections import OrderedDict
from datetime import datetime, UTC, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from db.queries import (
    select_ecg_waveforms,
    select_resp_waveforms,
    select_spo2_waveforms,  
)

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────
CHUNK_MS  = 30_000   # must match frontend CHUNK_MS constant
CACHE_MAX = 200      # max chunks held in memory (~100 min of history)

# ── Server-side LRU cache ─────────────────────────────────────────────
# Keyed by (channel, chunk_start_ms). Stores the fully-built response
# dict so a repeated request for the same 30-second window skips the DB.
_cache: OrderedDict = OrderedDict()
_cache_lock = asyncio.Lock()


async def _cache_get(key) -> Optional[dict]:
    async with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    return None


async def _cache_set(key, value: dict) -> None:
    async with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)


def ms_to_dt(epoch_ms: int) -> datetime:
    return datetime.fromtimestamp(epoch_ms / 1000.0)


def dt_to_ms(dt: datetime) -> float:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).timestamp() * 1000
    return dt.timestamp() * 1000


# ── Per-sample timestamp interpolation ───────────────────────────────
def interpolate_ts(row_ms: float, n: int, next_ms: Optional[float]) -> list[float]:
    """
    A DB row stores ~N samples recorded between row_ms and next_ms.
    Spread N timestamps evenly across that span.
    If next_ms is unknown (last row), assume a 200 ms span — adjust
    this to your actual device's batch interval if different.
    """
    span = (next_ms - row_ms) if next_ms is not None else 200.0
    if n <= 1:
        return [row_ms]
    step = span / n
    return [row_ms + i * step for i in range(n)]


# ── DB calls wrapped in a threadpool ─────────────────────────────────
# Your query functions are synchronous (psycopg2). Running them directly
# inside an async FastAPI handler would block the event loop. 
# asyncio.to_thread() offloads each call to a worker thread so FastAPI
# stays responsive while the DB query runs.

async def _run_ecg(start_dt: datetime, end_dt: datetime):
    return await asyncio.to_thread(select_ecg_waveforms, start_dt, end_dt)

async def _run_resp(start_dt: datetime, end_dt: datetime):
    return await asyncio.to_thread(select_resp_waveforms, start_dt, end_dt)

async def _run_spo2(start_dt: datetime, end_dt: datetime):
    return await asyncio.to_thread(select_spo2_waveforms, start_dt, end_dt)


# ── Flatten helpers ───────────────────────────────────────────────────
# Your queries now need to also return RECORDED_AT so we can interpolate.
# See the note at the bottom about the small SQL change required.

def _flatten_ecg(rows) -> dict:
    print(f"Row count: {len(rows)}")
    if rows:
        row = rows[0]
        print(f"Row[0] types: {[type(x) for x in row]}")
        print(f"Row[0] values: {row}")
    """
    rows: list of (RECORDED_AT, WAVE1, WAVE2, WAVEV)
    Returns: { timestamps: [...], ecgI: [...], ecgII: [...], ecgV: [...] }
    All timestamps are epoch-ms floats.
    """
    timestamps, ecgI, ecgII, ecgV = [], [], [], []

    for idx, row in enumerate(rows):
        recorded_at, wave1, wave2, wavev = row

        row_ms   = dt_to_ms(recorded_at)
        next_ms  = dt_to_ms(rows[idx + 1][0]) if idx + 1 < len(rows) else None

        samples  = list(wave1)          # WAVE1 is a list/array from the DB
        n        = len(samples)
        ts_list  = interpolate_ts(row_ms, n, next_ms)

        for i, t in enumerate(ts_list):
            timestamps.append(t)
            ecgI.append(float(wave1[i]))
            ecgII.append(float(wave2[i]))
            ecgV.append(float(wavev[i]))

    return {"timestamps": timestamps, "ecgI": ecgI, "ecgII": ecgII, "ecgV": ecgV}


def _flatten_single(rows, field_name: str) -> dict:
    """
    rows: list of (RECORDED_AT, WAVEFORM)
    Returns: { timestamps: [...], <field_name>: [...] }
    """
    timestamps, values = [], []

    for idx, row in enumerate(rows):
        recorded_at, waveform = row

        row_ms  = dt_to_ms(recorded_at)
        next_ms = dt_to_ms(rows[idx + 1][0]) if idx + 1 < len(rows) else None

        samples = list(waveform)
        ts_list = interpolate_ts(row_ms, len(samples), next_ms)

        for i, t in enumerate(ts_list):
            timestamps.append(t)
            values.append(float(samples[i]))

    return {"timestamps": timestamps, field_name: values}


# ── Route ─────────────────────────────────────────────────────────────
@router.get("/history")
async def get_history(
    channel: str = Query(..., pattern="^(ecg|resp|spo2)$"),
    start:   int = Query(..., description="Range start — epoch milliseconds (inclusive)"),
    end:     int = Query(..., description="Range end   — epoch milliseconds (exclusive)"),
):
    """
    Returns flattened per-sample waveform data for a time window.

    The frontend always requests exactly CHUNK_MS (30 s) windows.
    A hard cap of 5 minutes is enforced as a safety valve.

    Response shapes:
      ecg  → { timestamps, ecgI, ecgII, ecgV }
      resp → { timestamps, resp }
      spo2 → { timestamps, spo2 }
    """
    if end <= start:
        raise HTTPException(400, "end must be greater than start")
    if end - start > 5 * 60 * 1000:
        raise HTTPException(400, "Requested window exceeds 5-minute cap")

    # Snap start to chunk boundary so cache keys are consistent
    # (frontend already does this, but defensive here too)
    chunk_start = (start // CHUNK_MS) * CHUNK_MS
    cache_key   = (channel, chunk_start)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached

    start_dt = ms_to_dt(start)
    end_dt   = ms_to_dt(end)

    try:
        if channel == "ecg":
            rows = await _run_ecg(start_dt, end_dt)
            data = _flatten_ecg(rows)

        elif channel == "resp":
            rows = await _run_resp(start_dt, end_dt)
            data = _flatten_single(rows, "resp")

        else:  # spo2
            rows = await _run_spo2(start_dt, end_dt)
            data = _flatten_single(rows, "spo2")

    except Exception as exc:
        raise HTTPException(500, f"Database error: {exc}") from exc

    await _cache_set(cache_key, data)
    return data