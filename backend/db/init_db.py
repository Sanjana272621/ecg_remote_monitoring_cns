import psycopg2 
import os
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv('CONNECTION_STRING')
conn = psycopg2.connect(CONNECTION_STRING)

cur = conn.cursor()

cur.execute("""
CREATE TABLE PATIENT(
    PID INT PRIMARY KEY,
    PNAME VARCHAR(50)
)
""")


cur.execute("""
CREATE TABLE MEASUREMENT_DEFINITIONS(
    CODE VARCHAR(30) PRIMARY KEY,
    NAME VARCHAR(100) NOT NULL,
    UNIT VARCHAR(30)
)
""")

cur.execute("""
CREATE TABLE VITALS(
    VID SERIAL PRIMARY KEY,
    PID INT,
    CODE VARCHAR(30) NOT NULL,
    VALUE FLOAT,
    RECORDED_AT TIMESTAMP,

    FOREIGN KEY (PID)
        REFERENCES PATIENT(PID),

    FOREIGN KEY (CODE)
        REFERENCES MEASUREMENT_DEFINITIONS(CODE)
)
""")

cur.execute("""
CREATE TABLE BATCHED_WAVEFORMS(
    WID SERIAL PRIMARY KEY,
    PID INT,
    WAVEFORM INTEGER[],
    RECORDED_AT TIMESTAMP,
    
    FOREIGN KEY (PID)
        REFERENCES PATIENT (PID)
        
)
""")

#Inserting measurement definitions
#No CO2 Parameter
cur.execute("""
INSERT INTO MEASUREMENT_DEFINITIONS VALUES
('8867-4', 'HEART BEAT', 'bpm'),
('2710-2', 'OXYGEN SATURATION', '%'),
('8889-8', 'Pulse rate', 'bpm'),
('18686-6', 'Respiration rate', 'BrPM'),
('8480-6', 'Systolic blood pressure', 'mmHg'),
('8462-4', 'Diastolic blood pressure', 'mmHg'),
('8478-0', 'Mean blood pressure', 'mmHg'),
('61008-9', 'Body temperature', 'C'),
('76215-3', 'Systolic blood pressure', 'mmHg'),
('76213-8', 'Diastolic blood pressure', 'mmHg'),
('76214-6', 'Mean blood pressure', 'mmHg')
""")

conn.commit()
cur.close()
conn.close()



