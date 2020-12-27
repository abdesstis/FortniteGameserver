from .Net import FNetControlMessage, FNetControlMessageInfo, FInBunch, MessageTypes

class UWorld:
    def __init__(self):
        pass

    # https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/World.cpp#L4093
    async def NotifyControlMessage(self, Connection, MessageType: int, Bunch: FInBunch):
        # We are the server. -> https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/World.cpp#L4150
        print(f'Level server received: {FNetControlMessageInfo().GetName(MessageType)}')

        if MessageType == MessageTypes.Hello.value:
            IsLittleEndian = 0
            RemoteNetworkVersion = 0
            LocalNetworkVersion = None

            # No clue what this does
            # FNetControlMessage<NMT_Hello>::Receive(Bunch, IsLittleEndian, RemoteNetworkVersion);

            if (True != True): # FNetworkVersion::IsNetworkCompatible(LocalNetworkVersion, RemoteNetworkVersion)
                # FNetControlMessage<NMT_Upgrade>::Send(Connection, LocalNetworkVersion);
                pass
            else:
                print('We got NMT_Hello, sending challenge')
                self.ExpectedClientLoginMsgType = MessageTypes.Login
                
                await (FNetControlMessage(MessageTypes.Challenge)).Send(Connection)