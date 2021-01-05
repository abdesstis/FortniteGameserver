from enum import Enum

# Enumerates channel types.
# https://github.com/EpicGames/UnrealEngine/blob/2bf1a5b83a7076a0fd275887b373f8ec9e99d431/Engine/Source/Runtime/Engine/Classes/Engine/Channel.h#L21
class EChannelType(Enum):
    CHTYPE_None			= 0  # Invalid type.
    CHTYPE_Control		= 1  # Connection control.
    CHTYPE_Actor  		= 2  # Actor-update channel.
    
    # @todo: Remove and reassign number to CHTYPE_Voice (breaks net compatibility)
    CHTYPE_File         = 3  # Binary file transfer.
    
    CHTYPE_Voice		= 4  # VoIP data channel
    CHTYPE_MAX          = 8  # Maximum.