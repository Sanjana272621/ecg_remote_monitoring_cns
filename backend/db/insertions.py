from db.connection import get_connection 

conn = get_connection()
cur = conn.cursor()

def insert_vitals(pid, vitals, timestamp):
    for code, data in vitals.items():
        cur.execute("""
        INSERT INTO VITALS(
            PID,
            CODE,
            VALUE,
            RECORDED_AT
        )
        VALUES (%s, %s, %s, TO_TIMESTAMP(%s, 'YYYYMMDDHH24MISS'))
        """,
        (
            pid,
            code,
            data["value"],
            timestamp
        ))

    conn.commit()

def insert_patient(pid, pname = None):
    cur.execute("""
    INSERT INTO PATIENT(PID, PNAME)
    VALUES (%s, %s)
    ON CONFLICT (PID) DO NOTHING
    """,
    (pid, pname))

    conn.commit()

def insert_measurement_definition(code, name, unit):
    cur.execute("""
    INSERT INTO MEASUREMENT_DEFINITIONS(
        CODE,
        NAME,
        UNIT
    )
    VALUES (%s, %s, %s)
    """,
    (code, name, unit))

    conn.commit()

def insert_waveform(pid, waveform, timestamp):
    cur.execute("""
    INSERT INTO BATCHED_WAVEFORMS(
        PID,
        WAVEFORM,
        RECORDED_AT)
    VALUES(%s, %s, TO_TIMESTAMP(%s, 'YYYYMMDDHH24MISS'))
    """, (pid, waveform, timestamp)
    )

    conn.commit()


