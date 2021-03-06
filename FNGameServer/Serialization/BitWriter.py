import struct
from bitarray import bitarray

# Not good at all...
# https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Core/Private/Serialization/BitWriter.cpp#L21
class FBitWriter():
    def __init__(self, InMaxBits: int, InAllowResize: bool = False):
        self.bitpos = 0
        self.bits = [0] * InMaxBits

    def WriteBit(self, In: int):
        self.bits[self.bitpos] = In
        self.bitpos += 1
    
    def WriteByte(self, byte: int):
        for bit in ''.join(reversed(bin(byte)[2:].zfill(8))):
            self.WriteBit(int(bit))

    def WriteBytes(self, Src: bytes):
        for byte in Src:
            self.WriteByte(byte)

    def WriteFloat(self, In: int):
        self.WriteBytes(struct.pack('f', In))

    def WriteInt(self, In: int):
        self.WriteBytes(struct.pack('i', In))

    def GetData(self):
        return bitarray(''.join([str(bit) for bit in self.bits]), endian='little').tobytes()

    def WriteIntWrapped(self, Value: int, ValueMax: int):
        if not ValueMax >= 2:
            return
        
        # LengthBits = FMath::CeilLogTwo(ValueMax);

        NewValue = 0
        Mask = 1
        while (NewValue + Mask < Value and Mask):
            if (Value & Mask):
                self.WriteBit(1)
                NewValue += Mask
            Mask *= 2