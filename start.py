import sys
sys.dont_write_bytecode = True
import asyncio
import asyncio_dgram

from FNGameServer import UNetConnection

class EasyFN():
    def __init__(self, port: int, ip: str):
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.start(port, ip))

        self.UNetConnections = {}

    async def start(self, port: int, ip: str):
        socket = await asyncio_dgram.bind((ip, port))

        # This should be NMT_Login
        try:
            await (UNetConnection(socket, (None, None))).ReceivedRawPacket(bytes.fromhex('fa1800000002'), len(bytes.fromhex('fa1800000002')))
        except Exception as e:
            print('Error: ' + str(e) + '\n\n')

        print(f'Server started on {ip}:{port}\n\n')

        while True:
            data, remote_addr = await socket.recv()
            print(f'Received {data.hex()} from {remote_addr[0]}:{remote_addr[1]}')
            if not f'{remote_addr[0]}:{remote_addr[1]}' in list(self.UNetConnections.keys()):
                self.UNetConnections[f'{remote_addr[0]}:{remote_addr[1]}'] = UNetConnection(
                    socket,
                    remote_addr,
                    InMaxPacket = 1024 # Not sure, if you know the right value please pr, thanks
                )
            
            await self.UNetConnections[f'{remote_addr[0]}:{remote_addr[1]}'].ReceivedRawPacket(data, len(data))

EasyFN(
    port = 7777,
    ip = '127.0.0.1'
).loop.run_forever()