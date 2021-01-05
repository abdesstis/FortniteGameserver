import os
from ..Serialization import FBitReader, FBitWriter

# https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/PacketHandlers/StatelessConnectHandlerComponent.cpp#L122
HANDSHAKE_PACKET_SIZE_BITS = 194

class StatelessConnectHandlerComponent():
    def __init__(self):
        self.ActiveSecret = 0 # 255?
    
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/PacketHandlers/StatelessConnectHandlerComponent.cpp#L410
    async def Incoming(self, Packet: FBitReader, remote_addr: tuple, socket):
        bHandshakePacket = Packet.ReadBit() == 1

        if (bHandshakePacket):
            bHandshakePacket, SecretId, Timestamp, Cookie = self.ParseHandshakePacket(Packet)

            if (bHandshakePacket):
                bInitialConnect = int(Timestamp) == 0

                if bInitialConnect:
                    await self.SendConnectChallenge(SecretId, Timestamp, Cookie, remote_addr, socket)
                # Challenge response
                else:
                    # Cyuubi
                    await self.SendAck(Cookie, remote_addr, socket)
            else:
                pass # UE_LOG(LogHandshake, Log, TEXT("IncomingConnectionless: Error reading handshake packet."));
        else:
            pass # UE_LOG(LogHandshake, Log, TEXT("IncomingConnectionless: Error reading handshake bit from packet."));

    def CapHandshakePacket(self, HandshakePacket: FBitWriter):
        if (True): # TODO: HandshakePacket.GetNumBits() == HANDSHAKE_PACKET_SIZE_BITS:
            # Add a termination bit, the same as the UNetConnection code does
            HandshakePacket.WriteBit(1)

    def CanReadUnaligned(self):
        return True

    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/PacketHandlers/StatelessConnectHandlerComponent.cpp#L208
    async def SendConnectChallenge(self, SecretId: int, Timestamp: float, Cookie: bytes, remote_addr: tuple, socket):
        ChallengePacket = FBitWriter(HANDSHAKE_PACKET_SIZE_BITS + 1) # Termination bit
        bHandshakePacket = 1
        Timestamp = 1.0 # (Driver != nullptr ? Driver->Time : -1.f)
        Cookie = self.GenerateCookie('', SecretId, Timestamp) # TODO: ClientAddress

        ChallengePacket.WriteBit(bHandshakePacket)
        ChallengePacket.WriteBit(self.ActiveSecret)

        ChallengePacket.WriteFloat(Timestamp)
        ChallengePacket.WriteBytes(Cookie)

        # UE_LOG( LogHandshake, Log, TEXT( "SendConnectChallenge. Timestamp: %f, Cookie: %s" ), Timestamp, *FString::FromBlob( Cookie, ARRAY_COUNT( Cookie ) ) );

        self.CapHandshakePacket(ChallengePacket)

        await socket.send(ChallengePacket.GetData(), remote_addr)

    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/PacketHandlers/StatelessConnectHandlerComponent.cpp#L477
    def ParseHandshakePacket(self, Packet: FBitReader):
        bValidPacket = False

        # Only accept handshake packets of precisely the right size
        if (Packet.GetBitsLeft() == (HANDSHAKE_PACKET_SIZE_BITS - 1)):
            OutSecretId = Packet.ReadBit()
            OutTimestamp = Packet.ReadFloat()
            OutCookie = Packet.ReadBytes(20)

            bValidPacket = True
            return bValidPacket, OutSecretId, OutTimestamp, OutCookie
        
        return bValidPacket, 0, 1.0, bytes([0] * 20)

    def GenerateCookie(self, ClientAddress: str, SecretId: str, Timestamp: float):
        # CookieArc << Timestamp;
        # CookieArc << ClientAddress;
        # TODO: FSHA1::HMACBuffer(HandshakeSecret[!!SecretId].GetData(), SECRET_BYTE_SIZE, CookieData.GetData(), CookieData.Num(), OutCookie);
        CookieData = os.urandom(20)
        return CookieData

    # Cyuubi
    async def SendAck(self, cookie: bytes, remote_addr: tuple, socket):
        Writer = FBitWriter(HANDSHAKE_PACKET_SIZE_BITS + 1)
        bHandshakePacket = 1

        Writer.WriteBit(bHandshakePacket)
        Writer.WriteBit(0)

        Writer.WriteFloat(-1.0)
        Writer.WriteBytes(cookie) # TOOD: 

        self.CapHandshakePacket(Writer)

        await socket.send(Writer.GetData(), (remote_addr[0], remote_addr[1]))