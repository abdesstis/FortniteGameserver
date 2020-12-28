from .GameSession import AGameSession

class AGameModeBase:
    def __init__(self):
        # Game Session handles login approval, arbitration, online game interface
        self.GameSession = AGameSession()

    def GameWelcomePlayer(self, Connection, RedirectURL: str):
        pass

    async def PreLogin(self, Options: str, Address: str, UniqueId, ErrorMessage: str):
        # Maybe TODO: Try calling deprecated version first
        
        ErrorMessage = await self.GameSession.ApproveLogin(Options)