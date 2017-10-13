from hotswap.objects import ModularService
from firebase import firebase

class FirebaseService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.add_upstream("configservice")
        self.wait_for_manager()
        
        firebaseObjects = self.upstream("configservice").exposed_firebase_login()
        auth = firebase.FirebaseAuthentication(firebaseObjects[2], firebaseObjects[1])
        self.firebaseObj = firebase.FirebaseApplication(firebaseObjects[0], authentication=auth)

    def exposed_discord_id(self):
        return self.Config.get('Discord', 'clientID')
    
    def exposed_firebase_login(self): # this is an exposed method
        return (self.Config.get('Firebase', 'domain'), self.Config.get('Firebase', 'username'), self.Config.get('Firebase', 'key'))
