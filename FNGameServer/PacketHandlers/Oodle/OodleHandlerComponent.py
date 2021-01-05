from stream_reader import ConstBitStreamWrapper
from .OodleArchives import FOodleDictionaryArchive, FOodleCompressedData
from BitReader import FBitReader

class FortniteOodleDictionary():
    def __init__(self):
        self.HashTableSize = 17
        self.DictionaryData = FOodleCompressedData(
            Offset = 40,
            CompressedLength = 146696,
            DecompressedLength = 1048576
        )

# Encapsulates Oodle dictionary data loaded from file, to be wrapped in a shared pointer (auto-deleting when no longer in use)
class FOodleDictionary():
    def __init__(self):
        # Size of the hash table used for the dictionary
        self.HashTableSize = int()
        
        # The raw dictionary data
        DictionaryData = bytes()
        
        # The size of the dictionary
        DictionarySize = int()
        
        # Shared dictionary state
        SharedDictionary = None # OodleNetwork1_Shared
        
        # The size of the shared dictionary data (stored only for memory accounting)
        SharedDictionarySize = int()
        
        # The uncompacted compressor state
        CompressorState = None # OodleNetwork1UDP_State
        
        # The size of CompressorState
        CompressorStateSize = int()

class OodleHandlerComponent():
    def __init__(self):
        self.DictionaryRef = None
        self.bInitializedDictionaries = False

        self.ServerDictionaryPath = 'FortniteGameOutput.udic'
        self.ClientDictionaryPath = 'FortniteGameInput.udic'

        self.ClientDictionary = None
        self.ServerDictionary = None

    def InitializeDictionary(self, FilePath: str):
        # Load the dictionary, if it's not yet loaded
        if (self.DictionaryRef == None):
            # FOodleDictionaryArchive BoundArc(*ReadArc);
            BoundArc = FOodleDictionaryArchive(
                Reader = ConstBitStreamWrapper(open(FilePath, 'rb').read())
            )

            self.DictionaryData = 0
            self.DictionaryBytes = 0
            self.CompactCompressorState = 0
            self.CompactCompressorStateBytes = 0

            BoundArc.SerializeHeader()
            BoundArc.SerializeDictionaryAndState(self.DictionaryData, self.DictionaryBytes, self.CompactCompressorState, self.CompactCompressorStateBytes)

            print('Loading dictionary file...')
            
            # Uncompact the compressor state
            CompressorStateSize = 3060736 # OodleNetwork1UDP_State_Size()

            # Create the shared dictionary state
            SharedDictionarySize = 1048608 # OodleNetwork1_Shared_Size(HashTableSize)
            SharedDictionary = None

            print(DictionaryBytes)
            print(CompactCompressorState)

            SharedDictionary = None

    def InitializeDictionaries(self):
        self.InitializeDictionary(self.ServerDictionaryPath)
        self.InitializeDictionary(self.ClientDictionaryPath)

    def Incoming(self, InData: bytes):
        Packet = FBitReader(InData)
        if (True): # bEnableOodle
            bCompressedPacket = Packet.ReadBit()
            
            # If the packet is not compressed, no further processing is necessary
            if (bCompressedPacket):
                bIsServer = False # (Handler->Mode == Handler::Mode::Server)

            # Lazy-loading of dictionary when EOodleEnableMode::WhenCompressedPacketReceived is active
            if (not self.bInitializedDictionaries):
                self.InitializeDictionaries()

            CurDict = self.ClientDictionary # (bIsServer ? ClientDictionary.Get() : ServerDictionary.Get());
            
            BeforeDecompressedLength = Packet.GetBytesLeft()
            DecompressedLength = Packet.ReadInt(1024 * 2)

            print(BeforeDecompressedLength)
            print(f'DecompressedLength: {DecompressedLength}')

            if (DecompressedLength < 16384): # MAX_OODLE_PACKET_BYTES
                DecompressedData = []
                CompressedLength = Packet.GetBytesLeft()
                CompressedData = Packet.SerializeBits(CompressedLength)
                if (True): # bSuccess
                    pass # OodleNetwork1UDP_Decode(DecompressedLength)

        return InData

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Plugins/Runtime/PacketHandlers/CompressionComponents/Oodle/Source/OodleHandlerComponent/Private/OodleHandlerComponent.cpp#L149
    def SerializeOodlePacketSize(self, Reader: FBitReader):
        # @todo #JohnB: Restore when serialize changes are stable
        # Reader.NetSerializeInt<MAX_OODLE_PACKET_BYTES>(OutPacketSize);

        # @todo #JohnB: Remove when restoring the above
        OutPacketSize = Reader.SerializeInt(MAX_OODLE_PACKET_BYTES)
        
        # if (!Reader.IsError()):
        if (True):
            OutPacketSize += 1

        return OutPacketSize