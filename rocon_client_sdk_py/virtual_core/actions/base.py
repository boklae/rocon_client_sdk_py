import abc

class Action(object):
    def __init__(self):
        self.name = 'Not_defined'
        self.func_name = 'Not_defined'
        self.test = 'hi'
        pass

    @abc.abstractmethod
    async def on_define(self, context):
        raise NotImplementedError("Please Implement this method")

    @abc.abstractmethod
    async def on_perform(self, context):
        raise NotImplementedError("Please Implement this method")

