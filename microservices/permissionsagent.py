from hotswap.objects import ModularService

class PermissionsAgentService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("firebaseservice")
        self.wait_for_manager()

    def exposed_is_authorized(self, id):
        return True
    
    def exposed_add_authorized(self, id):
        pass
