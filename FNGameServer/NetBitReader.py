from ..Serialization import FBitReader

class NetBitReader(FBitReader):
    def __init__(self):
        super().__init__()

    def SerializePropertyInt(self):
        return self.ReadInt32()

    def  SerializeRepMovement(self):
        pass