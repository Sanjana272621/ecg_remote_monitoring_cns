from db.connection import get_connection 
from datetime import datetime, timezone
conn = get_connection()
cur = conn.cursor()

def insert_ecg(ecg):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        ecg["timestamp"] / 1000,
        tz=timezone.utc
    )
    cur.execute("""
    INSERT INTO ECG(
        RECORDED_AT,
        LEAD_STATUS,
        HRV,
        ARR_TYPE
    )
    VALUES(
        %s,
        %s,
        %s,
        %s
    )
    RETURNING ID
    """,
    (
        recorded_at,
        ecg['lead_status'],
        ecg['hrv'],
        ecg['arr_type']
    ))

    ecg_id = cur.fetchone()[0]

    cur.execute("""
    INSERT INTO ECG_WAVEFORM(
        ECG_ID,
        RECORDED_AT,
        WAVE1,
        WAVE2,
        WAVEV
    )
    VALUES(%s, %s, %s, %s, %s)
    """,
    (
        ecg_id,
        recorded_at,
        ecg['wave1'],
        ecg['wave2'],
        ecg['waveV']
    ))

    conn.commit()
    cur.close()

def insert_resp(resp):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        resp["timestamp"] / 1000,
        tz=timezone.utc
    )
    
    cur.execute("""
    INSERT INTO RESP(
        RECORDED_AT,
        RESP_RATE
    )
    VALUES(%s, %s)
                
    RETURNING ID
    """,
    (
        recorded_at,
        resp['resp_rate']
    ))

    resp_id = cur.fetchone()[0]

    cur.execute("""
    INSERT INTO RESP_WAVEFORM(
        RESP_ID,
        RECORDED_AT,
        WAVEFORM
    )
    VALUES(%s, %s, %s)
    """,
    (
        resp_id,
        recorded_at,
        resp['wave']
    ))

    conn.commit()
    cur.close()

def insert_spo2(spo2):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        spo2["timestamp"] / 1000,
        tz=timezone.utc
    )
    cur.execute("""
    INSERT INTO SPO2(
        RECORDED_AT,
        SPO2_VALUE,
        PULSE_RATE,
        ERROR_MSG
    )
    VALUES(%s, %s, %s, %s)
                
    RETURNING ID
    """,
    (
        recorded_at,
        spo2['spo2_val'],
        spo2['pr'],
        spo2['error_msg']
    ))

    spo2_id = cur.fetchone()[0]

    cur.execute("""
    INSERT INTO SPO2_WAVEFORM(
        SPO2_ID,
        RECORDED_AT,
        WAVEFORM
    )
    VALUES(%s, %s, %s)
    """,
    (
        spo2_id,
        recorded_at,
        spo2['wave']
    ))

    conn.commit()
    cur.close()

def insert_temp(temp):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        temp["timestamp"] / 1000,
        tz=timezone.utc
    )

    cur.execute("""
    INSERT INTO TEMP(
        RECORDED_AT,
        LEAD_STATUS,
        TEMP1,
        TEMP2
    )
    VALUES(%s, %s, %s, %s)
    """,
    (
        recorded_at,
        temp['lead_status'],
        temp['temp1'],
        temp['temp2']
    ))

    conn.commit()
    cur.close()

def insert_nibp(nibp):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        nibp["timestamp"] / 1000,
        tz=timezone.utc
    )
    cur.execute("""
    INSERT INTO NIBP(
        RECORDED_AT,
        SYS,
        MAP,
        DIA,
        ERROR_MSG
    )
    VALUES(%s, %s, %s, %s, %s)
    """,
    (
        recorded_at,
        nibp['sys'],
        nibp['map'],
        nibp['dia'],
        nibp['error_msg']
    ))

    conn.commit()
    cur.close()