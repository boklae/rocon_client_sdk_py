import pydash
from rocon_client_sdk_py.virtual_core.actions.base import Action
from rocon_client_sdk_py.virtual_core.components.actuators import Actuator
from rocon_client_sdk_py.virtual_core.components.autodoor_consumer import AutodoorConsumer
from rocon_client_sdk_py.virtual_core.components.elevator_consumer import ElevatorConsumer
from rocon_client_sdk_py.utils.waiter import Waiter


class UseResource(Action):
    def __init__(self):
        self.name = 'Use Resource'
        self.func_name = 'use_resource'
        self._actuator = None

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
                    'key': 'resource_id',
                    'type': 'string',
                    'default': resource_list[0],
                    'domain': resource_list,
                },
                {
                    'key': 'resource_type',
                    'type': 'string',
                    'enum': ['ExclusiveArea', 'Autodoor', 'Teleporter'],
                    'default': {'alias': 'ExclusiveArea', 'value': 'ExclusiveArea'},
                    'domain': [
                        {'alias': 'ExclusiveArea', 'value': 'ExclusiveArea'},
                        {'alias': 'Autodoor', 'value': 'Autodoor'},
                        {'alias': 'Elevator', 'value': 'Teleporter'}
                    ]
                },
                {
                    'key': 'params',
                    'type': 'object',
                    'default': {},
                    'domain': {}
                }
            ]
        }

    def get_arg_value(self, args, key):
        arg = pydash.find(args, {'key': key})
        if arg:
            return arg['value']

        return None

    async def perform_autodoor(self, context, target_autodoor):
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')

        aligns = target_autodoor['aligns']
        if worker_location['map'] != target_autodoor['map']:
            print('perform_autodoor : does not match worker\'s current map with target resources {}'.format({
                'worker_map': worker_location['map'],
                'resource_map': target_autodoor['map']
            }))

            raise Exception('perform_autodoor : does not match worker\'s current map with target resources')

        if self._actuator is None:
            self._actuator = Actuator(context)
            await self._actuator.init_path_planner(context)

        #TODO Promise.all 대응 루틴 확인 필요
        def cb(point):

            path = self._actuator.path_planner.get_path(target_autodoor['map'], worker_location['pose2d'], point)
            point['distance'] = self._actuator.path_planner.get_distance(path)
            return point

        aligns = pydash.map_(aligns, cb)
        aligns = pydash.sort_by(aligns, 'distance')
        entry = aligns[0]
        exit = aligns[len(aligns) - 1]


        autodoor_consumer = AutodoorConsumer()

        #1. move to entry point
        await self._actuator.moving(context, entry)
        #2. request door open
        await autodoor_consumer.request_open_autodoor(target_autodoor['id'], context)
        #3. waiting autodoor open
        await autodoor_consumer.ensure_autodoor_opened(target_autodoor['id'], context)
        #4. move to exit point
        await self._actuator.moving(context, exit)
        #5. close door
        await autodoor_consumer.request_close_autodoor(target_autodoor['id'], context)
        await autodoor_consumer.ensure_autodoor_closed(target_autodoor['id'], context)
        #6. release autodoor resource
        await context.api_configuration.return_resource(worker['id'], target_autodoor['id'])
        return True

    async def perform_teleporter(self, context, target_teleporter, params):
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')

        destination_map_id = params['destination_map_id']
        departure_map_id = params['departure_map_id']

        if worker_location['map'] != departure_map_id:
            print('cannot process use_resource: Teleporter: departure map{} is not same with worker\'s current map{}'.format(departure_map_id, worker_location['map']))
            return False

        entry_gate = await context.api_configuration.get_teleporter_gate(target_teleporter['id'], departure_map_id)
        exit_gate = await context.api_configuration.get_teleporter_gate(target_teleporter['id'], destination_map_id)

        entry_point = pydash.get(entry_gate, 'aligns.entries.0')
        exit_point = pydash.get(exit_gate, 'aligns.exits.0')

        elevator_consumer = ElevatorConsumer()

        #1. waiting elevator arrive
        service_id = await elevator_consumer.call_elevator(context, target_teleporter, entry_gate, exit_gate)
        result = await elevator_consumer.ensure_elevator_door_open(context, target_teleporter['id'])
        if result is False:
            return False

        print('elevator door opened and ready to ride')

        #2. move to entry point
        await self._actuator.moving(context, entry_point)
        #3. move to center of elevator gate
        await self._actuator.bulldozer_moving(context, pydash.pick(entry_gate['area'], ['x', 'y', 'theta']))
        #4. close door
        try:
            result = await elevator_consumer.close_elevator_door(context, target_teleporter['id'], service_id, 'board', 'success')
            if result is False:
                print('failed to closeElevatorDoor after ride elevator')
                return False
        except Exception as err:
            print(err)
            raise Exception(err)

        result = await elevator_consumer.ensure_elevator_door_closed(context, target_teleporter['id'])
        #TODO result가 faise로 넘어오는것 확인
        if result is False:
            print('failed to ensureElevatorDoorClosed after riding elevator')

        print('elevator door closed after ride elevator')

        #5. ensure elevator door open before unboard elevator
        result = await elevator_consumer.ensure_elevator_door_open(context, target_teleporter['id'])
        if result is False:
            return False

        print('elevator door opened and ready to ride')

        #6. change map to destination map (initial location is exit of destination gate)
        print('request change position with map')
        await self._actuator.change_position(context, pydash.pick(exit_gate['area'], ['x', 'y', 'theta']), exit_gate['map'])
        #7. move exit point
        await self._actuator.bulldozer_moving(context, exit_point)
        #8. close door
        if await elevator_consumer.close_elevator_door(context, target_teleporter['id'], service_id, 'unboard', 'success') is False:
            print('failed to closeElevatorDoor after unboard elevator')
            return False

        print('elevator door closed after unboard elevator')
        await context.api_configuration.return_resource(pydash.get(worker, 'id'), target_teleporter['id'])
        print('resource returned')
        return True

    async def perform_narrow_corridor(self, context, target_resource):
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')

        # In case of using narrow corridor
        # 1. calculate distances between robot and align points
        aligns = target_resource['aligns']
        if worker_location['map'] != target_resource['map']:
            print('perform_narrow_corridor: does not mathc worker\'s current map with target resources', {
                'worker_map': worker_location['map'],
                'resource_map': target_resource['map']
            })

            raise Exception('perform_narrow_corridor: does not match worker\'s current map with target resources worker_map:{}, resource_map: {}'.format(worker_location['map'], target_resource['map']))

        if self._actuator is None:
            self._actuator = Actuator(context)
            await self._actuator.init_path_planner(context)

        # TODO Promise.all 대응 루틴 확인 필요
        def cb(point):

            path = self._actuator.path_planner.get_path(target_resource['map'], worker_location['pose2d'], point)
            point['distance'] = self._actuator.path_planner.get_distance(path)
            return point

        aligns = pydash.map_(aligns, cb)
        aligns = pydash.sort_by(aligns, 'distance')
        entry = aligns[0]
        exit = aligns[len(aligns) - 1]

        # 2. move to nearest align point
        await self._actuator.moving(context, entry)
        # 3. move to farther align point
        await self._actuator.moving(context, exit)
        # 4. return occupied resource slot
        MAX_RETRY = 100
        REQUEST_INTERVAL = 100
        worker_id = worker['id']
        waiter = Waiter(REQUEST_INTERVAL)

        for i in range(MAX_RETRY):
            print('return occupied resource {}/{}'.format(i+1, MAX_RETRY))
            target_slots = target_resource['resource_slots']
            occupied = pydash.find(target_slots, {'user_id': worker_id, 'status': 'occupied'})

            try:
                await context.api_configuration.return_resource(worker_id, target_resource['id'], occupied['id'])
                return True
            except Exception as err:
                print('failed to return resource with error')

            await waiter.wait()

        print('exceed maximum try to return occupied resource')
        return False

    async def on_perform(self, context, args):
        resource_id = self.get_arg_value(args, 'resource_id')
        resource_type = self.get_arg_value(args, 'resource_type')
        instruction_param = self.get_arg_value(args, 'params')
        target_resource = await context.api_configuration.get_resource(resource_id)

        if resource_type == 'ExclusiveArea':
            return await self.perform_narrow_corridor(context, target_resource)
        elif resource_type == 'Autodoor':
            return await self.perform_autodoor(context, target_resource)
        elif resource_type == 'Teleporter':
            return await self.perform_teleporter(context, target_resource, instruction_param)
        else:
            print('unhandled resource type: {}'.format(resource_type))
            return False
