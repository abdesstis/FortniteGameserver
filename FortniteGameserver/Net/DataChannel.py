from enum import Enum
from .DataBunch import FInBunch, FControlChannelOutBunch

from ..Classes import EChannelType

MAX_QUEUED_CONTROL_MESSAGES = 32768

# https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Public/Net/DataChannel.h#L92
class FNetControlMessage():
    def __init__(self, MessageType: int):
        self.Index = MessageTypes

    async def Send(self, Connection, *args, **kwargs):
        Bunch = FControlChannelOutBunch(Connection.Channels[0], False)
        MessageType = self.Index
        await Connection.Channels[0].SendBunch(Bunch, True)

# https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Public/Net/DataChannel.h#L33
# contains info about a message type retrievable without static binding (e.g. whether it's a valid type, friendly name string, etc)
class FNetControlMessageInfo():
    def __init__(self):
        self.Names = ['Hello', 'Welcome', 'Upgrade', 'Challenge', 'Netspeed', 'Login', 'Failure', 'Join', 'JoinSplit', 0, 'Skip', 'Abort', 0, 'PCSwap', 'ActorChannelFailure', 'DebugText', 'NetGUIDAssign', 'SecurityViolation', 'GameSpecific', 'EncryptionAck', 'DestructionInfo', 0, 0, 'BeaconWelcome', 'BeaconJoin', 'BeaconAssignGUID', 'BeaconNetGUIDAck']

    def GetName(self, MessageIndex: int):
        return self.Names[MessageIndex]

    def IsRegistered(self, MessageIndex: int) -> bool:
        return self.Names[MessageIndex][0] != 0

    def SetName(self, MessageType: int, InName: str):
        self.Names[MessageType] = InName

class MessageTypes(Enum):
    Hello = 0 # initial client connection message
    Welcome = 1 # server tells client they're ok'ed to load the server's level
    Upgrade = 2 # server tells client their version is incompatible
    Challenge = 3 # server sends client challenge string to verify integrity
    Netspeed = 4 # client sends requested transfer rate
    Login = 5 # client requests to be admitted to the game
    Failure = 6 # indicates connection failure
    Join = 9 # final join request (spawns PlayerController)
    JoinSplit = 10 # child player (splitscreen) join request
    Skip = 12 # client request to skip an optional package
    Abort = 13 # client informs server that it aborted a not-yet-verified package due to an UNLOAD request
    PCSwap = 15 # client tells server it has completed a swap of its Connection->Actor
    ActorChannelFailure = 16 # client tells server that it failed to open an Actor channel sent by the server (e.g. couldn't serialize Actor archetype)
    DebugText = 17 # debug text sent to all clients or to server
    NetGUIDAssign = 18 # Explicit NetworkGUID assignment. This is rare and only happens if a netguid is only serialized client->server (this msg goes server->client to tell client what ID to use in that case)
    SecurityViolation = 19 # server tells client that it has violated security and has been disconnected
    GameSpecific = 20 # custom game-specific message routed to UGameInstance for processing
    EncryptionAck = 21
    DestructionInfo = 22
    BeaconWelcome = 25 # server tells client they're ok to attempt to join (client sends netspeed/beacontype)
    BeaconJoin = 26 # server tries to create beacon type requested by client, sends NetGUID for actor sync
    BeaconAssignGUID = 27 # client assigns NetGUID from server to beacon actor, sends NetGUIDAck
    BeaconNetGUIDAck = 28 # server received NetGUIDAck from client, connection established successfully

