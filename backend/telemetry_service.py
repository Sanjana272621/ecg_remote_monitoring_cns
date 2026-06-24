from circular_buffer import CircularBuffer
from vitals_buffer import VitalsBuffer 
import db.insertions
import db.queries
from enum import IntEnum
import logging 

logging.basicConfig(level=logging.INFO)
#1782225000000  1782225854841
#1782226800000

ecg_waveformI_buffer = CircularBuffer(5000)
ecg_waveformII_buffer = CircularBuffer(5000)
ecg_waveformV_buffer = CircularBuffer(5000)
resp_waveform_buffer = CircularBuffer(500)
spo2_waveform_buffer = CircularBuffer(500)

ecg_vitals_buffer = VitalsBuffer()
resp_vitals_buffer = VitalsBuffer()
spo2_vitals_buffer = VitalsBuffer()
temp_vitals_buffer = VitalsBuffer()
nibp_vitals_buffer = VitalsBuffer()

class ModuleID(IntEnum):
    ECG = 11
    RESP = 14
    NIBP = 15
    SPO2 = 16
    TEMP = 13
    PATIENT = 23

def view_buffers():
    print("Vitals Buffer: ")
    view = ecg_vitals_buffer.get()
    if view:
        print(view)

    print("Waveform Buffers: ")

    print(ecg_waveformI_buffer.get_window(10))
    print(ecg_waveformII_buffer.get_window(10))
    print(ecg_waveformV_buffer.get_window(10))
    print(resp_waveform_buffer.get_window(5))
    print(spo2_waveform_buffer.get_window(5))

def clear_buffers():
    ecg_waveformI_buffer.clear(60)
    ecg_waveformII_buffer.clear(60)
    ecg_waveformV_buffer.clear(60)
    resp_waveform_buffer.clear(25)
    spo2_waveform_buffer.clear(15)

#fastapi should get from here
def get_latest_ecgI_waveform():
    data = ecg_waveformI_buffer.get_latest(60)

    return data
    
def get_latest_ecgII_waveform():
    return ecg_waveformII_buffer.get_latest(60)

def get_latest_ecgV_waveform():
    return ecg_waveformV_buffer.get_latest(60)

def get_latest_resp_waveform():
    return resp_waveform_buffer.get_latest(25)

def get_latest_spo2_waveform():
    return spo2_waveform_buffer.get_latest(15)

def get_ecg_vitals():
    return ecg_vitals_buffer.get()

def get_resp_vitals():
    return resp_vitals_buffer.get()

def get_spo2_vitals():
    return spo2_vitals_buffer.get()

def get_temp_vitals():
    return temp_vitals_buffer.get()

def get_nibp_vitals():
    return nibp_vitals_buffer.get()

def realtime_storage(data):
    module_id = data['module_id']
    timestamp = data['timestamp']

    match module_id:

        case ModuleID.ECG:
            ecg_waveformI_buffer.update(data['wave1'])
            ecg_waveformII_buffer.update(data['wave2'])
            ecg_waveformV_buffer.update(data['waveV'])

            ecg_vitals_buffer.update({
                "lead_status": data['lead_status'],
                "hrv": data['hrv'],
                "arr_type": data['arr_type'],
                "timestamp": timestamp
            })

        case ModuleID.RESP:
            resp_waveform_buffer.update(data['wave'])

            resp_vitals_buffer.update({
                "resp_rate": data['resp_rate'],
                "timestamp": timestamp
            })

        case ModuleID.SPO2:
            spo2_waveform_buffer.update(data['wave'])

            spo2_vitals_buffer.update({
                "spo2_val": data['spo2_val'],
                "pr": data['pr'],
                "error_msg": data['error_msg'],
                "timestamp": timestamp
            })

        case ModuleID.TEMP:
            temp_vitals_buffer.update({
                "lead_status": data['lead_status'],
                "temp1": str(data['temp1'])[0:4],
                "temp2": str(data['temp2'])[0:4],
                "timestamp": timestamp
            })

        case ModuleID.NIBP:
            nibp_vitals_buffer.update({
                "sys": data['sys'],
                "map": data['map'],
                "dia": data['dia'],
                "error_msg": data['error_msg'],
                "timestamp": timestamp
            })
            
def persistent_storage(data):
    #for data in data_list:
    module_id = data['module_id']

    match module_id:
        case ModuleID.ECG:
            db.insertions.insert_ecg(data)
        case ModuleID.RESP:
            db.insertions.insert_resp(data)
        case ModuleID.SPO2:
            db.insertions.insert_spo2(data)
        case ModuleID.NIBP:
            db.insertions.insert_nibp(data)
        case ModuleID.TEMP:
            db.insertions.insert_temp(data)
