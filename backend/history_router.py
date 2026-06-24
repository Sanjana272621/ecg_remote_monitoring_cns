# history_router.py
from fastapi import APIRouter, Query, HTTPException
from db import queries

router = APIRouter()

CHUNK_DURATION_MS = 10_000  # 10 seconds per chunk


@router.get("/ecg_history")
def get_ecg_history(
    start: float = Query(..., description="Unix timestamp ms"),
    end: float   = Query(..., description="Unix timestamp ms"),
):
    try:
        rows = queries.select_ecg_waveforms(start, end)
        # with open("history_log.txt", "a") as file:
        #     file.write("timestamp: " + str(rows[0][0]) + type(rows[0][0]) + "\n")
        return [
            {
                "timestamp": row[0].timestamp() * 1000,  # → ms
                "ecgI":  row[1],  # list of ~33 samples
                "ecgII": row[2],
                "ecgV":  row[3],
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resp_history")
def get_resp_history(
    start: float = Query(...),
    end:   float = Query(...),
):
    try:
        rows = queries.select_resp_waveforms(start, end)
        return [
            {"timestamp": row[0].timestamp() * 1000, "waveform": row[1]}
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spo2_history")
def get_spo2_history(
    start: float = Query(...),
    end:   float = Query(...),
):
    try:
        rows = queries.select_spo2_waveforms(start, end)
        return [
            {"timestamp": row[0].timestamp() * 1000, "waveform": row[1]}
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    