from rocon_client_sdk_py.virtual_core.actions.base import Action
from rocon_client_sdk_py.virtual_core.components.actuators import Actuator
from rocon_client_sdk_py.utils.waiter import Waiter
import pydash


class Unlock(Action):
    def __init__(self):
        self.name = 'Unlock'
        self.func_name = 'unlock'

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
                },
                {
                    'type': 'object',
                    'key': 'quit',
                    'default': {},
                    'domain': [],
                    'options': {'user_input': False}
                }
            ]
        }

    async def on_perform(self, context, args):
        target_resource_id = pydash.find(args, {'key':'resource'})['value']
        quit_point = pydash.find(args, {'key':'quit'})['value']
        MAX_RETRY = 100
        REQUEST_INTERVAL = 100
        worker_id = context.blackboard.get_worker()

        actuator = Actuator()
        await actuator.moving(context, quit_point)

        waiter = Waiter(REQUEST_INTERVAL)
        for i in range(MAX_RETRY):
            print('return occupied resuorce {}/{}'.format(i+1, MAX_RETRY))
            target_resource = await context.api_configuration.get_resource(target_resource_id)
            target_slots = target_resource['resource_slots']
            occupied = pydash.find(target_slots, {'user_id': worker_id, 'status': 'occupied'})

            try:
                await context.api_configuration.return_resource(worker_id, target_resource_id, occupied['id'])
                return True
            except Exception as err:
                print(err)
                print('failed to return resource with error')

            await waiter.wait()

        print('exceed maximum try to return occupied resource')
        return False
