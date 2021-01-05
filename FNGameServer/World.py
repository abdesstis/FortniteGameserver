from .Net import FNetControlMessage, FNetControlMessageInfo, FInBunch, MessageTypes
from .GameModeBase import AGameModeBase
from .Classes import EClientLoginState
from .PlayerController import APlayerController
from .Level import ULevel

class UWorld:
    def __init__(self):
        # Pointer to the current level being edited. Level has to be in the Levels array and == PersistentLevel in the game.
        self.CurrentLevel = ULevel()

        self.AuthorityGameMode = AGameModeBase()

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
        elif MessageType == MessageTypes.Login.value:
            UniqueIdRepl = None

            # Admit or deny the player here.
            # FNetControlMessage<NMT_Login>::Receive(Bunch, Connection->ClientResponse, Connection->RequestURL, UniqueIdRepl);
            # UE_LOG(LogNet, Log, TEXT("Login request: %s userId: %s"), *Connection->RequestURL, UniqueIdRepl.IsValid() ? *UniqueIdRepl->ToString() : TEXT("Invalid"));

            # Compromise for passing splitscreen playercount through to gameplay login code,
				# without adding a lot of extra unnecessary complexity throughout the login code.
				# NOTE: This code differs from NMT_JoinSplit, by counting + 1 for SplitscreenCount
				#			(since this is the primary connection, not counted in Children)
            InURL = Connection.RequestURL

            # if ( !InURL.Valid )
            # {
            #     UE_LOG( LogNet, Error, TEXT( "NMT_Login: Invalid URL %s" ), *Connection->RequestURL );
            #     Bunch.SetError();
            #     break;
            # }

            SplitscreenCount = 0

            # Don't allow clients to specify this value
            # InURL.RemoveOption(TEXT("SplitscreenCount"));
            # InURL.AddOption(*FString::Printf(TEXT("SplitscreenCount=%i"), SplitscreenCount));

            # skip to the first option in the URL
            # const TCHAR* Tmp = *Connection->RequestURL;
            # for (; *Tmp && *Tmp != '?'; Tmp++);

            # keep track of net id for player associated with remote connection
            Connection.PlayerId = UniqueIdRepl

            # ask the game code if this player can join
            # AGameModeBase* GameMode = GetAuthGameMode();
            GameMode = 1

            if (GameMode):
                pass # GameMode->PreLogin(Tmp, Connection->LowLevelGetRemoteAddress(), Connection->PlayerId, ErrorMsg);
            
            await self.WelcomePlayer(Connection)
        elif MessageType == MessageTypes.Join.value:
            if (Connection.PlayerController == None):
                # Spawn the player-actor for this network player.
                print(f'Join request: {Connection.RequestURL}')

                InURL = Connection.RequestURL

                # if ( !InURL.Valid ):
                #     UE_LOG( LogNet, Error, TEXT( "NMT_Login: Invalid URL %s" ), *Connection->RequestURL );
                #     Bunch.SetError();
                #     break;

                Connection.PlayerController = SpawnPlayActor(Connection, ROLE_AutonomousProxy, InURL, Connection.PlayerId, ErrorMsg)
                if (Connection.PlayerController == None):
                    pass
                else:
                    # Successfully in game.
                    print(f'Join succeeded: {Connection.PlayerController.PlayerState.PlayerName}')
                    # if we're in the middle of a transition or the client is in the wrong world, tell it to travel
                    LevelName = ''
                    # FSeamlessTravelHandler &SeamlessTravelHandler = GEngine->SeamlessTravelHandlerForWorld( this );

                    # if (SeamlessTravelHandler.IsInTransition())
                    # {
                    #     // tell the client to go to the destination map
                    #     LevelName = SeamlessTravelHandler.GetDestinationMapName();
                    # }
                    # else if (!Connection->PlayerController->HasClientLoadedCurrentWorld())
                    # {
                    #     // tell the client to go to our current map
                    #     FString NewLevelName = GetOutermost()->GetName();
                    #     UE_LOG(LogNet, Log, TEXT("Client joined but was sent to another level. Asking client to travel to: '%s'"), *NewLevelName);
                    #     LevelName = NewLevelName;
                    # }
                    # if (LevelName != TEXT(""))
                    # {
                    #     Connection->PlayerController->ClientTravel(LevelName, TRAVEL_Relative, true);
                    # }

                    # // @TODO FIXME - TEMP HACK? - clear queue on join
                    # Connection->QueuedBits = 0;
    async def WelcomePlayer(self, Connection):
        if not self.CurrentLevel:
            return

        await Connection.SendPackageMap()

        LevelName = '/Game/Athena/Apollo/Maps/Apollo_Terrain'
        # FString LevelName = CurrentLevel->GetOutermost()->GetName();
        # Connection->ClientWorldPackageName = CurrentLevel->GetOutermost()->GetFName();
        Connection.ClientWorldPackageName = LevelName

        GameName = ''
        RedirectURL = ''
        if (self.AuthorityGameMode != None):
            GameName = '/Game/Athena/Athena_GameMode.Athena_GameMode_C'
            await self.AuthorityGameMode.GameWelcomePlayer(Connection, RedirectURL)

        await (FNetControlMessage(MessageTypes.Welcome)).Send(Connection, LevelName, GameName, RedirectURL)
        # Connection->FlushNet();
        # don't count initial join data for netspeed throttling
        # as it's unnecessary, since connection won't be fully open until it all gets received, and this prevents later gameplay data from being delayed to "catch up"
        Connection.QueuedBits = 0
        Connection.ClientLoginState = EClientLoginState.Welcomed # Client is fully logged in

    async def SpawnPlayActor(self, NewPlayer, RemoteRole, InURL: str, UniqueId, Error: str) -> APlayerController:
        pass