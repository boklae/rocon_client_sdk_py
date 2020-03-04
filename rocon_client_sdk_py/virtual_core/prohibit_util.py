import pydash
import math

FIXED_DIGITS = 8

def area_to_rect(map, area):
    grid_map = pydash.get(map, 'metadata.gridmap')

    if pydash.has(grid_map, 'origin') is False:
        raise Exception('metadata.gridmap.origin is undefined')

    if pydash.has(grid_map, 'scale_m2px') is False:
        raise Exception('metadata.gridmap.scale_m2px is undefined')

    monochrome = pydash.get(map, 'metadata.monochrome')
    if monochrome is None:
        raise Exception('metadata.monochrome is undefined')


    area['x'] = round(area['x'], FIXED_DIGITS)
    area['y'] = round(area['y'], FIXED_DIGITS)
    area['theta'] = round(area['theta'], FIXED_DIGITS)
    area['width'] = round(area['width'], FIXED_DIGITS)
    area['height'] = round(area['height'], FIXED_DIGITS)


    """
        2019.12.05 DoyoungHwang

        fms에서 prohibit존을 설정할때, height가 매우 작으면, 아래의 경우,

        "areas" : [ 
            {
                "x" : 8.95535081657486,
                "y" : 15.5115164301453,
                "theta" : 0.0143874963889283,
                "width" : 31.4533251518046,
                "height" : 0.0223003822327376
            }
        ],    

        rectangle 을 표시하기 위해서는 height의 절반 value를 사용하여하 한다.
        areas가 중심 기준으로 가로폭 세로폭을 가지기 때문.

        x,y를 바탕으로 rectangle을 만드는 경우에 height/2 value가 필요한데, 이 value가
        너무 작은 경우, 픽셀좌표 (x,y)에 1의 자리수보다 작아지는 경우, pathplan을 위한 gridMap에서
        표시할 수가 없다. 따라서 상식적으로 최소한의 단위는 monochrome.height/gridmap.height/gridmap.scale_m2px
        라고 볼 수 있는데, theta value가 너무 작은경우에 인접 픽셀(1px 차이의)이 또 rectangle의 범위에 포함되지 않기 때문에
        임의로 최소라고 볼 수 있는 monochrome.height/gridmap.height/gridmap.scale_m2px의 2배를 셋팅함

        테스트로 사용하는 monochrome과 fms에서 사용하는 gridmap의 비율이 차이가 많이 나는 경우, prohibit zone이 제대로
        설정되지 않을 수 있다. 때문에 이러한 경우 추가적인 테스트가 필요함.
    """

    val = monochrome['height']/grid_map['height']/grid_map['scale_m2px']*2*2
    minimum_size = round(val, FIXED_DIGITS)

    if area['width'] <= minimum_size:
        area['width'] = minimum_size

    if area['height'] <= minimum_size:
        area['height'] = minimum_size

    xaxis = round(area['width']/2, FIXED_DIGITS)
    yaxis = round(area['height'] / 2, FIXED_DIGITS)

    lt = {'x': area['x'] - xaxis, 'y': area['y'] + yaxis}
    rt = {'x': area['x'] + xaxis, 'y': area['y'] + yaxis}
    rb = {'x': area['x'] + xaxis, 'y': area['y'] - yaxis}
    lb = {'x': area['x'] - xaxis, 'y': area['y'] - yaxis}

    rotate_lt = rotate(area['x'], area['y'], lt['x'], lt['y'], area['theta'])
    rotate_rt = rotate(area['x'], area['y'], rt['x'], rt['y'], area['theta'])
    rotate_rb = rotate(area['x'], area['y'], rb['x'], rb['y'], area['theta'])
    rotate_lb = rotate(area['x'], area['y'], lb['x'], lb['y'], area['theta'])

    temp_rect = [rotate_lt, rotate_rt, rotate_rb, rotate_lb]
    temp_rect = pydash.order_by(temp_rect, ['x', 'y'], ['asc', 'desc'])

    rotate_lt = temp_rect[0]
    rotate_lb = temp_rect[1]
    rotate_rt = temp_rect[2]
    rotate_rb = temp_rect[3]

    return {
        'lt': rotate_lt,
        'rt': rotate_rt,
        'rb': rotate_rb,
        'lb': rotate_lb,

        'A': rotate_lt,
        'B': rotate_rt,
        'C': rotate_rb,
        'D': rotate_lb
    }


def pose_to_mono_pose(map, pose):
    grid_map = pydash.get(map, 'metadata.gridmap')

    if pydash.has(grid_map, 'origin') is False:
        raise Exception('metadata.gridmap.origin is undefined')

    if pydash.has(grid_map, 'scale_m2px') is False:
        raise Exception('metadata.gridmap.scale.m2px is undefined')

    monochrome = pydash.get(map, 'metadata.monochrome')
    if monochrome is None:
        raise Exception('metadata.monochrom is undefined')

    map_point = {
        'x': grid_map['origin']['x'] + pose['x']*grid_map['scale_m2px'],
        'y': grid_map['origin']['y'] - pose['y']*grid_map['scale_m2px']
    }

    return{
        'x': round(map_point['x'] * monochrome['width']/grid_map['width'], FIXED_DIGITS),
        'y': round(map_point['y'] * monochrome['height']/grid_map['height'], FIXED_DIGITS)
    }


def rect_to_mono_rect(map, rect):
    mono_lt = pose_to_mono_pose(map, rect['lt'])
    mono_rt = pose_to_mono_pose(map, rect['rt'])
    mono_rb = pose_to_mono_pose(map, rect['rb'])
    mono_lb = pose_to_mono_pose(map, rect['lb'])

    temp_rect = [mono_lt, mono_rt, mono_rb, mono_lb]
    temp_rect = pydash.order_by(temp_rect, ['x', 'y'], ['asc', 'desc'])

    mono_lt = temp_rect[0]
    mono_lb = temp_rect[1]
    mono_rt = temp_rect[2]
    mono_rb = temp_rect[3]

    return {
        'lt': mono_lt,
        'rt': mono_rt,
        'rb': mono_rb,
        'lb': mono_lb,

        'A': mono_lt,
        'B': mono_rt,
        'C': mono_rb,
        'D': mono_lb
    }


def vector(p1, p2):
    return {
        'x': round(p2['x'] - p1['x'], FIXED_DIGITS),
        'y': round(p2['y'] - p1['y'], FIXED_DIGITS)
    }


def dot(u, v):
    return round(u['x']*v['x'] + u['y']*v['y'], FIXED_DIGITS)


def is_point_in_rect(pose, rect):
    AB = vector(rect['A'], rect['B'])
    Apose = vector(rect['A'], pose)
    BC = vector(rect['B'], rect['C'])
    Bpose = vector(rect['B'], pose)
    dotABApose = dot(AB, Apose)
    dotABAB = dot(AB, AB)
    dotBCBpose = dot(BC, Bpose)
    dotBCBC = dot(BC, BC)

    return 0 <= dotABApose and dotABApose <= dotABAB and 0 <= dotBCBpose and dotBCBpose <= dotBCBC


def rotate(cx, cy, x, y, angle):
    radians = angle
    cos = math.cos(radians)
    sin = math.sin(radians)
    nx = cos*(x-cx)-sin*(y-cy) + cx
    ny = cos*(y-cy)+sin*(x-cx) + cy

    return {
        'x': round(nx, FIXED_DIGITS),
        'y': round(ny, FIXED_DIGITS)
    }
