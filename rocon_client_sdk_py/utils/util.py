from datetime import datetime
import time
from datetime import datetime
import yaml


class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMetaClass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def get_time_sec(dtstr):
    #now = dt.now()
    dtstr = dtstr.replace('T', ' ')
    dtstr = dtstr.replace('Z', '')
    dtn = datetime.strptime(dtstr, '%Y-%m-%d %H:%M:%S.%f')


    curnt_time_sec = time.mktime(dtn.timetuple()) + dtn.microsecond/1000000.0
    curnt_time_ms = curnt_time_sec*1000

    return curnt_time_sec


def get_time_milliseconds(dtstr):
    """
    :param dtn: string datetime format as '%Y-%m-%dT%H:%M:%S.%f'
    :return:
    """
    sec = get_time_sec(dtstr)
    return sec*1000


def current_datetime_utc_iso_format():
    utc_datetime = datetime.utcnow()

    isostring = datetime.strftime(utc_datetime, '%Y-%m-%dT%H:%M:%S.{0}Z')
    #print(isostring)
    return isostring.format(int(round(utc_datetime.microsecond/1000.0)))


def load_dict_from_yaml(filepathname) -> dict:
    try:
        config_dic = yaml.load(open(filepathname), Loader=yaml.FullLoader)
        print(config_dic)

        return config_dic
    except yaml.YAMLError as exc:
        print(exc)
        return None