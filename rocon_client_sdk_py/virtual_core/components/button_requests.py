from rocon_client_sdk_py.logic.context import Context

import pydash

BBKEY_BUTTON_REQUESTS = 'buttonRequests'

class ButtonRequests():
    def __init__(self, context:Context):
        self._context = context
        self._button_req = []

        self._load()

    def _load(self):
        self._button_req = self._context.blackboard.get(BBKEY_BUTTON_REQUESTS) or []
        return self._button_req

    def save(self):
        self._context.blackboard.set(BBKEY_BUTTON_REQUESTS, self._button_req)
        return self._button_req

    def set_button_request(self, button_request):
        self._load()
        target_idx = pydash.find_index(self._button_req, pydash.pick(button_request, ['button_id', 'uuid']))
        if target_idx != -1:
            self._button_req[target_idx] = button_request
        else:
            self._button_req.append(button_request)

        self.save()
        return self._button_req

    def remove_button_request(self, button_id, uuid):
        self._load()
        target_idx = pydash.find_index(self._button_req, {'button_id': button_id, 'uuid': uuid})
        if target_idx != -1:
            pydash.pull_at(self._button_req, target_idx)
        else:
            print('cannot remove button request')

        self.save()
        print('buttonRequest removed')
        return self._button_req

    def find_request_by_button_id(self, button_id, uuid):
        self._load()
        target_idx = pydash.find_index(self._button_req, {'button_id': button_id, 'uuid': uuid})
        if target_idx == -1:
            return None

        return self._button_req[target_idx]

    def find_request_by_button(self, button, uuid):
        self._load()
        target_idx = pydash.find_index(self._button_req, {'button': button, 'uuid': uuid})
        if target_idx == -1:
            return None

        return self._button_req[target_idx]

    def process(self, button_request, data):
        try:
            subj = button_request['notify']
            subj.on_next(data)
            subj.on_completed()
            self.remove_button_request(button_request['button_id'], button_request['uuid'])
            return button_request

        except Exception as err:
            self.remove_button_request(button_request['button_id'], button_request['uuid'])
            print('cannot process buttonReqest')
            return None

    def process_request_by_id(self, buton_id, uuid, data):
        request = self.find_request_by_button_id(buton_id, uuid)
        if request is None:
            print('cannot found button request for this id:'.format(buton_id))
            return None

        return self.process(request, data)

    def process_request_by_button(self, button, uuid, data):
        request = self.find_request_by_button(button, uuid)
        if request is None:
            print('cannot found button requeest for this button: '.format(button))
            return None

        return self.process(request, data)