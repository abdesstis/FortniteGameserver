from enum import Enum
from ..Serialization import FBitReader
    
# A bunch of data received from a channel.
# https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Public/Net/DataBunch.h
class FInBunch(FBitReader): # FNetBitReader
    def __init__(self):
        self.bError = False

        self.PacketId = 0

        self.ChIndex = None
        self.ChSequence = None
    
    def ToString(self):
        return f'Channel[{self.ChIndex}]. Seq {self.ChSequence}. PacketId: {self.PacketId}'

    def GetPosBits(self):
        return 0

    def GetData(self):
        pass
    
    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Core/Public/Serialization/Archive.h#L1091
	# Serializes an unsigned 8-bit integer value from or into an archive.
        # @param Ar The archive to serialize from or to.
        # @param Value The value to serialize.
    def Serialize(self, Value):
        pass

    def IsError(self):
        return self.bError
    
    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Core/Private/Serialization/BitReader.cpp#L177
    def SetData(self, Reader, CountBits: int):
        if (CountBits > (len(Reader.bytes) * 8) - Reader.bitpos):
            raise ('Not enough data')
        
        super().__init__(data = Reader.ReadBytes((len(Reader.bytes) * 8 - Reader.bitpos) >> 3))