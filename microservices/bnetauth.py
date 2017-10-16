from hotswap.objects import ModularService
import bna
import xmlrpc

class BNetAuthService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.wait_for_manager()
        
    def exposed_generate_serial(self):
        return bna.request_new_serial("US")
    
    def exposed_get_token(self, secret):
        if (type(secret) is xmlrpc.client.Binary):
            secret = secret.data
        token, time_remaining = bna.get_token(secret=secret)
        return token, time_remaining

    def exposed_get_restore_code(self, secret, serial):
        return bna.get_restore_coe(serial, secret)