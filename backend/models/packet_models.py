#dataclasses for each packet type 
#no standard packet lengths since it is taking from buffer written by main board

from dataclasses import dataclass
from typing import List, ClassVar

@dataclass
class Parameter:
    start_byte: ClassVar[int] = 85 #0x55
    end_byte: ClassVar[int] = 170 #0xaa
    checksum: ClassVar[int] = 90 

@dataclass 
class Ecg(Parameter):
    module_id: int #defaults in every ecg packet
    module_name: str
    lead_status: int
    hrv: int
    arr_type: int
    wave1: List[int]
    wave2: List[int]
    waveV: List[int]

@dataclass 
class Resp(Parameter):
    module_id: int
    module_name: str
    resp_rate: int 
    wave: List[int]
    

@dataclass
class Spo2(Parameter):
    module_id: int
    module_name: str
    spo2_val: int 
    pr: int
    wave: List[int]
    error_msg: int

@dataclass
class Temp(Parameter):
    module_id: int
    module_name: str
    lead_status: int
    temp1: float
    temp2: float

@dataclass
class Nibp(Parameter):
    module_id: int
    module_name: str
    sys: int
    map: int
    dia: int
    error_msg: int



