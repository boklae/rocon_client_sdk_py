import py_trees
from overrides import overrides
from .task import AsyncTask
from rocon_client_sdk_py.utils.util import *
import asyncio

class TaskUpdateWorker(AsyncTask):
    def __init__(self, name="updateWorker"):
        super(TaskUpdateWorker, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)

        except Exception as err:
            print(err)
            err.with_traceback()

    async def _do_work(self):
        interval = self.context.blackboard.get('updateInterval')
        curnt_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())

        last_time_ms = 0
        #last_updated_at = self.context.blackboard.get_worker(sub_key='updated_at')
        worker = self.context.blackboard.get_worker()
        last_updated_at = worker['updated_at']

        if last_updated_at:
            last_time_ms = get_time_milliseconds(last_updated_at)
            # print(last_time_ms)

        gap = curnt_time_ms - last_time_ms
        print('time gap : {}'.format(gap))
        if gap < interval:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return

        if self.context.blackboard.get_worker_update() is None:
            self.context.blackboard.set_worker({'updated_at': current_datetime_utc_iso_format()})

        try:
            result = await self.context.blackboard.sync_worker()

        except Exception as err:
            print(err)
            err.with_traceback()


        self.async_task_status = py_trees.common.Status.SUCCESS

    @overrides
    def update(self):
        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status


    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskUpdateTask(AsyncTask):
    def __init__(self, name="updateTask"):
        super(TaskUpdateTask, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)

        except Exception as err:
            print(err)
            err.with_traceback()

    async def _do_work(self):
        curnt_time_ms = get_time_milliseconds(current_datetime_utc_iso_format())

        task_body = self.context.blackboard.get('task')
        last_ms = self.context.blackboard.get('task_updated') or 0
        if curnt_time_ms - last_ms < 15000:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return

        worker = self.context.blackboard.get('worker')
        id = worker['id']

        try:
            result = await self.context.api_task.init_task(id, task_body)
            self.context.blackboard.set('task', result)
        except Exception as err:
            print(err)
            err.with_traceback()

        self.context.blackboard.set('task_updated', curnt_time_ms)
        self.async_task_status = py_trees.common.Status.SUCCESS

    @overrides
    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")

