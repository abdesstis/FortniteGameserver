from .PlayerController import APlayerController

class AGameSession:
    def __init__(self):
        # Maximum number of spectators allowed by this server.
        self.MaxSpectators = int()
        # Maximum number of players allowed by this server.
        self.MaxPlayers = int()
        # Restrictions on the largest party that can join together
        self.MaxPartySize = int()
        # Maximum number of splitscreen players to allow from one connection
        self.MaxSplitscreensPerConnection = int()
        # Is voice enabled always or via a push to talk keybinding
        self.bRequiresPushToTalk = bool()
        # SessionName local copy from PlayerState class.  should really be define in this class, but need to address replication issues 
        self.SessionName = str()
    
    # Initialize options based on passed in options string
    def InitOptions(Options: str):
        pass

    async def ApproveLogin(self, Options: str):
        return ''
        # TODO: The function

    # I don't think that we can ever use this...
    async def KickPlayer(self, KickedPlayer: APlayerController, KickReason: str):
        # Do not kick logged admins
        if (KickedPlayer != None):
            if (KickedPlayer.GetPaw() != None):
                await KickedPlayer.GetPawn().Destory()
            
            await KickedPlayer.ClientWasKicked(KickReason)

            if (KickedPlayer != None):
                await KickedPlayer.Destory()
            
            return True
        else:
            return False

    async def BanPlayer(self, BannedPlayer: APlayerController, BanReason: str):
        return await self.KickPlayer(BannedPlayer, BanReason)