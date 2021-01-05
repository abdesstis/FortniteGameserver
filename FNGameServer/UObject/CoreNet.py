from ..Serialization import FBitWriter

# A bit writer that serializes FNames and UObject* through
# a network packagemap.
class FNetBitWriter(FBitWriter):
    def __init__(self, *args, **kwargs):
        if kwargs.get('InPackageMap') and kwargs.get('InMaxBits'):
            self.InMaxBits = kwargs.get('InMaxBits')
        elif kwargs.get('InMaxBits'):
            self.InMaxBits = kwargs.get('InMaxBits')

        super().__init__(*args, **kwargs)