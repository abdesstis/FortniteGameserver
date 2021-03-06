from .Serialization import FBitReader, FBitWriter
from .PacketHandlers import *

from .Classes import EChannelType
from .UObject import EChannelCloseReason
from .Misc import EEngineNetworkVersionHistory
from .Net import FInBunch, FOutBunch

from .World import UWorld
from .Net import UChannel, UControlChannel
from .PackageMapClient import UPackageMapClient

StatelessConnectHandlerComponent = StatelessConnectHandlerComponent()

# Types # https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Classes/Engine/NetConnection.h#L51
MAX_CHSEQUENCE = 1024 # Power of 2 >RELIABLE_BUFFER, covering loss/misorder time.

# UE4.16 (https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Classes/Engine/NetConnection.h#L220)
MAX_CHANNELS = 10240 # Maximum channels. TODO: This needs to differ per game somehow but cannot with shared executable

# UE4.16
MAX_BUNCH_HEADER_BITS = 64

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

        self.OutBunches = 0

        self.InPacketId = 0

        self.QueuedBits = 0

        self.InBytesPerSecond = 0
        self.OutBytesPerSecond = 0
        self.InPacketsPerSecond	= 0
        self.OutPacketsPerSecond = 0

        self.InitHandler()
        self.InitTick()
        self.InitBase()
        self.InitUnknown()

        # .-.
        self.World = UWorld()

    def InitBase(self):
        # Create package map.
        PackageMapClient = UPackageMapClient(self)
        self.PackageMap = PackageMapClient

    def InitHandler(self):
        self.HandlerComponents = [StatelessConnectHandlerComponent] # TODO: AESGCMHandlerComponent, OodleHandlerComponent

    def InitTick(self):
        # TODO: Run self.Tick in the background

        # The channels that need ticking. This will be a subset of OpenChannels, only including
        # channels that need to process either dormancy or queued bunches. Should be a significant
        # optimization over ticking and calling virtual functions on the potentially hundreds of
        # OpenChannels every frame.
        self.ChannelsToTick = []

    def InitUnknown(self):
        # Not good yet :/
        self.InReliable = [0] * MAX_CHSEQUENCE # NOTE: This is wrong and makes no sense...
        self.Channels = [None] * MAX_CHANNELS
        self.OpenChannels = []
        self.bResendAllDataSinceOpen = False

    def IsInternalAck(self) -> bool:
        return False

    def EngineNetVer(self) -> int:
        # TODO: Parse almost all using https://github.com/EZFNDEV/FortLogReader
        return 2 # Season 1.8
        return 16 # Season 14.60

    # The maximum number of bits allowed within a single bunch.
    def GetMaxSingleBunchSizeBits(self) -> int:
        # TODO: Fix self.MaxPacket
        return 8000000
        # return (MaxPacket * 8) - MAX_BUNCH_HEADER_BITS - MAX_PACKET_TRAILER_BITS - MAX_PACKET_HEADER_BITS - MaxPacketHandlerBits

    async def Tick(self, DeltaSeconds: float):
        # Pretend everything was acked, for 100% reliable connections or demo recording.
        if (self.IsInternalAck()):
            OutAckPacketId = 0 # TODO: OutAckPacketId
        
            for i in range(len(self.OpenChannels)):
                It = self.OpenChannels[i]

                # for( FOutBunch* OutBunch=It->OutRec; OutBunch; OutBunch=OutBunch->Next )
                # {
                #     OutBunch->ReceivedAck = 1;
                # }

                It.OpenAcked = 1

                await It.ReceivedAcks()
                i -= 1

        if (False):
            pass
        else:
            # We should never need more ticking channels than open channels
            if (len(self.ChannelsToTick) <= len(self.OpenChannels)):
                print(f'More ticking channels ({len(self.ChannelsToTick)}) than open channels ({len(self.OpenChannels)}) for net connection!')
            
            # Tick the channels.

    # NOTE: We are in the wrong class, this function should be in UChannel
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L1068
    def IsKnownChannelType(self, Type) -> bool:
        if isinstance(Type, EChannelType):
            Type = Type.value

        return Type >= 0 and Type < EChannelType.CHTYPE_MAX.value # and ChannelClasses[Type]

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
        if (self.IsInternalAck()):
            self.InPacketId += 1
        else:
            # TODO: Read packet header
            pass

        if (self.EngineNetVer() == 2):
            # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L828
            if (self.IsInternalAck()):
                PacketId = self.InPacketId + 1
            else:
                PacketId = Reader.ReadInt()

            self.InPacketId = PacketId

        # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L2260
        # Disassemble and dispatch all bunches in the packet.
        while (not Reader.AtEnd()):
            # Parse the bunch.
            StartPos = Reader.GetPosBits()

            # For demo backwards compatibility, old replays still have this bit
            # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L861
            if (self.EngineNetVer() < EEngineNetworkVersionHistory.HISTORY_ACKS_INCLUDED_IN_HEADER.value):
                IsAck = Reader.ReadBit()
                # Process the bunch.
                if (IsAck):
                    # This is an acknowledgment.
                    AckPacketId = Reader.ReadInt()

                    ServerFrameTime = 0
                    
                    # If this is the server, we're reading in the request to send them our frame time
                    # If this is the client, we're reading in confirmation that our request to get frame time from server is granted
                    bHasServerFrameTime = not(not(Reader.ReadBit()))
                    
                    # We never actually read it for shipping

                    # Doesnt work good
                    if Reader.GetBitsLeft() < 0:
                        continue

                    RemoteInKBytesPerSecond = Reader.SerializeIntPacked()

                    # Resend any old reliable packets that the receiver hasn't acknowledged.
                    OutAckPacketId = 0 # TODO: Fix
                    if(AckPacketId > OutAckPacketId):
                        pass
                    
                    continue
                    # TODO: Continue https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L909
            
            # Process Received data
            Bunch = FInBunch()
            Bunch.IncomingStartPos = Reader.GetPosBits()
            Bunch.bControl = Reader.ReadBit()
            Bunch.bOpen = Reader.ReadBit() if Bunch.bControl else 0
            Bunch.bClose = Reader.ReadBit() if Bunch.bControl else 0

            if (self.EngineNetVer() < EEngineNetworkVersionHistory.HISTORY_CHANNEL_CLOSE_REASON.value):
                Bunch.bDormant = Reader.ReadBit() if Bunch.bClose else 0
                Bunch.CloseReason = EChannelCloseReason.Dormancy.value if Bunch.bDormant else EChannelCloseReason.Destroyed.value
            else:
                Bunch.CloseReason = Reader.ReadInt(EChannelCloseReason.Destroyed.value) if Bunch.bClose else EChannelCloseReason.Destroyed.value 
                Bunch.bDormant = (Bunch.CloseReason == EChannelCloseReason.Dormancy.value)
            
            Bunch.bIsReplicationPaused = Reader.ReadBit()
            Bunch.bReliable = Reader.ReadBit()

            if (self.EngineNetVer() < EEngineNetworkVersionHistory.HISTORY_MAX_ACTOR_CHANNELS_CUSTOMIZATION.value):
                OLD_MAX_ACTOR_CHANNELS = 10240
                Bunch.ChIndex = Reader.ReadInt(OLD_MAX_ACTOR_CHANNELS)
            else:
                ChIndex = Reader.SerializeIntPacked()

                # const int32 UNetConnection::DEFAULT_MAX_CHANNEL_SIZE = 32767;
                MaxChannelSize = 32767
                if (ChIndex >= int(MaxChannelSize)):
                    raise 'Bunch channel index exceeds channel limit'
                
                Bunch.ChIndex = ChIndex
                
            Bunch.bHasPackageMapExports	= Reader.ReadBit()
            Bunch.bHasMustBeMappedGUIDs	= Reader.ReadBit()
            Bunch.bPartial = Reader.ReadBit()

            if (Bunch.bReliable):
                if (self.IsInternalAck()):
                    # We can derive the sequence for 100% reliable connections
                    Bunch.ChSequence = self.InReliable[Bunch.ChIndex] + 1
                else:
                    # If this is a reliable bunch, use the last processed reliable sequence to read the new reliable sequence
                    Bunch.ChSequence = Reader.ReadInt(MAX_CHSEQUENCE)
            elif (Bunch.bPartial):
                # If this is an unreliable partial bunch, we simply use packet sequence since we already have it
                Bunch.ChSequence = self.InPacketId
            else:
                Bunch.ChSequence = 0

            Bunch.bPartialInitial = Reader.ReadBit() if Bunch.bPartial else 0
            Bunch.bPartialFinal = Reader.ReadBit() if Bunch.bPartial else 0

            if (self.EngineNetVer() < EEngineNetworkVersionHistory.HISTORY_CHANNEL_NAMES.value):
                Bunch.ChType =  Reader.ReadInt(EChannelType.CHTYPE_MAX.value) if (Bunch.bReliable or Bunch.bOpen) else 0 # EChannelType.CHTYPE_None
                if (Bunch.ChType == EChannelType.CHTYPE_Control.value):
                    Bunch.ChName = EChannelType.CHTYPE_Control
                elif (Bunch.ChType == EChannelType.CHTYPE_Voice.value):
                    Bunch.ChName = EChannelType.CHTYPE_Voice
                elif (Bunch.ChType == EChannelType.CHTYPE_Actor.value):
                    Bunch.ChName = EChannelType.CHTYPE_Actor
            else:
                if (Bunch.bReliable or Bunch.bOpen):
                    Bunch.ChType =  Reader.ReadSerializedInt(EChannelType.CHTYPE_MAX.value) if (Bunch.bReliable or Bunch.bOpen) else 0 # EChannelType.CHTYPE_None

                    if (Bunch.ChType == EChannelType.CHTYPE_Control.value):
                        Bunch.ChName = EChannelType.CHTYPE_Control
                    elif (Bunch.ChType == EChannelType.CHTYPE_Voice.value):
                        Bunch.ChName = EChannelType.CHTYPE_Voice
                    elif (Bunch.ChType == EChannelType.CHTYPE_Actor.value):
                        Bunch.ChName = EChannelType.CHTYPE_Actor
                else:
                    Bunch.ChType = EChannelType.CHTYPE_None
                    Bunch.ChName = EChannelType.NAME_None

            BunchDataBits = Reader.ReadInt(1024  * 8)
            HeaderPos = Reader.GetPosBits()

            # Bunch claims it's larger than the enclosing packet.
            if (BunchDataBits > ((len(Reader.bytes) * 8) - Reader.bitpos)):
                # print(f'Bunch data overflowed ({Bunch.IncomingStartPos} {HeaderPos}+{BunchDataBits}/{len(Reader.bytes) * 8})')
                return

            Bunch.SetData(Reader, BunchDataBits)

            if (Bunch.bHasPackageMapExports):
                NetGUIDInBytes = (BunchDataBits + (HeaderPos - Bunch.IncomingStartPos)) >> 3
                print(f'NetGUIDInBytes: {NetGUIDInBytes}') # TODO: Remove, just need this for testing

            if(Bunch.bReliable):
                print(f"Reliable Bunch, Channel {Bunch.ChIndex} Sequence {Bunch.ChSequence}: Size %.1f+%.1f") # , , (HeaderPos-IncomingStartPos)/8.f, (Reader.GetPosBits()-HeaderPos)/8.f );
            else:
                print(f"Unreliable Bunch, Channel %i: Size %.1f+%.1f") # , Bunch.ChIndex, (HeaderPos-IncomingStartPos)/8.f, (Reader.GetPosBits()-HeaderPos)/8.f );
            
            if (Bunch.bOpen):
                print(f"bOpen Bunch, Channel {Bunch.ChIndex} Sequence {Bunch.ChSequence}: Size %.1f+%.1f") # , , , (HeaderPos-IncomingStartPos)/8.f, (Reader.GetPosBits()-HeaderPos)/8.f );

            # Receiving data.

            # We're on a 100% reliable connection and we are rolling back some data.
            # In that case, we can generally ignore these bunches.
            if (False):
                pass # TODO
            
            # Ignore if reliable packet has already been processed.
            if (Bunch.bReliable and Bunch.ChSequence <= self.InReliable[Bunch.ChIndex]):
                print(f"UNetConnection::ReceivedPacket: Received outdated bunch (Channel {Bunch.ChIndex} Current Sequence {self.InReliable[Bunch.ChIndex]})")
                if (not self.IsInternalAck()): # Should be impossible with 100% reliable connections
                    return
            
            Channel = None

            # If opening the channel with an unreliable packet, check that it is "bNetTemporary", otherwise discard it
            if(not Channel and not Bunch.bReliable):
                # Unreliable bunches that open channels should be bOpen && (bClose || bPartial)
                # NetTemporary usually means one bunch that is unreliable (bOpen and bClose):	1(bOpen, bClose)
                # But if that bunch export NetGUIDs, it will get split into 2 bunches:			1(bOpen, bPartial) - 2(bClose).
                # (the initial actor bunch itself could also be split into multiple bunches. So bPartial is the right check here)

                ValidUnreliableOpen = Bunch.bOpen and (Bunch.bClose or Bunch.bPartial)
                if (not ValidUnreliableOpen):
                    if (self.IsInternalAck()):
                        # Should be impossible with 100% reliable connections
                        print(f'Received unreliable bunch before open with reliable connection (Channel {Bunch.ChIndex} Current Sequence {self.InReliable[Bunch.ChIndex]})')
                    else:
                        # Simply a log (not a warning, since this can happen under normal conditions, like from a re-join, etc)
                        print(f'Received unreliable bunch before open (Channel {Bunch.ChIndex} Current Sequence {self.InReliable[Bunch.ChIndex]})')
                    
                    # Since we won't be processing this packet, don't ack it
					# We don't want the sender to think this bunch was processed when it really wasn't
                    bSkipAck = True
                    continue

            # Create channel if necessary.
            if (Channel == None):
                # Validate channel type.
                if (not self.IsKnownChannelType(Bunch.ChType)):
                    # Unknown type.
                    print(f'UNetConnection::ReceivedPacket: Connection unknown channel type ({Bunch.ChType})')
                    return

                # Reliable (either open or later), so create new channel.
                print(f'Bunch Create {Bunch.ChIndex}: ChType {Bunch.ChType}, bReliable: {Bunch.bReliable}, bPartial: {Bunch.bPartial}, bPartialInitial: {Bunch.bPartialInitial}, bPartialFinal: {Bunch.bPartialFinal}')
                
                if (self.EngineNetVer() == 2):
                    Channel = self.CreateChannel(Bunch.ChType, True, Bunch.ChIndex)
                else:
                    Channel = self.CreateChannelByName(None, Bunch.ChIndex) # EChannelCreateFlags::None
                    
            # Notify the server of the new channel.
            if (not True): # !Driver->Notify->NotifyAcceptingChannel( Channel )
                pass

            # Dispatch the raw, unsequenced bunch to the channel.
            bLocalSkipAck = False
            if (Channel == None):
                raise 'Something went wrong while creating a channel :/'
            await Channel.ReceivedRawBunch(Bunch, bLocalSkipAck) # warning: May destroy channel.
            if (bLocalSkipAck):
                bSkipAck = True
    
    # UE 4.16
    def CreateChannel(self, ChType: EChannelType, bOpenedLocally: bool, ChIndex: int) -> UChannel:
        if not (self.IsKnownChannelType(ChType)):
            return
        
        # TODO: Make sure this connection is in a reasonable state.

        # If no channel index was specified, find the first available.
        if (ChIndex == -1): # INDEX_NONE	= -1
            FirstChannel = 1
            # Control channel is hardcoded to live at location 0
            if (ChType == EChannelType.CHTYPE_Control):
                FirstChannel = 0

            # If this is a voice channel, use its predefined channel index
            if (ChType == EChannelType.CHTYPE_Voice):
                FirstChannel = 1 # VOICE_CHANNEL_INDEX = 1

            # Search the channel array for an available location
            ChIndex = FirstChannel
            while (ChIndex < 10240): # MAX_CHANNELS =  10240
                if (self.Channels[ChIndex] == None):
                    break
                ChIndex += 1

            # Fail to create if the channel array is full
            if (ChIndex == 10240): # MAX_CHANNELS =  10240
                return

        # Make sure the channel is valid.
        if not (ChIndex < 10240):
            return
        if not (self.Channels[ChIndex] == None):
            pass

        # Create channel.
        # Only UControlChannel atm
        Channel = UControlChannel(self, ChIndex, bOpenedLocally, ChType)

        self.Channels[ChIndex] = Channel
        self.OpenChannels.append(Channel)
        # Always tick the control & voice channels
        if (Channel.ChType == EChannelType.CHTYPE_Control or Channel.ChType == EChannelType.CHTYPE_Voice.value):
            self.StartTickingChannel(Channel)

        print(f'Created channel {ChIndex} of type {ChType}')
        return Channel

    def StartTickingChannel(self, Channel: UChannel):
        # Adds the channel to the ticking channels list. Used to selectively tick channels that have queued bunches or are pending dormancy.
        self.ChannelsToTick.append(Channel)

    def CreateChannelByName(self, CreateFlags, ChIndex: int) -> UChannel: # TODO: EChannelCreateFlags CreateFlags
        raise Exception('Not supported yet.')
    
    async def SendPackageMap(self):
        pass
            
    # https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L3054
    async def SendRawBunch(self, Bunch: FOutBunch, InAllowMerge: bool, BunchCollector = None) -> int:
        if Bunch.ReceivedAck:
            return
        self.OutBunches += 1
        TimeSensitive = 1

        # Build header.
        Header = FBitWriter(MAX_BUNCH_HEADER_BITS)
        
        # Tried to make it a packet but it didnt work, if you anyone can fix this I would be happy :)
        Header.WriteBit(0) # No handshake packet
        Header.WriteInt(self.InPacketId)
        Header.WriteBit(0) # bcontrol
        Header.WriteBit(0) # IsAck


        Header.WriteBit(Bunch.bOpen or Bunch.bClose)
        if (Bunch.bOpen or Bunch.bClose):
            pass # TODO: Add this (Didnt need it yet)
        Header.WriteBit(Bunch.bIsReplicationPaused)
        Header.WriteBit(Bunch.bReliable)
        Header.WriteIntWrapped(Bunch.ChIndex, MAX_CHANNELS)
        Header.WriteBit(Bunch.bHasPackageMapExports)
        Header.WriteBit(Bunch.bHasMustBeMappedGUIDs)
        Header.WriteBit(Bunch.bPartial)
        
        if (Bunch.bReliable and not self.IsInternalAck()):
            Header.WriteIntWrapped(Bunch.ChSequence, MAX_CHSEQUENCE)

        if (Bunch.bPartial):
            Header.WriteBit(Bunch.bPartialInitial)
            Header.WriteBit(Bunch.bPartialFinal)

        if (Bunch.bReliable or Bunch.bOpen):
            Header.WriteIntWrapped(Bunch.ChType, EChannelType.CHTYPE_MAX.value)
        
        Header.WriteIntWrapped(Bunch.GetNumBits(), 1024 * 8)

        await self.socket.send(Header.GetData(), self.remote_addr)
        # Remember start position.
        AllowMerge = InAllowMerge
        # TODO: Bunch.Time      = Driver->Time;

        # if ((Bunch.bClose || Bunch.bOpen) && UE_LOG_ACTIVE(LogNetDormancy,VeryVerbose) )
        # {
        #     UE_LOG(LogNetDormancy, VeryVerbose, TEXT("Sending: %s"), *Bunch.ToString());
        # }

        # if (UE_LOG_ACTIVE(LogNetTraffic,VeryVerbose))
        # {
        #     UE_LOG(LogNetTraffic, VeryVerbose, TEXT("Sending: %s"), *Bunch.ToString());
        # }
    
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L1234
    async def WriteBitsToSendBuffer(self, Bits, SizeInBits, ExtraBits, ExtraSizeInBits):
        # ValidateSendBuffer()

        TotalSizeInBits = SizeInBits + ExtraSizeInBits

        # Flush if we can't add to current buffer
        # if (TotalSizeInBits > GetFreeSendBufferBits()):
        #     FlushNet()

        # Remember start position in case we want to undo this write
        # Store this after the possible flush above so we have the correct start position in the case that we do flush

    def ReadPacketInfo(self, Reader: FBitReader, bHasPacketInfoPayload: bool):
        # If this packet did not contain any packet info, nothing else to read
        if (bHasPacketInfoPayload == False):
            return True # bCanContinueReading

        bHasServerFrameTime = Reader.ReadBit() == 1
        ServerFrameTime = 0.0
        
        if (bHasServerFrameTime):
            # FrameTimeByte = 0
			# Reader << FrameTimeByte
            FrameTimeByte = 0
            # As a client, our request was granted, read the frame time
            ServerFrameTime = FrameTimeByte / 1000
        
        if (self.EngineNetVer() < EEngineNetworkVersionHistory.HISTORY_JITTER_IN_HEADER.value):
            RemoteInKBytesPerSecondByte = 0
            Reader << RemoteInKBytesPerSecondByte
        
        # Update ping
        # At this time we have updated OutAckPacketId to the latest received ack.

    # UE 4.16
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/NetConnection.cpp#L1340
    async def SendAck(self, AckPacketId, FirstTime: int):
        if (not(self.IsInternalAck())): # NOTE: In UE4 source its InternalAck idk
            if (FirstTime):
                # TODO: PurgeAcks()
                # TODO: self.QueuedAcks.append(AckPacketId)
                pass

            AckData = FBitWriter()

            AckData.WriteBit(1)
            # AckData.WriteIntWrapped(AckPacketId, self.MAX_PACKETID) # TODO: Add that function

            # We still write the bit in shipping to keep the format the same
            AckData.WriteBit(0)

            # Notify server of our current rate per second at this time
            InKBytesPerSecond = 1024 / 1024 # TODO: InBytesPerSecond
            # AckData.SerializeIntPacked(InKBytesPerSecond)

            self.WriteBitsToSendBuffer()

            AllowMerge = False

            TimeSensitive = 1

            print(f'Send ack {AckPacketId}')