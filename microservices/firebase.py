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
        # self.exposed_add_authenticated_user()

    def exposed_get_authenticated_users(self):
        a = self.firebaseObj.get('/ryukbotv2/data/authedusers', None)
        print(a)
        return a
        
    def exposed_add_authenticated_user(self):
        a = self.firebaseObj.patch('/ryukbotv2/data/authedusers', {'data': [{'username': 'ryuklikesapples'}, {'username' : 'bubby'}]})
        print(a)
        return a
 

