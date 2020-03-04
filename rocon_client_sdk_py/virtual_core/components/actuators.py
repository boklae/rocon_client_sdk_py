import asyncio
import pydash
import math
from rocon_client_sdk_py.virtual_core.path_planner import PathPlanner

class Actuator(): #metaclass=SingletonMetaClass):
    def __init__(self, context):
        pass

    async def change_position(self, context, destination_point, destination_map=None):
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')

        updated_type_specific = worker['type_specific']
        if 'theta' in destination_point is None:
            destination_point['theta'] = pydash(worker, 'type_specific.location.pose2d.theta')

        update = {
                'map': destination_map or worker_location['map'],
                'pose2d': destination_point or worker_location['pose2d'],
                'semantic_location': None
            }

        if 'location' in updated_type_specific:
            updated_type_specific['location'] = pydash.assign({}, updated_type_specific['location'], update)
        else:
            updated_type_specific['location'] = pydash.assign({}, update)


        context.blackboard.set_worker({'type_specific':updated_type_specific})
        await context.blackboard.sync_worker()
        print('position changed')
        return True

    async def init_path_planner(self, context):
        self.path_planner = PathPlanner(context)
        await self.path_planner.init_map()

    async def moving(self, context, destination_pose, semantic_location_id=None):


        UPDATE_INTERVAL = 500
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')


        path = self.path_planner.get_path(worker_location['map'], worker_location['pose2d'], destination_pose)
        trajectory = self.path_planner.path_to_trajectory(path, 1, UPDATE_INTERVAL)

        print('start to moving robot on path')

        def rotate_nearby(cx, cy, x, y, angle):
            radians = (math.pi/180)*angle
            cos = math.cos(radians)
            sin = math.sin(radians)
            nx = cos*(x-cx)+sin*(y-cy)+cx
            ny = cos*(y-cy)-sin*(x-cx)+cy
            return {'x':nx, 'y':ny}


        for point in trajectory:
            worker = context.blackboard.get_worker()
            updated_type_specific = worker['type_specific']

            if 'theta' in point and point['theta'] != None:
                pass
            else:
                point['theta'] = pydash.get(worker, 'type_specific.location.pose2d.theta')

            updated_type_specific['location'] = pydash.assign({}, updated_type_specific['location'], {
                'map': worker_location['map'],
                'pose2d': point,
                'semantic_location': None
            })

            #if config.get('action.move') == 'nearby' and idx == len(trajectory)-1:  조건 필요?

            context.blackboard.set_worker({'type_specific': updated_type_specific})
            await context.blackboard.sync_worker()

            #print('moving...sleep')
            await asyncio.sleep(0.1)
            #print('moving...done sleep')

        updated_type_specific = context.blackboard.get_worker()['type_specific']
        pydash.set_(updated_type_specific, 'location.semantic_location', semantic_location_id)
        context.blackboard.set_worker({'type_specific': updated_type_specific})
        await context.blackboard.sync_worker()
        return True


    async def bulldozer_moving(self, context, destination_pose, semantic_location_id=None):
        UPDATE_INTERVAL = 500
        worker = context.blackboard.get_worker()
        worker_location = pydash.get(worker, 'type_specific.location')

        path = [worker_location['pose2d'], destination_pose]
        trajectory = self.path_planner.path_to_trajectory(path, 1, UPDATE_INTERVAL)

        print('start to bulldozerMoving robot on path')

        for point in trajectory:
            updated_type_specific = worker['type_specific']
            if 'theta' in point is None:
                point['theta'] = pydash(worker, 'type_specific.location.pose2d.theta')

            updated_type_specific['location'] = pydash.assign({}, updated_type_specific['location'], {
                'map': worker_location['map'],
                'pose2d': point,
                'semantic_location': None
            })

            context.blackboard.set_worker({'type_specific': updated_type_specific})
            await context.blackboard.sync_worker()
            await asyncio.sleep(0.1)

        updated_type_specific = context.blackboard.get_worker()['type_specific']
        pydash.set_(updated_type_specific, 'location.semantic_location', semantic_location_id)
        context.blackboard.set_worker({'type_specific': updated_type_specific})
        await context.blackboard.sync_worker()
        return True