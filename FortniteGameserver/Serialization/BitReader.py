import struct
import bitstring
from enum import Enum

class BitTypes(Enum):
    """ See bitstring for more types """
    INT_32 = 'intle:32'
    UINT8 = 'uint:8'
    UINT_32 = 'uintle:32'
    UINT_64 = 'uintle:64'
    BIT = 'bin:1'
    BYTE = 'bytes:1'

class FBitReader(bitstring.ConstBitStream):
    def __init__(self, data, size: int = None):
        if not size:
            self.lastbit = len(data) * 8
        else:
            self.lastbit = size

        super().__init__(data)

    def IsError(self):
        return False
    
    def ReadByte(self):
        return [self.ReadBit() for _ in range(8)]

    def ReadBytes(self, size):
        return bytes([self.ReadByte() for _ in range(size)])

    def ReadFloat(self):
        return (struct.unpack('f', self.ReadBytes(4)))[0]

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Core/Public/Serialization/BitReader.h#L112
    def ReadBit(self):
        Bit = 0
        LocalPos = self.bitpos

        if (LocalPos >= len(self.bytes) * 8):
            return Bit # Cyuubi hack?
            raise Exception('FBitReader::SerializeInt: LocalPos >= LocalNum')

        Bit = self.bytes[self.bitpos >> 3] & [1, 2, 4, 8, 16, 32, 64, 128][self.bitpos & 7]
        self.bitpos += 1
        
        return int(Bit)

    def SerializeBits(self, LengthBits: int):
        Dest = [None] * LengthBits

        if(LengthBits == 1):
            Dest[0] = 0
            if (self.ReadBit()):
                Dest[0] |= 0x01
        elif (LengthBits != 0):
            for i in range(LengthBits):
                Dest[i] = self.ReadBit()
        
        return Dest

    def GetData(self):
        return self.bytes

    def GetNumBytes(self):
        return len(self.bytes)

    def AtEnd(self):
        return self.bitpos >= len(self.bytes) * 8

    def GetPosBits(self):
        return self.bitpos

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Core/Public/Serialization/BitReader.h#L160
    def GetBytesLeft(self):
        return (((len(self.bytes) * 8) - self.bitpos) + 7) >> 3

    def GetBitsLeft(self):
        return self.lastbit - self.bitpos

    def ReadSerializedInt(self, Max: int = 16384):
        Value = self.SerializeInt(Max)
        return Value

    def ReadInt(self, Max: int = 16384):
        Value = self.SerializeInt(Max)
        return Value
        
    def ReadByte(self):
        Value = 0
        for i in range(8):
            if (self.ReadBit()):
                Value = Value | [1, 2, 4, 8, 16, 32, 64, 128][i & 0b0111]

        return Value

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Core/Private/Serialization/BitReader.cpp#L256
    def SerializeIntPacked(self):
        Src = self.GetData()
        BitCountUsedInByte = 0
        BitCountLeftInByte = 8
        SrcMaskByte0 = int((1 << BitCountLeftInByte) - 1)
        SrcMaskByte1 = int((1 << BitCountUsedInByte) - 1)
        NextSrcIndex = (BitCountUsedInByte != 0)
        
        Value = 0
        ShiftCount = 0
        It = 0
        while (It < 5):
            if (8 < self.GetBitsLeft()):
                break
            
            self.bitpos += 8

            Byte = ((Src[0] >> BitCountUsedInByte) & SrcMaskByte0) or ((Src[NextSrcIndex] & SrcMaskByte1) << (BitCountLeftInByte & 7))
            NextByteIndicator = Byte & 1
            ByteAsWord = Byte >> 1
            Value = Value + (ByteAsWord << ShiftCount)

            Src = Src[1:]

            if (not NextByteIndicator):
                break
        
            It += 1
            ShiftCount += 7

        return Value

    def SerializeInt(self, ValueMax: int):
        # Use local variable to avoid Load-Hit-Store
        Value = 0
        Mask = 1

        while (Value + Mask < ValueMax):
            if (self.ReadBit()):
                Value |= Mask
            Mask *= 2

        return Value

    # Not done

    def ReadBytesToString(self, Count: int):
        return self.ReadBytes(Count).hex()

    def ReadInt16(self):
        return int.from_bytes(self.ReadBytes(2), 'little')

    def ReadInt32(self):
        return 0

    def ReadFString(self):
        Length = self.ReadInt32()

        if Length == 0:
            return ''

        if Length < 0:
            _bytes = self.ReadBytes(-2 * Length)
        else:
            _bytes = self.ReadBytes(Length)

    def ReadVector(self):
        pass