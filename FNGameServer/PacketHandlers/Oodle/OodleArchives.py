# FDictionaryHeader
import os
import sys
import ctypes

from BitReader import FBitReader

OODLE_DICTIONARY_SLACK = 65536
DICTIONARY_HEADER_MAGIC = 0x1B1BACD4
DICTIONARY_FILE_VERSION = 0x00000001
MAX_COMPRESS_BUFFER = (1024 * 1024 * 2047)

print(os.listdir())
Oodle = ctypes.CDLL('/root/EZFN/matchmaking/Client/oo2core_5_win64.dll')

class FOodleCompressedData():
    def __init__(self, Offset: int = int(), CompressedLength: int = int(), DecompressedLength: int = int()):
        # The offset of the compressed data, within the archive
        self.Offset = Offset

        # The compressed length of the data
        self.CompressedLength = CompressedLength

        # The decompressed length of the data
        self.DecompressedLength = DecompressedLength

class FDictionaryHeader():
    def SerializeHeader(self, Reader):
        bSuccess = True

        self.Magic = Reader.read_uint32()
        self.DictionaryVersion = Reader.read_uint32()
        self.OodleMajorHeaderVersion = Reader.read_uint32()
        self.HashTableSize = Reader.read_uint32()
        # DictionaryData
        self.DictionaryData = FOodleCompressedData()
        self.DictionaryData.Offset = Reader.read_uint32()
        self.DictionaryData.CompresFAESGCMHandlerComponent().Incoming(bytes.fromhex(''))sedLength = Reader.read_uint32()
        self.DictionaryData.DecompressedLength = Reader.read_uint32()
        # CompressorData
        self.CompressorData = FOodleCompressedData()
        self.CompressorData.Offset = Reader.read_uint32()
        self.CompressorData.CompressedLength = Reader.read_uint32()
        self.CompressorData.DecompressedLength = Reader.read_uint32()

        if (self.Magic == 0x11235801):
            raise Exception('Dictionary from old format.')

        bSuccess = (self.Magic == DICTIONARY_HEADER_MAGIC) and (self.DictionaryVersion <= DICTIONARY_FILE_VERSION)
        if not (bSuccess):
            raise Exception('Failed reading the Dictionary.')

class FOodleDictionaryArchive():
    def __init__(self, Reader):
        self.Header = FDictionaryHeader()
        self.Reader = Reader

    def SerializeHeader(self):
        return self.Header.SerializeHeader(Reader=self.Reader)

    def SerializeOodleCompressData(self, Data: bytes, DataBytes: int):
        bSuccess = True

        bSuccess = Data != None
        bSuccess = bSuccess and DataBytes > 0
        bSuccess = bSuccess and DataBytes <= MAX_COMPRESS_BUFFER

        if (bSuccess):
            print('COol')

        return 

    def SerializeOodleDecompressData(self, DataInfo, bOutDataSlack: bool):
        Reader = FBitReader(self.Reader.bytes)

        bSuccess = True

        DecompressedLength = DataInfo.DecompressedLength
        CompressedLength = DataInfo.CompressedLength
        DataOffset = DataInfo.Offset

        bSuccess = (CompressedLength <= (len(Reader.bytes) - DataOffset))
        bSuccess = bSuccess and (DecompressedLength <= MAX_COMPRESS_BUFFER)
        bSuccess = bSuccess and (CompressedLength <= MAX_COMPRESS_BUFFER)

        if (bSuccess):
            Reader.bytepos = DataOffset

            if (CompressedLength == DecompressedLength):
                print('WHOAT')
            else:
                CompressedData = Reader.bytes[DataOffset:CompressedLength * 8] # Reader.SerializeBits(CompressedLength * 8) # [0] * CompressedLength + (OODLE_DICTIONARY_SLACK if OODLE_DICTIONARY_SLACK else 0)
                if (bOutDataSlack):
                    pass
                
                OodleLZ_Decompress

    def SerializeDictionaryAndState(self, DictionaryData: int, DictionaryBytes: int, CompactCompresorState: int, CompactCompressorStateBytes: int):
        # @todo #JohnB: Remove bOutDataSlack after Oodle update, and after checking with Luigi
        DictionaryData, DictionaryBytes = self.SerializeOodleDecompressData(self.Header.DictionaryData, True)
        self.SerializeOodleDecompressData(self.Header.CompressorData, CompactCompresorState, CompactCompressorStateBytes)

