import pydash

class HookManager():
    def __init__(self, context):
        self._context = context

    def get_hook(self, path):
        #hook = self._context.
        #pydash.get
        pass

    def call_hook(self, path, *args):
        f = self.get_hook(path)
        if f is None:
            return []

        #TODO implement here

        if pydash.is_list(f):
            def cb(h):
                pass

            results = pydash.map_(f, cb)

        if type(f) is 'function':
            return []

        else:
            print('unknown hook type')
            return []