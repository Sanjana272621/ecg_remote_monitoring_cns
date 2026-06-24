from db.connection import get_connection 


def select_ecg_waveforms(start_timestamp, end_timestamp):
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
            (start_timestamp, end_timestamp))
            output = cur.fetchall()
            print("ECG WAVEFORM RETURNED!!", output)
            return output

def select_resp_waveforms(start_timestamp, end_timestamp):
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
            (start_timestamp, end_timestamp))
            return cur.fetchall()

def select_spo2_waveforms(start_timestamp, end_timestamp):
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
            (start_timestamp, end_timestamp))
            return cur.fetchall()
