import abc

class Message(object):
    def __init__(self):
        self.name = 'Not_defined'
        self.func_name = 'Not_defined'
        self.test = 'hi'
        pass

    @abc.abstractmethod
    async def on_handler(self, context, message):
        raise NotImplementedError("Please Implement this method")
