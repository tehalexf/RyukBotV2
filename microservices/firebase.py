from hotswap.objects import ModularService
from firebase import firebase
import urllib


class FirebaseService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name,
                                manager_port, query_mode=query_mode)
        self.add_upstream("configservice")
        self.wait_for_manager()

        firebaseObjects = self.upstream(
            "configservice").exposed_firebase_login()
        auth = firebase.FirebaseAuthentication(
            firebaseObjects[2], firebaseObjects[1])
        self.firebaseObj = firebase.FirebaseApplication(
            firebaseObjects[0], authentication=auth)
        # self.exposed_add_authenticated_user()

    def exposed_get_authenticated_users(self):
        a = self.firebaseObj.get('/ryukbotv2/data/authedusers', None)
        return a

    def exposed_add_ow_account(self, accountdict):
        accountdict['battletag'] = accountdict['battletag'].replace('#', '-')
        accountdict['hidden'] = False
        a = self.firebaseObj.patch(
            '/ryukbotv2/data/storedaccounts/%s' % accountdict['battletag'], accountdict)
        return a

    def exposed_get_ow_accounts(self, renamed={}):
        a = self.firebaseObj.get('/ryukbotv2/data/storedaccounts', None)
        popList = []
        for key in a.keys():
            if 'hidden' in a[key].keys():
                if (a[key]['hidden']):
                    popList.append(key)
                a[key].pop('hidden', None)
            if 'battletag' in a[key].keys():
                a[key]['battletag'] = a[key]['battletag'].replace('-', '#')
        for item in popList:
            a.pop(item, None)

        returnDict = {}
        for item in a.keys():
            returnDict[item.replace('-', '#')] = a[item]
        return returnDict

    def exposed_patch_ow_account(self, tag, key, value):
        tag = tag.replace('#', '-')
        a = self.firebaseObj.patch(
            '/ryukbotv2/data/storedaccounts/%s/%s' % (tag, key), value)
        return a

    def exposed_patch_ow_account_multiple(self, tag, values):
        tag = tag.replace('#', '-')
        a = self.firebaseObj.patch(
            '/ryukbotv2/data/storedaccounts/%s' % (tag), values)
        return a

    def exposed_remove_ow_account(self, accountName):
        accountName = accountName.replace('#', '-')
        a = self.firebaseObj.delete(
            '/ryukbotv2/data/storedaccounts', accountName)
        return a

    def exposed_remove_fake_ow_account(self, accountName):
        accountName = accountName.replace('#', '-')
        a = self.firebaseObj.patch(
            '/ryukbotv2/data/storedaccounts/%s' % accountName, {'hidden': True})
        return a

    def exposed_add_authenticated_user(self):
        a = self.firebaseObj.patch('/ryukbotv2/data/authedusers',
                                   [{'username': 'ryuklikesapples'}, {'username': 'bubby'}])
        return a
