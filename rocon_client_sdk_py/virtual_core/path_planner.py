from rocon_client_sdk_py.utils.util import *
from rocon_client_sdk_py.logic.context import Context
from PIL import ImageDraw
from pathfinding.core.grid import Grid
from pathfinding.finder.best_first import BestFirst
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.util import smoothen_path
from .prohibit_util import *
import copy
import sys

class PathPlanner():
    def __init__(self, context:Context):
        self._context = context
        self._path_map = {}
        self._grid_map_images = {}
        self._maps = None

        print('pathPlanner has been initialized')

    async def init_map(self):
        start_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())

        print('pathPlanner initiating...')
        found_map = await self._context.api_configuration.get_maps()

        def cb(map):
            return pydash.get(map, 'site') and pydash.get(map, 'site') != None

        self._maps = pydash.filter_(found_map, cb)
        self._grid_map_images ={}

        for map in self._maps:
            self._path_map[map['id']], self._grid_map_images[map['id']]= await self.load_map(map)


        print('done PathPlanner._init')

        end_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())
        gap = end_time_ms - start_time_ms
        print('Required time msec of init_map : {}'.format(gap))

    def get_path(self, map, pose_a, pose_b):
        if isinstance(map, str):
            map = pydash.find(self._maps, {'id':map}) or map
        else:
            map = pydash.find(self._maps, {'id': map['id']}) or map

        mono_point_a = self.pose_to_mono(map, pose_a)
        mono_point_b = self.pose_to_mono(map, pose_b)

        valid = True
        if self._path_map[map['id']] is None:
            print('getPath() : pathMap was not loaded for map')
            valid = False

        gpx_a = self.get_monochrome_pixel(map, mono_point_a['x'], mono_point_a['y'])
        if gpx_a:
            if gpx_a.walkable is False:
                print('[pathPlanner]: getPath(): departure point is located in nonwalkable position')
                valid = False

        else:
            print('[pathPlanner]: getPath(): departure point is out of gridmap range')
            valid = False

        gpx_b = self.get_monochrome_pixel(map, mono_point_b['x'], mono_point_b['y'])
        if gpx_b is None:
            valid = False

        else:
            if gpx_b.walkable is False:
                print('[pathPlanner]: getPath(): departure point is out of gridmap range')
                valid = False

        if valid is False:
            return []

        #finder = AStarFinder() #diagonal_movement=DiagonalMovement.always, weight=1)
        finder = BestFirst(diagonal_movement=DiagonalMovement.always,weight=1)
        #finder = DijkstraFinder(diagonal_movement=DiagonalMovement.always, weight=1)


        grid = self._path_map[map['id']]
        clone_grid = copy.copy(grid)

        path = None
        try:
            print('\n')
            print('** find_path : ({},{}) -> ({},{})'.format(gpx_a.x, gpx_a.y, gpx_b.x, gpx_b.y))

            path, runs = finder.find_path(gpx_a, gpx_b, clone_grid)
            print('done find_path')
            print('operations:', runs, 'path length:', len(path))

            #img = self._grid_map_images[map['id']].copy()
            #self.draw_path(img, path, color_path='blue', radius=1)
            #print(grid.grid_str(path=path, start=gpx_a, end=gpx_b))

        except Exception as err:
            print('[check here.. path_planner] exception error')
            print(err)


        if path and len(path) > 0:

            clone_grid.cleanup()

            if len(path) > 1:
                path2 = smoothen_path(clone_grid, path, use_raytrace=False)
            else:
                path2 = path
            #self.draw_path(img, path2, color_path='green', radius=1)

            path3 = pydash.map_(path2, lambda point: {'x':point[0], 'y':point[1]})
            pose_path = self.grid_path_to_pose_path(map, path3)

            return pose_path
        else:
            print('[check here.. path_planner] Not found path')
            return []

    def draw_path(self, img, path, color_path='blue', radius=1):
        draw = ImageDraw.Draw(img)

        for i, pos in enumerate(path):
            if i == 0:
                # start point
                point_radius = radius
                color = 'red'
            elif i == len(path) - 1:
                point_radius = radius
                color = 'red'
            else:
                # end point
                point_radius = radius
                color = color_path

            rect = (pos[0] - point_radius, pos[1] - point_radius, pos[0] + point_radius, pos[1] + point_radius)
            draw.ellipse(rect, fill=color)

        #img.show()

    def get_monochrome_pixel(self, map, x, y):
        path_map = self._path_map[map['id']]
        if path_map is None:
            print('pathMap is not loaded')
            return None

        if x > path_map.width or y > path_map.height:
            print('get_monochrome_pixel: Coordinates must be smaller than gridmap size')
            return None
        elif x < 0 or y < 0:
            print('get_monochrome_pixel: Coordinates must be positive')
            return None

        return path_map.nodes[y][x]

    def path_to_trajectory(self, path, v, dt):
        step_size = (v*dt)/1000
        trajectory = []

        if path is None or len(path) == 0:
            return []

        trajectory.append(path[0])
        for idx in range(0, len(path)-1):
            before = path[idx]
            after = path[idx + 1]
            distance = self.get_distance_pose_to_pose(before, after)
            direction = self.get_angle_rad(before, after)

            n = 1
            if distance-n*step_size > step_size:
                while(distance-n*step_size > step_size):
                    pose_n = {
                        'x': before['x'] + ((after['x'] - before['x'])*step_size*n)/distance,
                        'y': before['y'] + ((after['y'] - before['y'])*step_size*n)/distance,
                        'theta':direction
                    }

                    trajectory.append(pose_n)
                    n += 1

                trajectory.append(after)
            else:
                """
                    blcho@
                    python 버전의 pathfinding 모듈의 path 결과 sampling data 수가 조밀하여 매 point 사이의 direction 계산해서 넣어준다.
                    
                """
                after = pydash.assign(after, {'theta': direction})


            trajectory.append(after)



        return trajectory

    def mono_to_pose(self, map, point_on_monochrome):
        mono = self.get_monochrome_metadata(map)
        grid = self.get_gridmap_metadata(map)

        map_point = {
            'x': (point_on_monochrome['x']*grid['width'])/mono['width'],
            'y': (point_on_monochrome['y']*grid['height'])/mono['height']
        }
        return self.map_to_pose(map, map_point)

    def pose_to_mono(self, map, pose):
        map_point = self.pose_to_map(map, pose)
        mono = self.get_monochrome_metadata(map)
        grid = self.get_gridmap_metadata(map)

        return{
            'x': round((map_point['x']*mono['width'])/grid['width']),
            'y': round((map_point['y']*mono['height'])/grid['height'])
        }

    def pose_to_map(self, map, pose):
        origin = self.get_origin_coordinate(map)
        scale = self.get_scale_meter_to_pixel(map)
        return {
            'x': origin['x'] + pose['x']*scale,
            'y': origin['y'] - pose['y']*scale
        }

    def map_to_pose(self, map, map_point):
        origin = self.get_origin_coordinate(map)
        scale = self.get_scale_meter_to_pixel(map)

        return{
            'x': (map_point['x'] - origin['x'])/scale,
            'y': (origin['y'] - map_point['y']) / scale
        }

    def get_monochrome_metadata(self, map):
        monochrome = pydash.get(map, 'metadata.monochrome')
        if monochrome is None:
            print('map record is malformed "metadata.monochrome" is undefined')

        return monochrome

    def get_origin_coordinate(self, map):
        origin = pydash.get(map, 'metadata.gridmap.origin')
        if origin is None:
            print('map record is malformed "metadata.gridmap.origin" is undefined')

        return origin

    def get_gridmap_metadata(self, map):
        gridmap = pydash.get(map, 'metadata.gridmap')
        if gridmap is None:
            print('map record is malformed "metadata.gridmap" is undefined')

        return gridmap

    def get_scale_meter_to_pixel(self, map):
        scale = pydash.get(map, 'metadata.gridmap.scale_m2px')
        if scale is None:
            print('map record is malformed "metadata.gridmap.scale_m2px" is undefined')

        return scale

    def get_distance_pose_to_pose(self, pose_a, pose_b):
        dx = pose_a['x'] - pose_b['x']
        dy = pose_a['y'] - pose_b['y']
        return math.sqrt(dx*dx + dy*dy)

    def get_distance(self, path):
        if len(path) == 0:
            return sys.maxsize

        distance = 0
        for i in range(len(path)-1):
            distance += self.get_distance_pose_to_pose(path[i+1], path[i])

        return distance

    def get_angle_rad(self, pose_a, pose_b):
        return math.atan2(pose_b['y'] - pose_a['y'], pose_b['x'] - pose_a['x'])

    def grid_path_to_pose_path(self, map, path):
        return pydash.map_(path, lambda point: self.mono_to_pose(map, point))

    async def load_map(self, map):

        grid_map_image = None

        try:
            grid_map_image = await self._context.api_configuration.get_map_image('/public/' + pydash.get(map, 'files.monochrome'))

        except Exception as err:
            print(err)
            err.with_traceback()
            return None

        print(grid_map_image)
        w = grid_map_image.width
        h = grid_map_image.height

        new_grid_map = Grid(w, h)
        non_walkable = 0

        prohibit_zones = await self._context.api_configuration.get_zones('prohibit', map['id'])
        print(prohibit_zones)
        prohibits_mono_rects = []


        for zone in prohibit_zones:
            rect = area_to_rect(map, zone['areas'][0])
            mono_rect = rect_to_mono_rect(map, rect)
            prohibits_mono_rects.append(mono_rect)

        px = grid_map_image.load()
        print('image rows :{}'.format(grid_map_image.size[0]))
        print('image cols :{}'.format(grid_map_image.size[1]))

        start_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())

        #grid_map_image.show()
        """
            @blcho,
            처리 속도를 높이기 위해 prohibits zone을 mono 이미지에 black처리해서 non walkable zone으로 먼저 만든다.
        """

        for rect in prohibits_mono_rects:
            print(rect)
            ltx = rect['lt']['x']
            lty = rect['lt']['y']

            rtx = rect['rt']['x']
            rty = rect['rt']['y']

            rbx = rect['rb']['x']
            rby = rect['rb']['y']

            lbx = rect['lb']['x']
            lby = rect['lb']['y']

            coords = [(ltx, lty), (rtx, rty), (rbx, rby), (lbx, lby)]
            draw = ImageDraw.Draw(grid_map_image)
            draw.polygon(coords, fill="#000000")



        for y in range(w):
            for x in range(h):
                rgb_tuple = px[y, x]
                pixel_value = 0 if rgb_tuple[0] == 0 and rgb_tuple[1] == 0 and rgb_tuple[2] == 0 else 1
                node = new_grid_map.node(y, x)

                if pixel_value == 0:
                    node.walkable = False
                    non_walkable += 1
                else:
                    node.walkable = True


                    """
                    #위에서 prohibit zone 을 mono 이미지에 black 처리해 속도를 높인다.
                    for rect in prohibits_mono_rects:
                        is_in_rect = is_point_in_rect({'x':x, 'y':y}, rect)
                        if is_in_rect:
                            non_walkable += 1
                            #node = new_grid_map.node(y, x)
                            node.walkable = False
                            break
                    """




        end_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())
        gap = end_time_ms - start_time_ms
        print('Required time msec of load_map loop : {}'.format(gap))
        print('Non walkerble count : {}'.format(non_walkable))

        #grid_map_image.show()
        print('end')

        return new_grid_map, grid_map_image

    async def load_map_origin(self, map):

        grid_map_image = None

        try:
            grid_map_image = await self._context.api_configuration.get_map_image('/public/' + pydash.get(map, 'files.monochrome'))

        except Exception as err:
            print(err)
            err.with_traceback()
            return None

        print(grid_map_image)
        w = grid_map_image.width
        h = grid_map_image.height

        new_grid_map = Grid(w, h)
        non_walkable = 0

        prohibit_zones = {}
        prohibit_zones = await self._context.api_configuration.get_zones('prohibit', map['id'])
        print(prohibit_zones)
        prohibits_mono_rects = []


        for zone in prohibit_zones:
            rect = area_to_rect(map, zone['areas'][0])
            mono_rect = rect_to_mono_rect(map, rect)
            prohibits_mono_rects.append(mono_rect)



        px = grid_map_image.load()
        print('image rows :{}'.format(grid_map_image.size[0]))
        print('image cols :{}'.format(grid_map_image.size[1]))

        start_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())

        for y in range(grid_map_image.size[0]):
            for x in range(grid_map_image.size[1]):
                rgb_tuple = px[y, x]
                pixel_value = self.rgb_to_int(rgb_tuple)
                node = new_grid_map.node(y, x)

                if pixel_value == 0:
                    node.walkable = False
                    non_walkable += 1
                else:
                    node.walkable = True

                #if new_grid_map.node(y, x).walkable:
                #if node.walkable == True:
                    for rect in prohibits_mono_rects:
                        is_in_rect = is_point_in_rect({'x':x, 'y':y}, rect)
                        if is_in_rect:
                            non_walkable += 1
                            node = new_grid_map.node(y, x)
                            node.walkable = False
                            break



        end_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())
        gap = end_time_ms - start_time_ms
        print('Required time msec of load_map loop : {}'.format(gap))

        #grid_map_image.show()
        print('end')

        grid_map_image.close()

        return new_grid_map

    def rgb_to_int(self, rgb_tuple):
        rgb_int = rgb_tuple[0] << 16 | rgb_tuple[1] << 8 | rgb_tuple[2]
        return rgb_int