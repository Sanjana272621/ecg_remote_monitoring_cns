from ..models.packet_models import Ecg, Resp, Spo2, Temp, Nibp 

def to_big_endian_int(data):
    if len(data) == 1:
        return int(data[0])
    
    high = data[1]
    low = data[0]
    dec_output = int((high << 8) + low)

    return dec_output - 65536 if dec_output >= 32768 else dec_output

def ecg_parser(bin_packet, dec_packet_length):

    lead_status = to_big_endian_int(bin_packet[4:6])
    heart_rate = to_big_endian_int(bin_packet[6:8])
    arr_type = to_big_endian_int(bin_packet[8:12])
    
    #waveforms_bytes = bin_packet[28: -2]
    wave1 = []
    wave2 = []
    waveV = []
    waveforms_length = dec_packet_length - 30

    for i in range(28, 28+int(waveforms_length/3), 4):
        dec_sample = to_big_endian_int(bin_packet[i: i+4])
        wave1.append(dec_sample)
    
    for i in range(28+int(waveforms_length/3), 28+2*int(waveforms_length/3), 4):
        dec_sample = to_big_endian_int(bin_packet[i: i+4])
        wave2.append(dec_sample)

    for i in range(28+2*int(waveforms_length/3), 28+waveforms_length, 4):
        dec_sample = to_big_endian_int(bin_packet[i: i+4])
        waveV.append(dec_sample)

    return(Ecg(
        module_id = 11,
        module_name = "ecg",
        lead_status = lead_status,
        hrv = heart_rate,
        arr_type = arr_type,
        wave1 = wave1,
        wave2 = wave2,
        waveV = waveV
    ))

def resp_parser(bin_packet, dec_packet_length):
    resp_rate = to_big_endian_int(bin_packet[4:6])
    
    waveform_length = dec_packet_length - 8
    wave = []
    for i in range(8, 8+waveform_length, 4):
        dec_sample = to_big_endian_int(bin_packet[i: i+4])
        wave.append(dec_sample)

    return(Resp(
        module_id = 14,
        module_name = "resp",
        resp_rate = resp_rate,
        wave = wave
    ))

def spo2_parser(bin_packet, dec_packet_length):
    spo2_val = to_big_endian_int(bin_packet[4:5])
    pr = to_big_endian_int(bin_packet[5:7])
    wave = []
    waveform_length = dec_packet_length - 16

    for i in range(16, 16+waveform_length, 4):
        dec_sample = to_big_endian_int(bin_packet[i: i+4])
        wave.append(dec_sample)

    error_msg = to_big_endian_int(bin_packet[13:14])

    return(Spo2(
        module_id = 16,
        module_name = "spo2",
        spo2_val = spo2_val,
        pr = pr,
        wave = wave,
        error_msg = error_msg
    ))

def nibp_parser(bin_packet, dec_packet_length):
    sys = to_big_endian_int(bin_packet[4:6])
    map = to_big_endian_int(bin_packet[6:8])
    dia = to_big_endian_int(bin_packet[8:10])
    error_msg = to_big_endian_int(bin_packet[11:12])

    return(Nibp(
        module_id= 15,
        module_name = "nibp", 
        sys = sys,
        map = map,
        dia = dia,
        error_msg = error_msg
    ))

def temp_parser(bin_packet, dec_packet_length):
    lead_status = to_big_endian_int(bin_packet[4:5])
    temp1_val = to_big_endian_int(bin_packet[5:7]) * 0.1
    temp2_val = to_big_endian_int(bin_packet[7:9]) *0.1

    return(Temp(
        module_id = 13,
        module_name = "temp",
        lead_status = lead_status,
        temp1 = temp1_val,
        temp2 = temp2_val
    ))

def patient_parser(bin_packet, dec_packet_length):
    gender = to_big_endian_int(bin_packet[8:10])
    name = to_big_endian_int(bin_packet[10:12])
    pid = to_big_endian_int(bin_packet[12:14])
    date = str(to_big_endian_int(bin_packet[14:16])) + str(to_big_endian_int(bin_packet[16:18])) + str(to_big_endian_int(bin_packet[18:20]))
    bedno = to_big_endian_int(bin_packet[20:22])
    

    

