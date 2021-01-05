from enum import Enum

# https://github.com/EpicGames/UnrealEngine/blob/df84cb430f38ad08ad831f31267d8702b2fefc3e/Engine/Source/Runtime/CoreUObject/Public/UObject/CoreNetTypes.h#L37from enum import Enum
class EChannelCloseReason(Enum):
    Destroyed = 1
    Dormancy = 2
    LevelUnloaded = 3
    Relevancy = 4
    TearOff = 5
    # reserved
    MAX = 15 # this value is used for serialization, modifying it may require a network version change