from ..Serialization import FBitReader
from .StatelessConnectHandlerComponent import StatelessConnectHandlerComponent

class PacketHandler():
    def __init__(self):
        self.HandlerComponents = [StatelessConnectHandlerComponent()] # TODO: AESGCMHandlerComponent, OodleHandlerComponent

        self.bError = False
    
    # Processes incoming packets at the PacketHandler level, before any UNetConnection processing takes place on the packet.
    # Use this for more complex changes to packets, such as compression/encryption,
    # but be aware that compatibility problems with other HandlerComponent's are more likely.
    async def Incoming(self, Packet: bytes, CountBytes: int, bConnectionless: bool, Address: str):
        CountBits = CountBytes * 8

        if (len(self.HandlerComponents) > 0):
            LastByte = Data[-1]
            
            if (LastByte != 0):
                CountBits -= 1
                
                # Bit streaming, starts at the Least Significant Bit, and ends at the MSB.
                while (not (LastByte & 0x80)):
                    LastByte *= 2
                    CountBits -= 1
            else:
                self.bError = True

            if not (self.bError):
                ProcessedPacketReader = FBitReader(PacketHandler, size = CountBits)

                for CurComponent in self.HandlerComponents:
                    # Realign the packet, so the packet data starts at position 0, if necessary
                    if (ProcessedPacketReader.GetPosBits() != 0 and not CurComponent.CanReadUnaligned()):
                        pass # RealignPacket(ProcessedPacketReader)
                
                    if (bConnectionless):
                        await PacketHandler.Incoming(Reader, self.remote_addr, self.socket)
                    else:
                        await PacketHandler.Incoming(Reader, self.remote_addr, self.socket)