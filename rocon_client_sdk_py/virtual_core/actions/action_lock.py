from rocon_client_sdk_py.virtual_core.actions.base import Action
from rocon_client_sdk_py.utils.waiter import Waiter
import pydash


class Lock(Action):
    def __init__(self):
        self.name = 'Lock'
        self.func_name = 'lock'

    async def on_define(self, context):
        print('define action of ' + self.name)
        api_config = context.api_configuration
        result = await api_config.get_resources()

        resources = pydash.filter_(result, {'resource_type': 'ExclusiveArea'})

        resource_list = []
        def cb(resource):
            resource_list.append(
                {'alias': resource['name'], 'value': resource['id']})

        pydash.map_(resources, cb)

        return {
            'name': self.name,
            'func_name': self.func_name,
            'args': [
                {
                    'type': 'string',
                    'key': 'resource',
                    'default': resource_list[0],
                    'domain': resource_list,
                    'options':{'user_input': False}
                }
            ]
        }

    async def on_perform(self, context, args):
        target_resource_id = pydash.find(args, {'key': 'resource'})['value']
        MAX_RETRY = 100
        REQUEST_INTERVAL = 100
        work_id = context.blackboard.get_worker()['id']

        waiter = Waiter(REQUEST_INTERVAL)
        for i in range(MAX_RETRY):
            print('check resource have assigned to this worker {}/{}'.format(i+1, MAX_RETRY))
            target_resource = await context.api_configuration.get_resource(target_resource_id)
            target_slots = target_resource['resource_slots']
            occupied = pydash.find(target_slots, {'user_id': work_id, 'status':'occupied'})
            if occupied:
                print('confirmed : resource have assigned to this worker')
                return True

            await waiter.wait()

        print('exceed maximum try to check resource have assigned to this worker')
        return False