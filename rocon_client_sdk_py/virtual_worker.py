import pydash
import os
from .virtual_core.hooks.bootstrap import HookBootstrap
from .virtual_core.hooks.busy import HookBusy
from .worker import Worker

class VirtualWorker(Worker):

    def __init__(self, uuid, options, configs, event_loop):

        self._uuid = uuid
        self._event_loop = event_loop

        self._options = options
        self._configs = configs

        pydash.merge(self._options['configs'], self._configs)
        # virtualworker.py파일이 있는 절대 경로
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._act_def_paths = dir_path + '/virtual_core/actions'
        self._msg_def_paths = dir_path + '/virtual_core/message_handlers'
        self.load_hooks()

        self.mqtt_client = None

        super().__init__(self._uuid, self._act_def_paths, self._msg_def_paths, self._options, self._event_loop)

    def reset(self):
        self.stop()
        super().reset()


    def load_hooks(self):

        #hooks = {HookBootstrap(), HookBusy()}
        #self.tree_manager.hooks = hooks
        pass

    async def on_core_logic_task_hook_handler(self, context, task_name, to_do, *args):
        print('on_core_logic_task_hook_handler >> ' + task_name)

        if task_name is 'initWorker' and to_do is 'loadWorkerContext':
            hook = HookBootstrap(context)
            return await hook.load_worker_context(args[0], args[1])

        elif task_name is 'checkRevision' and to_do is 'checkRevision':
            hook = HookBusy(context)
            return await hook.checkRevision(args[0])

        return None

