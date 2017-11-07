from hotswap.objects import ModularService
import bna
import xmlrpc
import binascii

class BNetAuthService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.wait_for_manager()
        
    def exposed_generate_serial(self):
        serial, byte_secret = bna.request_new_serial("US")
        secret = binascii.hexlify(byte_secret).decode('utf-8')
        restore = bna.get_restore_code(bna.normalize_serial(serial), byte_secret)
        return [serial, secret, restore]
    
    def exposed_get_token(self, secret):
        if (type(secret) is xmlrpc.client.Binary):
            secret = secret.data
        else:
            secret = binascii.unhexlify(secret)
        return bna.get_token(secret=secret)

    def exposed_get_restore_code(self, secret, serial):
        return bna.get_restore_code(bna.normalize_serial(serial), secret)

    def exposed_get_secret_code(self, serial, restore):
        serial, secret = bna.restore(bna.normalize_serial(serial), restore)
        return [serial, secret, restore]
