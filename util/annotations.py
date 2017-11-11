def usage(use):
    def decorator(func):
        func.usage = use
        return func
    return decorator
    
def description(text_description):
    def decorator(func):
        func.description = text_description
        return func
    return decorator
    
class DocumentableObject():
    def __init__(self):
        pass
    
    def consolidateDocumentation(self):
        import inspect
        
        try:
            caller = inspect.stack()[1][0]; 
            members = caller.f_locals
            
            for item in members.keys():
                if True in [X in dir(members[item]) for X in ['usage', 'description']]:
                    print(item)
                    
            
        finally:
            del caller
        # print(dir(caller[myvars[0]]))
        
        # for item in (x for x in myvars):
        #     print(item, dir(item))
        #     print(type(item))
