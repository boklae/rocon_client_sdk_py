"""
This is test doc
"""
import pydash
from rocon_client_sdk_py.apis.httpclient import HttpClient
from abc import ABC, abstractmethod
from threading import Timer
from rocon_client_sdk_py.logic.trees.trees_manager import BehaviorTreeManager
from rocon_client_sdk_py.logic.context import Context

class Worker(ABC):
    """
    Worker class
    """

    def __init__(self, uuid, act_def_paths, msg_def_paths, options: dict, event_loop = None):
        """
        :param uuid:            - name of virtualWorker
        :param act_def_paths:   - path of action files
        :param msg_def_paths:   - path of message_handlers
        :param options:         - options object {tickInterval, updateInterval, initWork, configs}
        """
        self._uuid = uuid
        self._act_def_paths = act_def_paths
        self._msg_def_paths = msg_def_paths
        self._options = options

        self._call_back_after_tick = None

        if event_loop:
            self.initialize(event_loop)

    def initialize(self, event_loop):

        # TODO
        self._logger = None

        self._tick_interval = pydash.get(self._options, 'tickInterval') or 1000
        self._update_interval = pydash.get(self._options, 'updateInterval') or 2000

        self._initial_worker = pydash.get(self._options, 'initialWorker') or {}
        self._configs = pydash.get(self._options, 'configs') or {}

        self._httpclient = self._init_http_client()

        # ??
        self._ticker = None
        self._tick_timer = None

        self._event_loop = event_loop
        self._context = Context(self, event_loop)

        self._tree_manager = BehaviorTreeManager(self._context)
        self._tree_manager.blackboard.set('uuid', self._uuid)
        self._tree_manager.blackboard.set('configs', self._configs)
        self._tree_manager.blackboard.set('actionDefinePaths', self._act_def_paths)
        self._tree_manager.blackboard.set('messageDefinePaths', self.msg_def_paths)
        self._tree_manager.blackboard.set('tickInterval', self._tick_interval)
        self._tree_manager.blackboard.set('updateInterval', self._update_interval)

    @property
    def uuid(self):
        return self._uuid

    @property
    def act_def_paths(self):
        return self._act_def_paths

    @property
    def msg_def_paths(self):
        return self._msg_def_paths

    @property
    def httpclient(self):
        return self._httpclient

    @property
    def event_loop(self):
        return self._event_loop

    def _init_http_client(self):
        hostname = pydash.get(self._configs, 'hostname.concert')
        siteconf = pydash.get(self._configs, 'hostname.siteConfig')

        httpclient = HttpClient(hostname_concert=hostname, hostname_site_config=siteconf)
        return httpclient

    def reset(self):
        self._initialize(self._uuid, self._act_def_paths, self._msg_def_paths, self._options, self._event_loop)

    def reset_blackboard(self):
        self._tree_manager.blackboard.reset_blackboard()


    def tick(self):
        print('tick')
        self._tree_manager.tick()

        self.after_tick(self.context)


    def after_tick(self, context):
        print('done after_tick')

        if self._call_back_after_tick:
            self._call_back_after_tick(context)


    @property
    def context(self):
        return self._context

    @property
    def tree_manager(self):
        return self._tree_manager

    @abstractmethod
    async def on_core_logic_task_hook_handler(self, context, task_name, to_do, *args):
        raise NotImplementedError("Please Implement this method")

    @property
    def tick_interval(self):
        return self._tick_interval

    @tick_interval.setter
    def tick_interval(self, interval):
        self._tick_interval = interval

    def to_json(self):
        json_data = {
            'uuid': self._uuid,
            'actionDefinePaths': self._act_def_paths,
            'messageDefinePaths': self._msg_def_paths,
            'tickInterval': self.tick_interval,
            'isRunning': True,
            'worker': self.context.blackboard.get_worker(),
            'blackboard': self.context.blackboard.get_blackborad_info()
        }

        return json_data

    def start(self, interval_msec = 1000):
        self.start_tick_timer(interval_msec)

    def stop(self, offline = False):
        self.stop_tick_timer()

    def start_tick_timer(self, interval_msec=1000):
        self.stop_tick_timer()
        self.tick_interval = interval_msec
        interval_sec = interval_msec / 1000;
        self._tick_timer = TickTimer(interval_sec, lambda: self.tick())
        self._tick_timer.start()

    def stop_tick_timer(self):
        if self._tick_timer:
            self._tick_timer.cancel()

    def set_after_tick_callback(self, callback):
        self._call_back_after_tick = callback


class TickTimer():
    def __init__(self, interval_sec, callback_func):
        self._interval_sec = interval_sec
        self._callback_func = callback_func
        self._thread = Timer(self._interval_sec, self._handle_func)

    def _handle_func(self):
        self._callback_func()
        self._thread = Timer(self._interval_sec, self._handle_func)
        self._thread.start()

    def start(self):
        self._thread.start()

    def cancel(self):
        self._thread.cancel()



