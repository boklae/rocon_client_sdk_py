from rocon_client_sdk_py.virtual_core.message_handlers.base import Message
import pydash


class ResetLocation(Message):
    def __init__(self):
        self.name = 'resetLocation'

    async def on_handler(self, context, message):

        worker = context.blackboard.get_worker()
        location = pydash.get(worker, 'type_specific.location')
        updated_type_specific = worker['type_specific']
        updated_type_specific['location'] = pydash.assign({}, location, message)
        context.blackboard.set_worker({'type_specific': updated_type_specific})
        await context.blackboard.sync_worker()
        return True