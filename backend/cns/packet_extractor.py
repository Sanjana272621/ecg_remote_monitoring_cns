#if stop byte seen AND current byte = 55, then starrt new packet
#else 55 is a random value encountered
from enum import IntEnum
from .parser import ecg_parser, resp_parser, spo2_parser, nibp_parser, temp_parser

class ModuleID(IntEnum):
    ECG = 0x11
    RESP = 0x14
    NIBP = 0x15
    SPO2 = 0x16
    TEMP = 0x13
    PATIENT = 0x23

start_byte = b'\x55'
end_byte = b'\xaa'

def packet_extractor(client_socket, buffer):
    with client_socket:
        while True:
            data = client_socket.recv(4096)
            buffer.extend(data)

            if not data:
                print("CONNECTION DISCONNECTED!!!!")
                break

            try:
                start_ptr = start_ptr = buffer.find(0x55)

                if start_ptr == -1:
                    print("no start byte found!")
                    continue
                
                if len(buffer) > start_ptr+2:
                    binary_packet_length_high = buffer[start_ptr+2] #recieved stream is according to little endian
                    binary_packet_length_low = buffer[start_ptr+1]
                    dec_packet_length = int(((binary_packet_length_high << 8) + binary_packet_length_low))
                    
                else:
                    break 

                while (start_ptr + dec_packet_length) <= len(buffer):
                    bin_packet = buffer[start_ptr: start_ptr+dec_packet_length]

                    #route to each parser
                    module_id = bin_packet[3]
                    
                    match module_id:
                        case ModuleID.ECG:
                            ecg_data = ecg_parser(bin_packet, dec_packet_length)
                            yield(ecg_data)
                        case ModuleID.RESP:
                            resp_data = resp_parser(bin_packet, dec_packet_length)
                            yield(resp_data)
                        case ModuleID.NIBP:
                            nibp_data = nibp_parser(bin_packet, dec_packet_length)
                            yield(nibp_data)
                        case ModuleID.SPO2:
                            spo2_data = spo2_parser(bin_packet, dec_packet_length)
                            yield(spo2_data)
                        case ModuleID.TEMP:
                            temp_data = temp_parser(bin_packet, dec_packet_length)
                            yield(temp_data)
                        case ModuleID.PATIENT:
                            print("PATIENT DATA")
                    
                    del buffer[:start_ptr + dec_packet_length] #modify buffer in place
                    start_ptr = 0

                    if len(buffer) > start_ptr+2:
                        binary_packet_length_high = buffer[start_ptr+2] #recieved stream is according to little endian
                        binary_packet_length_low = buffer[start_ptr+1]
                        dec_packet_length = int(((binary_packet_length_high << 8) + binary_packet_length_low))
                        
                    else:
                        break
                
            except Exception as e:

                print("Decode Error:", e)
                
    return data, buffer

