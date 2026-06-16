from circular_buffer import CircularBuffer
from vitals_buffer import VitalsBuffer 
import db.insertions

waveform_buffer = CircularBuffer(1000000)
vitals_buffer = VitalsBuffer()

def view_buffers():
    print("Vitals Buffer: ")
    view = vitals_buffer.view()
    if view:
        print(view)

    print("Waveform Buffer: ")
    window = waveform_buffer.get_window()
    print(window)

#fastapi should get from here
def get_latest_waveform():
    return waveform_buffer.get_latest()

def get_vitals():
    return vitals_buffer.get()
    

def realtime_storage(parsed):
    if parsed["vitals"]:
        vitals_buffer.update(parsed["vitals"], parsed["timestamp"])

    if parsed["waveform"]:
        waveform_buffer.enqueue(parsed["waveform"])
    

def persistent_storage(parsed):
    db.insertions.insert_patient(parsed["PID"])
    if parsed["vitals"]:
        db.insertions.insert_vitals(parsed["PID"], parsed["vitals"], parsed["timestamp"])

    if parsed["waveform"]:
        db.insertions.insert_waveform(parsed["PID"], parsed["waveform"], parsed["timestamp"])