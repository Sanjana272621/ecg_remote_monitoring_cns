from db.connection import get_connection 
from datetime import datetime, timezone


def select_ecg_waveforms(start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(
        start_timestamp / 1000,
        tz=timezone.utc)
    end_dt = datetime.fromtimestamp(
        end_timestamp / 1000,
        tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT RECORDED_AT, WAVE1, WAVE2, WAVEV 
            FROM ECG_WAVEFORM
            WHERE 
                ECG_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                ECG_WAVEFORM.RECORDED_AT    
            """,
            (start_dt, end_dt))
            output = cur.fetchall()
            print("ECG WAVEFORM RETURNED!!", output)
            return output

def select_resp_waveforms(start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(
        start_timestamp / 1000,
        tz=timezone.utc)
    end_dt = datetime.fromtimestamp(
        end_timestamp / 1000,
        tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT RECORDED_AT, WAVEFORM
            FROM RESP_WAVEFORM
            WHERE 
                RESP_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                RESP_WAVEFORM.RECORDED_AT    
            """,
            (start_dt, end_dt))
            return cur.fetchall()

def select_spo2_waveforms(start_timestamp, end_timestamp):
    start_dt = datetime.fromtimestamp(
        start_timestamp / 1000,
        tz=timezone.utc)
    end_dt = datetime.fromtimestamp(
        end_timestamp / 1000,
        tz=timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT RECORDED_AT, WAVEFORM 
            FROM SPO2_WAVEFORM
            WHERE 
                SPO2_WAVEFORM.RECORDED_AT BETWEEN %s AND %s
            ORDER BY
                SPO2_WAVEFORM.RECORDED_AT    
            """,
            (start_dt, end_dt))
            return cur.fetchall()
        
