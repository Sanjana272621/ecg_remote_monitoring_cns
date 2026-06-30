import psycopg2.extras

psycopg2.extras.register_uuid()

from db.connection import get_connection 
from datetime import datetime, timezone

def get_all_patients():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT ID, NAME, BEDNO
            FROM PATIENT
            ORDER BY RECORDED_AT
            """)
            rows = cur.fetchall()

    result = []
    unknown_count = 0
    for pid, name, bedno in rows:
        if not name:
            unknown_count += 1
            name = f"Unknown_{unknown_count}"
        result.append((pid, name, bedno))
    return result

def select_ecg_waveforms(patient_id, start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT ECG_WAVEFORM.RECORDED_AT, WAVE1, WAVE2, WAVEV
            FROM ECG_WAVEFORM
            JOIN ECG ON ECG_WAVEFORM.ECG_ID = ECG.ID
            WHERE
                ECG.PID = %s
                AND ECG_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                ECG_WAVEFORM.RECORDED_AT
            """,
            (patient_id, start_dt, end_dt))
            return cur.fetchall()


def select_resp_waveforms(patient_id, start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT RESP_WAVEFORM.RECORDED_AT, WAVEFORM
            FROM RESP_WAVEFORM
            JOIN RESP ON RESP_WAVEFORM.RESP_ID = RESP.ID
            WHERE
                RESP.PID = %s
                AND RESP_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                RESP_WAVEFORM.RECORDED_AT
            """,
            (patient_id, start_dt, end_dt))
            return cur.fetchall()


def select_spo2_waveforms(patient_id, start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT SPO2_WAVEFORM.RECORDED_AT, WAVEFORM
            FROM SPO2_WAVEFORM
            JOIN SPO2 ON SPO2_WAVEFORM.SPO2_ID = SPO2.ID
            WHERE
                SPO2.PID = %s
                AND SPO2_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                SPO2_WAVEFORM.RECORDED_AT
            """,
            (patient_id, start_dt, end_dt))
            return cur.fetchall()