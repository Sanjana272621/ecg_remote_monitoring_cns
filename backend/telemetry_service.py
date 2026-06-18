from circular_buffer import CircularBuffer
from vitals_buffer import VitalsBuffer 
import db.insertions
from enum import IntEnum

ecg_waveformI_buffer = CircularBuffer(100000)
ecg_waveformII_buffer = CircularBuffer(100000)
ecg_waveformV_buffer = CircularBuffer(100000)
resp_waveform_buffer = CircularBuffer(10000)
spo2_waveform_buffer = CircularBuffer(10000)

ecg_vitals_buffer = VitalsBuffer()
resp_vitals_buffer = VitalsBuffer()
spo2_vitals_buffer = VitalsBuffer()
temp_vitals_buffer = VitalsBuffer()
nibp_vitals_buffer = VitalsBuffer()

class ModuleID(IntEnum):
    ECG = 0x11
    RESP = 0x14
    NIBP = 0x15
    SPO2 = 0x16
    TEMP = 0x13
    PATIENT = 0x23

def view_buffers():
    print("Vitals Buffer: ")
    view = ecg_vitals_buffer.view()
    if view:
        print(view)

    print("Waveform Buffers: ")

    print(ecg_waveformI_buffer.get_window())
    print(ecg_waveformII_buffer.get_window())
    print(ecg_waveformV_buffer.get_window())
    print(resp_waveform_buffer.get_window())
    print(spo2_waveform_buffer.get_window())

#fastapi should get from here
def get_latest_ecgI_waveform():
    return ecg_waveformI_buffer.get_latest()

def get_latest_ecgII_waveform():
    return ecg_waveformII_buffer.get_latest()

def get_latest_ecgV_waveform():
    return ecg_waveformV_buffer.get_latest()

def get_latest_resp_waveform():
    return resp_waveform_buffer.get_latest()

def get_latest_spo2_waveform():
    return spo2_waveform_buffer.get_latest()

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
                "temp1": data['temp1'],
                "temp2": data['temp2'],
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
