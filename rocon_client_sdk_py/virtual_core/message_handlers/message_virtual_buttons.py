from rocon_client_sdk_py.virtual_core.message_handlers.base import Message
from rocon_client_sdk_py.virtual_core.components.button_requests import ButtonRequests


class VirtualButtons(Message):
    def __init__(self):
        self.name = 'virtualButtons'

    async def on_handler(self, context, message):
        print('have got virtualButtons message: {}'.format(message))
        button_requests = ButtonRequests(context)

        if button_requests.process_request_by_button(message, context.worker.uuid, message) is None:
            if message == 'O':
                print('pause called!! it is not implemented yet.')
            elif message == 'E_PUSH':
                print('emergency called!! it is not implemented yet.')

        return True