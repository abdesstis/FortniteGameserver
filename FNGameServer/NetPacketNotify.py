from .BitReader import FBitReader

class FNotificationHeader():
    def __init__(self):
        self.History = ''
        self.HistoryWordCount = ''
        self.Seq = ''
        self.AckedSeq = ''

class FNetPacketNotify():
    def __init__(self):
        self.WrittenHistoryWordCount = 0
        self.AckRecord = 64
        self.InSeq = 0
        self.OutSeq = 64

        self.SequenceNumberBits = 14
        self.MaxSequenceHistoryLength = 256

        self.SequenceNumberT = []
        self.SequenceHistoryT = []

        # FPackedHeader
        self.HistoryWordCountBits = 4
        self.SeqMask = (1 << self.SequenceNumberBits) - 1
        self.HistoryWordCountMask = (1 << self.HistoryWordCountBits) - 1
        self.AckSeqShift = self.HistoryWordCountBits
        self.SeqShift = self.AckSeqShift + self.SequenceNumberBits
    
    # FPackedHeader
    def SequenceNumberT(self, Packed: int):
        # we have not written a header...this is a fail.
        if (self.WrittenHistoryWordCount != 0):
            return

        # Add entry to the ack-record so that we can update the InAckSeqAck when we received the ack for this OutSeq.
        self.AckRecord.append({self.OutSeq: WrittenInAckSeq})
        self.WrittenHistoryWordCount = 0

        self.OutSeq += 1
        return self.OutSeq

    def GetSeq(self, Packed: int):
        return self.SequenceNumberT(Packed >> self.SeqShift and self.SeqMask)

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/Net/NetPacketNotify.cpp#L142
    def ReadHeader(self, Data: FNotificationHeader, Reader: FBitReader):
        # Read packed header
        PackedHeader = Reader.read_uint32()

        # Unpack
        Data.Seq = FPackedHeader().GetSeq(PackedHeader)

        print(Data.Seq)