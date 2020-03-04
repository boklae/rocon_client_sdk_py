import pydash
from rocon_client_sdk_py.virtual_core.actions.base import Action
from rocon_client_sdk_py.virtual_core.components.actuators import Actuator


class Move(Action):
    def __init__(self):
        self.name = 'Move'
        self.func_name = 'move'

    async def on_define(self, context):
        print('define action of ' + self.name)
        domain_goal_finishing = [{'alias': 'True', 'value': True}, {'alias': 'False', 'value': False}]

        api_config = context.api_configuration
        result = await api_config.get_locations()

        domain_destination = []
        def cb(location):
            domain_destination.append({'alias':location['name'], 'value':location['id']})

        pydash.map_(result, cb)

        return {
            'name': self.name,
            'func_name': self.func_name,
            'args': [
                {
                    'key': 'destination',
                    'options': {
                        'min': 0,
                        'user_input': False,
                        'max': 0
                    },
                    'default': domain_destination[0],
                    'domain': domain_destination,
                    'type': 'string'
                },
                {
                    'key': 'goal_finishing',
                    'type': 'boolean',
                    'default': domain_goal_finishing[0],
                    'domain': domain_goal_finishing,
                },
                {
                    'key': 'finishing_timeout',
                    'type': 'number',
                    'default': 30,
                    'domain': [0, 10, 20, 30, 40, 50, 60],
                    'options': {
                        'user_input': True,
                        'min': 0,
                        'max': 300
                    }
                }
            ]
        }

    async def on_perform(self, context, args):
        print('perform')

        destination_id = pydash.find(args, {'key': 'destination'})['value']
        #await path_planner

        destination = await context.api_configuration.get_locations(destination_id=destination_id)
        print('get destination object from site configuration server')

        if destination is None:
            print('failed to get destination')

        actuator = Actuator(context)
        await actuator.init_path_planner(context)

        await actuator.moving(context, destination['pose'], destination_id)
        return True
