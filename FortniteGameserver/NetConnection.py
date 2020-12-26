from .Serialization import FBitReader
from .PacketHandlers import *

StatelessConnectHandlerComponent = StatelessConnectHandlerComponent()

class UNetConnection():
    def __init__(self, socket, remote_addr: tuple, InMaxPacket: int = 1, InPacketOverhead: int = 1):
        self.socket = socket
        self.remote_addr = remote_addr

        # Use the passed in values
        self.MaxPacket = InMaxPacket
        self.PacketOverhead = InPacketOverhead

        if not (self.MaxPacket > 0) or not (self.PacketOverhead > 0):
            raise Exception('InMaxPacket and InPacketOverhead must be greater than 0')

        self.InBytes = 0
        self.OutBytes = 0
        self.InTotalBytes = 0
        self.OutTotalBytes = 0
        self.InPackets = 0
        self.OutPackets = 0
        self.InTotalPackets = 0
        self.OutTotalPackets = 0

        self.InBytesPerSecond = 0
        self.OutBytesPerSecond = 0
        self.InPacketsPerSecond	= 0
        self.OutPacketsPerSecond = 0

        self.InitHandler()
    
    def InitHandler(self):
        self.HandlerComponents = [StatelessConnectHandlerComponent] # TODO: AESGCMHandlerComponent, OodleHandlerComponent

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L1186
    async def ReceivedRawPacket(self, Data: bytes, Count: int):
        # Handle an incoming raw packet from the driver.
        # UE_LOG(LogNetTraffic, Verbose, TEXT("%6.3f: Received %i"), FPlatformTime::Seconds() - GStartTime, Count );
        PacketBytes = Count # TODO: + self.PacketOverhead
        self.InBytes += PacketBytes
        self.InTotalBytes += PacketBytes
        self.InPackets += 1
        self.InTotalPackets += 1

        if (Count > 0):
            LastByte = Data[-1]
            
            if (LastByte != 0):
                BitSize = (Count * 8) - 1
                
                # Bit streaming, starts at the Least Significant Bit, and ends at the MSB.
                while (not (LastByte & 0x80)):
                    LastByte *= 2
                    BitSize -= 1

                Reader = FBitReader(Data, size = BitSize)
                
                # TODO: Set the network version on the reader
			    # Reader.SetEngineNetVer( EngineNetworkProtocolVersion );
			    # Reader.SetGameNetVer( GameNetworkProtocolVersion );

                for PacketHandler in self.HandlerComponents:
                    await PacketHandler.Incoming(Reader, self.remote_addr, self.socket)
                
                if (Reader.GetBitsLeft() > 0):
                    await self.ReceivedPacket(Reader)
                    
                # Check if the out of order packet cache needs flushing
				# TODO: FlushPacketOrderCache()
            else:
                raise Exception('MalformedPacket - Received a packet with 0\'s in the last byte')
        else:
            raise Exception('MalformedPacket - Received a packet of 0 bytes')

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L2016
    async def ReceivedPacket(self, Reader: FBitReader, bIsReinjectedPacket: bool = False):
        pass