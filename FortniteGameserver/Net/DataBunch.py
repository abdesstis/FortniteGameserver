from enum import Enum
from ..UObject import FNetBitWriter
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

class FOutBunch:
    def __init__(self, *args, **kwargs):
        self.Next = None
        self.Channel = None
        self.Time = 0
        self.ReceivedAck = False
        self.ChIndex = 0
        self.ChType = 0
        self.ChSequence = 0
        self.PacketId = 0
        self.bOpen = 0
        self.bClose = 0
        self.bDormant = 0
        self.bIsReplicationPaused = 0
        self.bReliable = 0
        self.bPartial = 0
        self.bPartialInitial = 0
        self.bPartialFinal = 0
        self.bHasPackageMapExports = 0
        self.bHasMustBeMappedGUIDs = 0

        if kwargs.get('InChannel') and kwargs.get('bInClose'):
            InChannel = kwargs['InChannel']
            bInClose = kwargs['bInClose']

            self.FNetBitWriter = FNetBitWriter(InChannel.Connection.PackageMap, InChannel.Connection.GetMaxSingleBunchSizeBits())

            self.ChIndex = InChannel.ChIndex
            self.ChType = InChannel.ChType
            self.bClose = bInClose

            # Match the byte swapping settings of the connection
            # TODO: SetByteSwapping(Channel->Connection->bNeedsByteSwapping);

        elif kwargs.get('InPackageMap') and kwargs.get('MaxBits'):
            self.FNetBitWriter = FNetBitWriter(kwargs.get('InPackageMap'), kwargs.get('MaxBits'))
    
    def GetNumBits(self):
        return 0

# https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/DataBunch.cpp#L138
class FControlChannelOutBunch(FOutBunch):
    def __init__(self, *args, **kwargs):
        # control channel bunches contain critical handshaking/synchronization and should always be reliable
        self.bReliable = True
        super().__init__(*args, **kwargs)