class UChannel:
    def __init__(self, Connection, ChIndex: int, bOpenedLocally: bool, ChType: EChannelType):
        self.Connection = Connection
        self.bOpenedLocally = bOpenedLocally
        self.ChIndex = ChIndex
        self.ChType = ChType

        # I guess this is wrong...
        self.InPartialBunch = FInBunch()
    
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L313
    async def ReceivedRawBunch(self, Bunch: FInBunch, bOutSkipAck: bool):
        # Immediately consume the NetGUID portion of this bunch, regardless if it is partial or reliable.
        # NOTE - For replays, we do this even earlier, to try and load this as soon as possible, in case there is an issue creating the channel
        # If a replay fails to create a channel, we want to salvage as much as possible
        if (Bunch.bHasPackageMapExports):
            await self.Connection.PackageMap.ReceiveNetGUIDBunch(Bunch)

        if (self.Connection.IsInternalAck()):
            return

        if not (self.Connection.Channels[self.ChIndex] == self):
            return

        if (False): # Bunch.bReliable and Bunch.ChSequence != self.Connection.InReliable[self.ChIndex] + 1
            # We shouldn't hit this path on 100% reliable connections
            # if (self.Connection.IsInternalAck()):
            #     return
            # If this bunch has a dependency on a previous unreceived bunch, buffer it.
            if (Bunch.bOpen):
                return

            # Verify that UConnection::ReceivedPacket has passed us a valid bunch.
            if not (Bunch.ChSequence > self.Connection.InReliable[self.ChIndex]):
                return

            # Find the place for this item, sorted in sequence.
            # UE_LOG(LogNetTraffic, Log, TEXT("      Queuing bunch with unreceived dependency: %d / %d"), Bunch.ChSequence, Connection->InReliable[ChIndex]+1 );
            # TODO: Continue
        else:
            bDeleted = await self.ReceivedNextBunch(Bunch, bOutSkipAck)
            
            if (bDeleted):
                return

            # TODO: Dispatch any waiting bunches.
            InRec = False
            while (InRec):
                break
    
    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L432
    async def ReceivedNextBunch(self, Bunch: FInBunch, bOutSkipAck: bool) -> bool:
        return await self.ReceivedSequencedBunch(Bunch)
        
        # .-.

        # We received the next bunch. Basically at this point:
        # -We know this is in order if reliable
        # -We dont know if this is partial or not
        # If its not a partial bunch, of it completes a partial bunch, we can call ReceivedSequencedBunch to actually handle it

        # Note this bunch's retirement.
        if (Bunch.bReliable):
            # Reliables should be ordered properly at this point
            if not (Bunch.ChSequence == self.Connection.InReliable[Bunch.ChIndex] + 1):
                return

            self.Connection.InReliable[Bunch.ChIndex] = Bunch.ChSequence
        
        if (Bunch.bPartial):
            HandleBunch = None
            if (Bunch.bPartialInitial):
                # Create new InPartialBunch if this is the initial bunch of a new sequence.
                if (self.InPartialBunch != None):
                    if not (self.InPartialBunch.bPartialFinal):
                        if (self.InPartialBunch.bReliable):
                            if (Bunch.bReliable): # FIXME: Disconnect client in this case
                                return
                            # UE_LOG(LogNetPartialBunch, Log, TEXT( "Unreliable partial trying to destroy reliable partial 1") );
                            bOutSkipAck = False
                            return False
                        
                        # We didn't complete the last partial bunch - this isn't fatal since they can be unreliable, but may want to log it.
                        # UE_LOG(LogNetPartialBunch, Verbose, TEXT("Incomplete partial bunch. Channel: %d ChSequence: %d"), InPartialBunch->ChIndex, InPartialBunch->ChSequence);
                    
                    self.InPartialBunch = None
                
                self.InPartialBunch = FInBunch(Bunch, False)
                if (not Bunch.bHasPackageMapExports and Bunch.GetBitsLeft() > 0):
                    if not (Bunch.GetBitsLeft() % 8 == 0): # Starting partial bunches should always be byte aligned.
                        return
                    
                    # self.InPartialBunch.AppendDataFromChecked(Bunch.GetDataPosChecked(), Bunch.GetBitsLeft())
                    # UE_LOG(LogNetPartialBunch, Verbose, TEXT("Received New partial bunch. Channel: %d ChSequence: %d. NumBits Total: %d. NumBits LefT: %d.  Reliable: %d"), InPartialBunch->ChIndex, InPartialBunch->ChSequence, InPartialBunch->GetNumBits(),  Bunch.GetBytesLeft(), Bunch.bReliable);
                else:
                    pass # UE_LOG(LogNetPartialBunch, Verbose, TEXT("Received New partial bunch. It only contained NetGUIDs.  Channel: %d ChSequence: %d. Reliable: %d"), InPartialBunch->ChIndex, InPartialBunch->ChSequence, Bunch.bReliable);
            else:
                # Merge in next partial bunch to InPartialBunch if:
                #   -We have a valid InPartialBunch
                #   -The current InPartialBunch wasn't already complete
                #   -ChSequence is next in partial sequence
                #   -Reliability flag matches
                bSequenceMatches = False
                if (self.InPartialBunch != None):
                    bReliableSequencesMatches = Bunch.ChSequence == self.InPartialBunch.ChSequence + 1
                    bUnreliableSequenceMatches = bReliableSequencesMatches or (Bunch.ChSequence == self.InPartialBunch.ChSequence)
                    
                    # Unreliable partial bunches use the packet sequence, and since we can merge multiple bunches into a single packet,
                    # it's perfectly legal for the ChSequence to match in this case.
                    # Reliable partial bunches must be in consecutive order though
                    bSequenceMatches = InPartialBunch.bReliable if bReliableSequencesMatches else bUnreliableSequenceMatches

                if (self.InPartialBunch != None and not (self.InPartialBunch.bPartialFinal) and bSequenceMatches and self.InPartialBunch.bReliable == Bunch.bReliable):
                    # Merge.
                    # UE_LOG(LogNetPartialBunch, Verbose, TEXT("Merging Partial Bunch: %d Bytes"), Bunch.GetBytesLeft() );
                    if (Bunch.bHasPackageMapExports and Bunch.GetBitsLeft() > 0):
                        pass # self.InPartialBunch.AppendDataFromChecked(Bunch.GetDataPosChecked(), Bunch.GetBitsLeft())
                    
                    # Only the final partial bunch should ever be non byte aligned. This is enforced during partial bunch creation
                    # This is to ensure fast copies/appending of partial bunches. The final partial bunch may be non byte aligned.
                    if not (Bunch.bHasPackageMapExports or Bunch.bPartialFinal or Bunch.GetBitsLeft() % 8 == 0):
                        return
                    
                    # Advance the sequence of the current partial bunch so we know what to expect next
                    self.InPartialBunch.ChSequence = Bunch.ChSequence

                    if (Bunch.bPartialFinal):
                        # if (UE_LOG_ACTIVE(LogNetPartialBunch,Verbose)) // Don't want to call appMemcrc unless we need to
                        # {
                        #     UE_LOG(LogNetPartialBunch, Verbose, TEXT("Completed Partial Bunch: Channel: %d ChSequence: %d. Num: %d Rel: %d CRC 0x%X"), InPartialBunch->ChIndex, InPartialBunch->ChSequence, InPartialBunch->GetNumBits(), Bunch.bReliable, FCrc::MemCrc_DEPRECATED(InPartialBunch->GetData(), InPartialBunch->GetNumBytes()));
                        # }

                        if (Bunch.bHasPackageMapExports):
                            return
                        
                        HandleBunch = self.InPartialBunch
                        
                        self.InPartialBunch.bPartialFinal = True
                        self.InPartialBunc.bClose = Bunch.bClose
                        self.InPartialBunc.bDormant = Bunch.bDormant
                        self.InPartialBunc.bIsReplicationPaused = Bunch.bIsReplicationPaused
                        self.InPartialBunc.bHasMustBeMappedGUIDs = Bunch.bHasMustBeMappedGUIDs
                    else:
                        # if (UE_LOG_ACTIVE(LogNetPartialBunch,Verbose)) // Don't want to call appMemcrc unless we need to
                        # {
                        #     UE_LOG(LogNetPartialBunch, Verbose, TEXT("Received Partial Bunch: Channel: %d ChSequence: %d. Num: %d Rel: %d CRC 0x%X"), InPartialBunch->ChIndex, InPartialBunch->ChSequence, InPartialBunch->GetNumBits(), Bunch.bReliable, FCrc::MemCrc_DEPRECATED(InPartialBunch->GetData(), InPartialBunch->GetNumBytes()));
                        # }
                        pass
                else:
                    # Merge problem - delete InPartialBunch. This is mainly so that in the unlikely chance that ChSequence wraps around, we wont merge two completely separate partial bunches.

                    # We shouldn't hit this path on 100% reliable connections
                    if self.Connection.IsInternalAck():
                        return
                    
                    bOutSkipAck = True # Don't ack the packet, since we didn't process the bunch
                    
                    if (self.InPartialBunch != None and self.InPartialBunch.bReliable):
                        if Bunch.bReliable: # FIXME: Disconnect client in this case
                            return
                        
                        # UE_LOG( LogNetPartialBunch, Log, TEXT( "Unreliable partial trying to destroy reliable partial 2" ) );
                        return False
                    
                    # if (UE_LOG_ACTIVE(LogNetPartialBunch,Verbose)) // Don't want to call appMemcrc unless we need to
                    # {
                    #     if (InPartialBunch)
                    #     {
                    #         UE_LOG(LogNetPartialBunch, Verbose, TEXT("Received Partial Bunch Out of Sequence: Channel: %d ChSequence: %d/%d. Num: %d Rel: %d CRC 0x%X"), InPartialBunch->ChIndex, InPartialBunch->ChSequence, Bunch.ChSequence, InPartialBunch->GetNumBits(), Bunch.bReliable, FCrc::MemCrc_DEPRECATED(InPartialBunch->GetData(), InPartialBunch->GetNumBytes()));
                    #     }
                    #     else
                    #     {
                    #         UE_LOG(LogNetPartialBunch, Verbose, TEXT("Received Partial Bunch Out of Sequence when InPartialBunch was NULL!"));
                    #     }
                    # }

                    if (self.InPartialBunch != None):
                        self.InPartialBunch = None

            # Fairly large number, and probably a bad idea to even have a bunch this size, but want to be safe for now and not throw out legitimate data
            MAX_CONSTRUCTED_PARTIAL_SIZE_IN_BYTES = 1024 * 64
            
            if (self.Connection.IsInternalAck() and self.InPartialBunch != None and self.InPartialBunch.GetNumBytes() > MAX_CONSTRUCTED_PARTIAL_SIZE_IN_BYTES):
                return False

        if (HandleBunch != None):
            if (HandleBunch.bOpen):
                if (self.ChType != EChannelType.CHTYPE_Voice.value): # Voice channels can open from both side simultaneously, so ignore this logic until we resolve this´
                    if self.bOpenedLocally: # If we opened the channel, we shouldn't be receiving bOpen commands from the other side
                        return
                
                # Remember the range.
                # In the case of a non partial, HandleBunch == Bunch
                # In the case of a partial, HandleBunch should == InPartialBunch, and Bunch should be the last bunch.
                # OpenPacketId.First = HandleBunch.PacketId
                # OpenPacketId.Last = Bunch.PacketId
                OpenAcked = True

                # UE_LOG( LogNetTraffic, Verbose, TEXT( "ReceivedNextBunch: Channel now fully open. ChIndex: %i, OpenPacketId.First: %i, OpenPacketId.Last: %i" ), ChIndex, OpenPacketId.First, OpenPacketId.Last );
            
            if (self.ChType != EChannelType.CHTYPE_Voice.value): # Voice channels can open from both side simultaneously, so ignore this logic until we resolve this
                # Don't process any packets until we've fully opened this channel 
                # (unless we opened it locally, in which case it's safe to process packets)
                pass # TODO...

            # Receive it in sequence.
            return await self.ReceivedSequencedBunch(HandleBunch)
    
        return False

    async def ReceivedSequencedBunch(self, Bunch: FInBunch) -> bool:
        if True: # (!Closing)
            await self.ReceivedBunch(Bunch)

    async def SendBunch(self, *args, **kwargs): # TODO:
        # Set bunch flags.
        pass

