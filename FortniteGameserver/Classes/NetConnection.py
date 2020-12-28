from enum import Enum

# If this connection is from a client, this is the current login state of this connection/login attempt
class EClientLoginState(Enum):
    Invalid		= 0 # This must be a client (which doesn't use this state) or uninitialized.
    LoggingIn	= 1 # The client is currently logging in.
    Welcomed	= 2 # Fully logged in.
    
    def ToString(self, EnumVal):
        if EnumVal == 0:
            return 'Invalid'
        elif EnumVal == 1:
            return 'LoggingIn'
        elif EnumVal == 2:
            return 'Welcomed'
        else:
            return ''