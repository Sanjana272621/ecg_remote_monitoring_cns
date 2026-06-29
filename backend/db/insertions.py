import psycopg2.extras

psycopg2.extras.register_uuid()

from db.connection import get_connection 
from datetime import datetime, timezone
conn = get_connection()
cur = conn.cursor()

def ensure_patient_exists(cur, pid):
    cur.execute("""
        INSERT INTO PATIENT (ID)
        VALUES (%s)
        ON CONFLICT (ID) DO NOTHING
    """, (str(pid),))

def insert_patient(patient):
    cur = conn.cursor()
    # print(patient)
    # print(type(patient["gender"]), repr(patient["gender"]))
    # print(type(patient["bedno"]), repr(patient["bedno"]))
    recorded_at = datetime.fromtimestamp(
        patient["timestamp"] / 1000,
        tz=timezone.utc
    )

    cur.execute("""
    INSERT INTO PATIENT(
        ID, 
        GENDER,
        NAME,
        RECORDED_AT,
        BEDNO
    )
    VALUES(
        %s,
        %s,
        %s,
        %s,
        %s
    )
    ON CONFLICT(ID) DO NOTHING
    """,
    (
        patient['pid'],
        patient['gender'],
        patient['name'],
        recorded_at,
        patient['bedno'],
    )
    )   
    conn.commit()
    cur.close()

def insert_ecg(ecg):
    cur = conn.cursor()

    recorded_at = datetime.fromtimestamp(
        ecg["timestamp"] / 1000,
        tz=timezone.utc
    )

    ensure_patient_exists(cur, ecg['pid'])

    cur.execute("""
    INSERT INTO ECG(
        PID, 
        RECORDED_AT,
        LEAD_STATUS,
        HRV,
        ARR_TYPE
    )
    VALUES(
        %s,
        %s,
        %s,
        %s,
        %s
    )
    RETURNING ID
    """,
    (
        ecg['pid'],
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
    
    ensure_patient_exists(cur, resp['pid'])

    cur.execute("""
    INSERT INTO RESP(
        PID,
        RECORDED_AT,
        RESP_RATE
    )
    VALUES(%s, %s, %s)
                
    RETURNING ID
    """,
    (   
        resp['pid'],
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

    ensure_patient_exists(cur, spo2['pid'])

    cur.execute("""
    INSERT INTO SPO2(
        PID,
        RECORDED_AT,
        SPO2_VALUE,
        PULSE_RATE,
        ERROR_MSG
    )
    VALUES(%s, %s, %s, %s, %s)
                
    RETURNING ID
    """,
    (   
        spo2['pid'],
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

    ensure_patient_exists(cur, temp['pid'])

    cur.execute("""
    INSERT INTO TEMP(
        PID, 
        RECORDED_AT,
        LEAD_STATUS,
        TEMP1,
        TEMP2
    )
    VALUES(%s, %s, %s, %s, %s)
    """,
    (   
        temp['pid'],
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

    ensure_patient_exists(cur, nibp['pid'])

    cur.execute("""
    INSERT INTO NIBP(
        PID,
        RECORDED_AT,
        SYS,
        MAP,
        DIA,
        ERROR_MSG
    )
    VALUES(%s, %s, %s, %s, %s, %s)
    """,
    (   
        nibp['pid'],
        recorded_at,
        nibp['sys'],
        nibp['map'],
        nibp['dia'],
        nibp['error_msg']
    ))

    conn.commit()
    cur.close()

def rewrite_patient_id(old_id, new_id, since):
    since_dt = datetime.fromtimestamp(since, tz=timezone.utc)
    
    tables = ['ECG', 'RESP', 'SPO2', 'TEMP', 'NIBP']
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"""
                    UPDATE {table}
                    SET PID = %s
                    WHERE PID = %s
                    AND RECORDED_AT >= %s
                """, (str(new_id), str(old_id), since_dt))
    
        conn.commit()