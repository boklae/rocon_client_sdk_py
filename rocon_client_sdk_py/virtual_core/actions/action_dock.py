from rocon_client_sdk_py.virtual_core.actions.base import Action
import asyncio
import pydash
from rocon_client_sdk_py.virtual_core.path_planner import PathPlanner


class Dock(Action):
    def __init__(self):
        self.name = 'Dock'
        self.func_name = 'dock'

    async def on_define(self, context):
        print('define action of ' + self.name)
        api_config = context.api_configuration
        result = await api_config.get_stations()

        domain_station = []

        def cb(station):
            domain_station.append({'alias': station['name']+'('+str(station['marker_value'])+')', 'value': station['id']})

        pydash.map_(result, cb)

        return {
            'name': self.name,
            'func_name': self.func_name,
            'args': [
                {
                    'key': 'station',
                    'type': 'number',
                    'default': domain_station[len(domain_station) -1],
                    'domain': domain_station
                }
            ]
        }

    async def on_perform(self, context, args):
        station_id = pydash.find(args, {'key': 'station'})['value']
        station = await context.api_configuration.get_stations(station_id)

        if station is None:
            print('failed to get station')

        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')
        path_planner = PathPlanner(context)
        await path_planner.init_map()

        path = path_planner.get_path(worker_location['map'], worker_location['pose2d'], station['pose'])
        trajectory = path_planner.path_to_trajectory(path, 1, 1000)

        print('start to moving robot on path')

        for point in trajectory:
            worker = context.blackboard.get_worker()
            updated_type_specific = worker['type_specific']
            if 'theta' in point:
                pass
            else:
                point['theta'] = pydash.get(worker, 'type_specific.location.pose2d.theta')

            updated_type_specific['location'] = pydash.assign({}, updated_type_specific['location'], {
                'map': worker_location['map'],
                'pose2d': point
            })

            context.blackboard.set_worker({'type_specific': updated_type_specific})
            await context.blackboard.sync_worker()
            await asyncio.sleep(1)

        updated_type_specific['location']['pose2d']['theta'] = station['pose']['theta']
        context.blackboard.set_worker({'type_specific': updated_type_specific})
        await context.blackboard.sync_worker()
        await asyncio.sleep(1)
        return True
