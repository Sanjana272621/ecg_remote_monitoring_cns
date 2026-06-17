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

LOG_FILE = 'cns_capture.bin'
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
                    print("MODULE ID: ", module_id, type(module_id))
                    with open("cns_capture.txt", "a") as file:
                        match module_id:
                            case ModuleID.ECG:
                                ecg_data = ecg_parser(bin_packet, dec_packet_length)
                                file.write(f"{ecg_data}\n")
                                yield(ecg_data)
                            case ModuleID.RESP:
                                resp_data = resp_parser(bin_packet, dec_packet_length)
                                file.write(f"{resp_data}\n")
                                yield(resp_data)
                            case ModuleID.NIBP:
                                nibp_data = nibp_parser(bin_packet, dec_packet_length)
                                file.write(f"{nibp_data}\n")
                                yield(nibp_data)
                            case ModuleID.SPO2:
                                spo2_data = spo2_parser(bin_packet, dec_packet_length)
                                file.write(f"{spo2_data}\n")
                                yield(spo2_data)
                            case ModuleID.TEMP:
                                temp_data = temp_parser(bin_packet, dec_packet_length)
                                file.write(f"{temp_data}\n")                     
                                yield(temp_data)
                            case ModuleID.PATIENT:
                                print("PATIENT DATA")
                                file.write("THIS IS PATIENT DATA!")
                                file.write(str(bin_packet.hex()))

                    with open("module_log.txt", "a") as f:
                        f.write(f"{module_id}\n")
                    print("Opening log file!")
                    with open(LOG_FILE, "ab") as file:
                        #file.write("NEW MESSAGE! LENGTH = " + str(len(data)) + "\n")
                        if module_id == ModuleID.PATIENT:
                            file.write(bin_packet) 
                            file.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                        

                    with open("cns_verify.txt", "a") as file:
                        hex_data = str(bin_packet.hex())

                        for i in range(0, len(hex_data), 2):
                            file.write(hex_data[i: i+2])
                            file.write(" ")

                        file.write("\n\n\n")
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

