from hotswap.objects import ModularService

class DiscordOutboundService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.jobs = []
        self.wait_for_manager()

    def exposed_add_job(self, job):
        self.jobs.append(job)
    
    def exposed_get_job(self): # this is an exposed method
        if (len(self.jobs) > 0):
            return self.jobs.pop(0)
        return None