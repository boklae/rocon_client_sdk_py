import py_trees
import asyncio
import threading
from .task import Task, AsyncTask
from overrides import overrides


class TaskIsBooted(Task):

    @overrides
    def __init__(self, name="isBooted"):
        super(TaskIsBooted, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")

    @overrides
    def update(self):

        is_booted = self.context.is_booted

        if is_booted == True:
            self.logger.debug("update >> SUCCESS")
            return py_trees.common.Status.SUCCESS
        else:
            self.logger.debug("update >> FAILURE")
            return py_trees.common.Status.FAILURE

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskInitWorker(AsyncTask):

    @overrides
    def __init__(self, name="initWorker"):
        super(TaskInitWorker, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        super().initialise()
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.RUNNING

        event_loop = self.context.event_loop
        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
        except Exception as err:
            print(err)
            err.with_traceback()


        print('done TaskInitWorker initalise')

    async def _do_work(self):

        worker = self.context.blackboard.get_worker()
        if worker:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return

        uuid = self.context.worker.uuid
        api_worker = self.context.api_worker

        worker_record = await api_worker.find_one_by_uuid(uuid)


        if worker_record is None or len(worker_record) is 0:
            self.logger.debug('failed to find worker by uuid' + uuid)
            self.logger.debug('worker registered very first time. generate worker');
        else:
            self.logger.debug('registered worker')

        #TODO running multiple hooks

        worker_context = await self.context.worker.on_core_logic_task_hook_handler(self.context, self.name, 'loadWorkerContext', uuid, worker_record)
        result = worker_context or worker_record
        result = await api_worker.upsert(result)

        self.context.blackboard.set('worker', result)

        print('done do_work')
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


class TaskInitTask(AsyncTask):

    @overrides
    def __init__(self, name="initTask"):
        super(TaskInitTask, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")
        task = self.context.task

        if task is not None:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return


        event_loop = self.context.event_loop
        try:
            future = asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
            result = future.result()
        except Exception as err:
            print(err)
            err.with_traceback()


    async def _do_work(self):

        api_task = self.context.api_task

        if self.context.blackboard.get('task'):
            self.async_task_status = py_trees.common.Status.SUCCESS
            return

        task_configs = self.context.blackboard.get('configs')

        options = {
                'name': None if task_configs == None else task_configs['taskName'],
                'description': None if task_configs == None else task_configs['taskDescription']
            }

        task_body = await self.context.action_manager.build_task(options=options)


        worker = self.context.blackboard.get_worker()
        if worker and 'id' in worker:
            #TODO if(data.worker && data.worker.id) 조건 필요 확인
            id = worker['id']

            task = await api_task.init_task(id, task_body)
            self.context.blackboard.set('task', task)
            t = self.context.blackboard.get('task')

            if task is None or len(task) is 0:
                self.logger.debug('not registered worker')
            else:
                self.logger.debug('registered worker')

        else:
            print('initialize worker first. before register task')

        self.async_task_status = py_trees.common.Status.SUCCESS

    @overrides
    def update(self):
        return self.async_task_status


    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskBootCheck(AsyncTask):

    @overrides
    def __init__(self, name="bootCheck"):
        super(TaskBootCheck, self).__init__(name)

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

        #TODO check hook

        worker = self.context.blackboard.get('worker')
        task = self.context.blackboard.get('task')
        if worker and task:

            try:
                result = await self.context.blackboard.sync_worker()
                print('boot check finished, set worker status to idle')
                self.async_task_status = py_trees.common.Status.SUCCESS

                return

            except Exception as err:
                print(err)
                err.with_traceback()
        else:
            print('worker or task is not initialized')

        self.async_task_status = py_trees.common.Status.FAILURE

    @overrides
    def update(self):

        if self.async_task_status == py_trees.common.Status.SUCCESS:
            self.context.is_booted = True
            self.context.blackboard.set('status', 'idle')
            self.context.blackboard.set_worker({'status': 'idle'})

        return self.async_task_status

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskTestContextSwiching(AsyncTask):

    @overrides
    def __init__(self, name="testContextSwiching"):
        super(TaskTestContextSwiching, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    def mytimer(self):
        self.async_task_status = py_trees.common.Status.SUCCESS

    @overrides
    def initialise(self):
        self.logger.debug("initialise")

        self.async_task_status = py_trees.common.Status.RUNNING

        self.mytimer = threading.Timer(3, self.mytimer)
        self.mytimer.start()

    @overrides
    def update(self):

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update.. SUCCESS")
        else:
            self.logger.debug("update.. RUNNING")

        return self.async_task_status

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskTestAsyncWork(AsyncTask):

    @overrides
    def __init__(self, name="testAsyncWork"):
        super(TaskTestAsyncWork, self).__init__(name)
        self.async_task_status = py_trees.common.Status.RUNNING

    @overrides
    def setup(self):
        self.logger.debug("setup")

    async def display_date(self):

        print('enter display_date')
        await asyncio.sleep(5)
        print('done display_date')
        self.async_task_status = py_trees.common.Status.SUCCESS
        return 100

    @overrides
    def initialise(self):

        self.logger.debug("initialise")

        # event_loop = asyncio.get_event_loop()
        event_loop = self.context.event_loop

        asyncio.run_coroutine_threadsafe(self.display_date(), event_loop)
        print('done TaskTestAsyncWork initalise')

    @overrides
    def update(self):

        if self.async_task_status is py_trees.common.Status.SUCCES:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")

