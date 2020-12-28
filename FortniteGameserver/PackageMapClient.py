from .Net import FInBunch

class UPackageMapClient:
    def __init__(self, Connection):
        self.Connection = Connection

        self.MustBeMappedGuidsInLastBunch = False

    # https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Private/PackageMapClient.cpp#L1319
    async def ReceiveNetGUIDBunch(self, InBunch: FInBunch):
        if not (InBunch.bHasPackageMapExports):
            return

        StartingBitPos = InBunch.GetPosBits()

        bHasRepLayoutExport = InBunch.ReadBit() == 1
        if (bHasRepLayoutExport):
            # We need to keep this around to ensure we don't break backwards compatability.
            await self.ReceiveNetFieldExportsCompat()
            return

    # UE4.16 https://github.com/EpicGames/UnrealEngine/blob/37ca478f5aa37e9dd49b68a7a39d01a9d5937154/Engine/Source/Runtime/Engine/Private/PackageMapClient.cpp#L1284
    # UE4.26 https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Private/PackageMapClient.cpp#L1592
    async def ReceiveNetFieldExportsCompat(self, Archive):
        # WARNING: If this code path is enabled for use beyond replay, it will need a security audit/rewrite
        if not self.Connection.IsInternalAck():
            return
        
        # Read number of net field exports
        NumLayoutCmdExports = 0

    def GetMustBeMappedGuidsInLastBunch(self):
        return self.MustBeMappedGuidsInLastBunch