# https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Classes/Engine/ControlChannel.h#L20
class FQueuedControlMessage:
    def __init__(self):
        # The raw message data
        self.Data = bytes()
        # The bit size of the message
        self.CountBits = 0

# https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Classes/Engine/ControlChannel.h#L40
# A channel for exchanging connection control messages.
class UControlChannel(UChannel):
    def __init__(self, *args, **kwargs):
        # Used to interrogate the first packet received to determine endianess
        # of the sending client
        self.bNeedsEndianInspection = bool()
        # provides an extra buffer beyond RELIABLE_BUFFER for control channel messages
        # as we must be able to guarantee delivery for them
        # because they include package map updates and other info critical to client/server synchronization
        self.QueuedMessages = []
        # maximum size of additional buffer
        # if this is exceeded as well, we kill the connection.  @TODO FIXME temporarily huge until we figure out how to handle 1 asset/package implication on packagemap

        super().__init__(*args, **kwargs)

    # https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L1404
    def CheckEndianess(self, Bunch: FInBunch) -> bool:
        # Assume the packet is bogus and the connection needs closing
        bConnectionOk = False
        # Get pointers to the raw packet data
        HelloMessage = Bunch.GetData()
        # Check for a packet that is big enough to look at (message ID (1 byte) + platform identifier (1 byte))
        if (Bunch.GetNumBytes() >= 2):
            if (HelloMessage[0] == MessageTypes.Hello.value):
                # Get platform id
                OtherPlatformIsLittle = HelloMessage[1]
                OtherPlatformIsLittle == int(not (not OtherPlatformIsLittle)) # should just be zero or one, we use check slow because we don't want to crash in the wild if this is a bad value.
                IsLittleEndian = 0 # int(not (not 0)) # should only be one or zero
                
                # Check whether the other platform needs byte swapping by
                # using the value sent in the packet. Note: we still validate it
                # TODO: Add this
                if (OtherPlatformIsLittle ^ IsLittleEndian):
                    # Client has opposite endianess so swap this bunch
                    # and mark the connection as needing byte swapping
                    # Bunch.SetByteSwapping(true);
                    # Connection->bNeedsByteSwapping = true;
                    pass
                else:
                    # Disable all swapping
                    # Bunch.SetByteSwapping(false);
                    # Connection->bNeedsByteSwapping = false;
                    pass
                
                # We parsed everything so keep the connection open
                bConnectionOk = True
                self.bNeedsEndianInspection = False
        
        return bConnectionOk

    # https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L1479
    async def ReceivedBunch(self, Bunch: FInBunch):
        # If this is a new client connection inspect the raw packet for endianess
        if (self.Connection and self.bNeedsEndianInspection and not self.CheckEndianess(Bunch)):
            # Send close bunch and shutdown this connection
            # UE_LOG(LogNet, Warning, TEXT("UControlChannel::ReceivedBunch: NetConnection::Close() [%s] [%s] [%s] from CheckEndianess(). FAILED. Closing connection."),
			# Connection->Driver ? *Connection->Driver->NetDriverName.ToString() : TEXT("NULL"),
			# Connection->PlayerController ? *Connection->PlayerController->GetName() : TEXT("NoPC"),
			# Connection->OwningActor ? *Connection->OwningActor->GetName() : TEXT("No Owner"));

            await self.Connection.socket.close()
            return

        # Process the packet
        if (True): # while (not Bunch.AtEnd() and self.Connection != None): # if the connection got closed, we don't care about the rest
            MessageType = Bunch.ReadByte()
            Pos = Bunch.GetPosBits()

            print(f'MessageType: ' +  str(MessageType))

            # we handle Actor channel failure notifications ourselves
            if (MessageType == MessageTypes.ActorChannelFailure.value):
                pass
            elif (MessageType == MessageTypes.GameSpecific.value):
                MessageByte = 0
                MessageStr = ''
                # FNetControlMessage<NMT_GameSpecific>::Receive(Bunch, MessageByte, MessageStr);
                # if (Connection->Driver->World != NULL && Connection->Driver->World->GetGameInstance() != NULL)
                # {
                #     Connection->Driver->World->GetGameInstance()->HandleGameNetControlMessage(Connection, MessageByte, MessageStr);
                # }
                # else
                # {
                #     FWorldContext* Context = GEngine->GetWorldContextFromPendingNetGameNetDriver(Connection->Driver);
                #     if (Context != NULL && Context->OwningGameInstance != NULL)
                #     {
                #         Context->OwningGameInstance->HandleGameNetControlMessage(Connection, MessageByte, MessageStr);
                #     }
                # }
            elif (MessageType == MessageTypes.SecurityViolation.value):
                DebugMessage = ''
                # FNetControlMessage<NMT_SecurityViolation>::Receive(Bunch, DebugMessage);
                # UE_SECURITY_LOG(Connection, ESecurityEvent::Closed, TEXT("%s"), *DebugMessage);
                # break
            elif (MessageType == MessageTypes.DestructionInfo.value):
                await self.ReceiveDestructionInfo(Bunch)
            else:
                # Process control message on client/server connection
                await self.Connection.World.NotifyControlMessage(self.Connection, MessageType, Bunch)

            # if the message was not handled, eat it ourselves
            if (Pos == Bunch.GetPosBits()):
                print(f'Got control channel message type: {MessageType}')
                if MessageType == MessageTypes.Hello.value:
                    pass
                elif MessageType == MessageTypes.Welcome:
                    pass
                elif MessageType == MessageTypes.Upgrade:
                    pass
                elif MessageType == MessageTypes.Challenge:
                    pass
                elif MessageType == MessageTypes.Netspeed:
                    pass
                elif MessageType == MessageTypes.Login:
                    pass
                elif MessageType == MessageTypes.Failure:
                    pass
                elif MessageType == MessageTypes.Join:
                    pass
                elif MessageType == MessageTypes.JoinSplit:
                    pass
                elif MessageType == MessageTypes.Skip:
                    pass
                elif MessageType == MessageTypes.Abort:
                    pass
                elif MessageType == MessageTypes.PCSwap:
                    pass
                elif MessageType == MessageTypes.ActorChannelFailure:
                    pass
                elif MessageType == MessageTypes.DebugText:
                    pass
                elif MessageType == MessageTypes.NetGUIDAssign:
                    pass
                elif MessageType == MessageTypes.EncryptionAck:
                    pass
                elif MessageType == MessageTypes.BeaconWelcome:
                    pass
                elif MessageType == MessageTypes.BeaconJoin:
                    pass
                elif MessageType == MessageTypes.BeaconAssignGUID:
                    pass
                elif MessageType == MessageTypes.BeaconNetGUIDAck:
                    pass
                else:
                    # if this fails, a case is missing above for an implemented message type
                    # or the connection is being sent potentially malformed packets
                    # @PotentialDOSAttackDetection
                    # check(!FNetControlMessageInfo::IsRegistered(MessageType));

                    print(f'Received unknown control channel message {MessageType}. Closing connection.')
                    await self.Connection.socket.close()
                    return
        
    # https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Private/DataChannel.cpp#L1856
    async def ReceiveDestructionInfo(self, Bunch: FInBunch):
        raise '"ReceiveDestructionInfo" not added yet'