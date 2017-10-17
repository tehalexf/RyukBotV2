from hotswap.objects import ModularService
from firebase import firebase

class DiscordContextService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("firebaseservice")
        self.wait_for_manager()
        self.state = {}
        # self.exposed_add_authenticated_user()

    def exposed_update_context(self, user, key, value):
        if user not in self.state:
            self.state[user] = {}
        self.state[user][key] = value

    def exposed_get_context(self, user, key):
        try:
            return self.state[user][key]
        except:
            return None
        
