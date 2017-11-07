import xmlrpc.client
import threading
from xmlrpc.server import SimpleXMLRPCServer
from inspect import getmembers, isfunction
import time
from xmlrpc.server import SimpleXMLRPCServer
import inspect

class DocumentWriter():
    def __init__(self):
        self.descriptions = []
    def describe(self, usage, regex, text_description, glob=True):
        def decorator(func):
            self.descriptions.append({'u' : usage, 'r' : regex, 't' : text_description, 'f' : func, 'a' : glob})
            return func
        return decorator
    
    def get_descriptions(self):
        return self.descriptions

class ServerWrapper():
    def __init__(self, port, className, instanceName, *args):
        self.server = SimpleXMLRPCServer(('localhost', port), allow_none=True,logRequests=False)
        self.instance = className(port, instanceName, *args)
        attrs = (getattr(self.instance, name) for name in dir(self.instance))
        methods = filter(inspect.ismethod, attrs)
        
        for method in methods:
            if method.__name__.startswith('exposed_'):
                self.server.register_function(method)
        # self.server.register_function(self.instance.add_upstream)
        # self.server.register_function(self.instance.add_downstream)
        # self.server.register_function(self.instance.test)
        # self.server.register_instance(self.instance)
        t = threading.Thread(target=self.server.serve_forever)
        t.start()

class ManagerInvoker():
    def __init__(self, port, *args):
        t = threading.Thread(target=ServerWrapper, args=(port, ModularServiceManager, "manager", port, *args))
        t.start()
        print("Manager service started on %d." % port)

class ModularServiceManager(object):
    def __init__(self, dummy1, dummy2, port, services, address_pool):

        
        self.services = {}
        self.pool = address_pool
        self.port = port
        self.start_services([x for x in map(lambda x: [x, x.__name__.lower()], services)])

    def exposed_wait(self):
        return

    def start_services(self, service_list):
        for item in service_list:
            className, instanceName, *args = item
            port = self.exposed_init_svc(instanceName)
            t = threading.Thread(target=ServerWrapper, args=(port, className, instanceName, self.port, *args))
            t.start()
            print('Service %s starting...' % instanceName)

    def exposed_resolve_name(self, name):
        if name not in self.services.keys():
            port = self.pool.pop(0)
            self.services[name] = {'port': port, 'status' : 0}
            return port
        else:
            return self.services[name]['port']

    def exposed_init_svc(self, name):
        if name not in self.services.keys():
            port = self.pool.pop(0)
            self.services[name] = {'port': port, 'status' : 1}
            return port
        else:
            service = self.services[name]
            if not service['status']:
                service['status'] = 1
                return service['port']
            else:
                print("ALREADY REGISTERED")
                return None


class ModularService(object):
    def __init__(self, port, service_name, manager_port, query_mode = False):
        self.dict_upstream = {}
        self.dict_downstream = {}
        self.is_up = False
        self.query_mode = query_mode
        self.port = port
        self.loaded = False
        self.service_name = service_name
        self.manager = xmlrpc.client.ServerProxy("http://localhost:%d/" % (manager_port))
        print("Service %s registered on port %d (manager %d)." % (service_name, port, manager_port))
    
    def run_in_thread(self, className, *args):
        t = threading.Thread(target=className, args=args)
        t.start()

    def finalize(self):
        print("FINALIZED")
        pass

    def wait_for_manager(self):
        self.loaded = True
        self.manager.exposed_wait()

    def upstream(self, dep_name):
        if (dep_name not in self.dict_upstream.keys()):
            print("Upstream %s does not exist." % dep_name)
        else:
            return self.dict_upstream[dep_name][1]

            
    def add_upstream(self, dep_name):
        if (dep_name not in self.dict_upstream.keys()):
            port = self.manager.exposed_resolve_name(dep_name)
            self.dict_upstream[dep_name] = [port, xmlrpc.client.ServerProxy("http://localhost:%d/" % (port))]
        else:
            print("Upstream %s already registered." % dep_name)

    # def exposed_add_endpoint(self, dep_name)

    # def exposed_add_downstream(self, dep_name, ways=2):
    #     if dep_name in self.dependencies.keys():
    #         print("DEPENCENCY %s ALREADY REGISTERED" % dep_name)
    #         return
    #         # TODO: Throw error?
    #     print("%s adding downstream %s" % (self.service_name, dep_name))
    #     # TODO: Failure condition AND query_mode
    #     dep_port = self.manager.exposed_resolve_name(dep_name)
    #     entry = [dep_port, None, xmlrpc.client.ServerProxy("http://localhost:%d/" % (dep_port)), ways]
    #     self.dependencies[dep_name] = entry

    #     time.sleep(3)
    #     entry[-2].add_upstream(self.service_name, self.port)

    # def exposed_add_upstream(self, dep_name, dep_port):
    #     if dep_name in self.parents.keys():
    #         if dep_port != self.parents[dep_name]:
    #             print("ERROR ERROR!!!")
    #             return
    #         print("ALREADY EXISTS!!!!")
    #     else:
    #         print("%s adding upstream %s on %d" % (self.service_name, dep_name, dep_port))
    #         self.parents[dep_name] = dep_port

    # def exposed_test(self):
    #     time.sleep(3)
    #     print("AJKSASDLSANKFLFKNDSFSFKLSDFKSD")
    def exposed_start_server(self):
        self.is_up = True


