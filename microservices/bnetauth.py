from hotswap.objects import ModularService
import bna

class BNetAuthService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.wait_for_manager()
        serial, secret = bna.requestNewSerial("US")
        print(serial, secret)
        # print(dir(bna))
