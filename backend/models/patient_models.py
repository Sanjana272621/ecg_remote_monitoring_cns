from dataclasses import dataclass 
from typing import List, ClassVar

@dataclass
class BasePacket:
    start_byte: ClassVar[int] = 85 #0x55
    end_byte: ClassVar[int] = 170 #0xaa
    checksum: ClassVar[int] = 90 

@dataclass
class Patient(BasePacket):
    module_id: int 
    module_name: str 
    gender: int 
    name: int 
    pid: int
    # date: str 
    bedno: int
    timestamp: int
