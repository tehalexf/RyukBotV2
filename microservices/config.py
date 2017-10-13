from hotswap.objects import ModularService
import configparser
import os

class ConfigService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.Config = configparser.ConfigParser()
        self.Config.read('config/ryukbot.dev.config')

    def exposed_discord_id(self):
        return self.Config.get('Discord', 'clientID')
    
    def exposed_firebase_login(self): # this is an exposed method
        return (self.Config.get('Firebase', 'domain'), self.Config.get('Firebase', 'username'), self.Config.get('Firebase', 'key'))
