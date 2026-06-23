from db.connection import get_connection 

conn = get_connection()
cur = conn.cursor()

def select_ecg_waveforms(start_timestamp, end_timestamp):
    cur = conn.cursor()

    cur.execute("""
    SELECT RECORDED_AT, WAVE1, WAVE2, WAVEV 
    FROM ECG_WAVEFORM
    WHERE 
        ECG_WAVEFORM.RECORDED_AT BETWEEN ? AND ?
    ORDER BY
        ECG_WAVEFORM.RECORDED_AT    
    """,
    (start_timestamp, end_timestamp))

    rows = cur.fetchall()
    
    cur.close()

    return rows

def select_resp_waveforms(start_timestamp, end_timestamp):
    cur = conn.cursor()

    cur.execute("""
    SELECT RECORDED_AT, WAVEFORM
    FROM RESP_WAVEFORM
    WHERE 
        RESP_WAVEFORM.RECORDED_AT BETWEEN ? AND ?
    ORDER BY
        RESP_WAVEFORM.RECORDED_AT    
    """,
    (start_timestamp, end_timestamp))

    rows = cur.fetchall()
    
    cur.close()

    return rows

def select_spo2_wavefors(start_timestamp, end_timestamp):
    cur = conn.cursor()

    cur.execute("""
    SELECT RECORDED_AT, WAVEFORM 
    FROM SPO2_WAVEFORM
    WHERE 
        SPO2_WAVEFORM.RECORDED_AT BETWEEN ? AND ?
    ORDER BY
        SPO2_WAVEFORM.RECORDED_AT    
    """,
    (start_timestamp, end_timestamp))

    rows = cur.fetchall()
    
    cur.close()

    return rows
