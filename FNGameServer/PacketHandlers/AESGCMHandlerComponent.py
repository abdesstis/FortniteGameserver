import binascii
from Crypto.Cipher import AES

class FAESGCMHandlerComponent():
    def __init__(self):
        self.Iv = str()
        self.key = str()

    def ReadKey(self, key: str):
        self.Iv = key[:12]
        self.key = key[12:]
    
    def Incoming(self, Packet: bytes):
        print('PacketHandler AESGCM Decrypt')
        # TODO: I will do that when we can actually use this...
        key = binascii.unhexlify('')
        data = binascii.unhexlify('')
        nonce, tag = data[:12], data[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce)
        print(cipher.decrypt_and_verify(data[12:-16], tag))