class UNetConnection():
    def __init__(self, socket, remote_addr: tuple):
        self.socket = socket
        self.remote_addr = remote_addr
    
    async def ReceivedRawPacket(self, Data: bytes, Count: int):
        print('Received a raw packet.')