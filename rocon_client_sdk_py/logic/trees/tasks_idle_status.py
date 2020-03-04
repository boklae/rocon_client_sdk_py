import py_trees
from .task import Task, AsyncTask
import asyncio
import pydash


class TaskIsIdleStatus(Task):
    def __init__(self, name="isIdleStatus"):
        super(TaskIsIdleStatus, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")

    def update(self):
        self.logger.debug("update")

        if self.context.blackboard.get('status') is 'idle':
            print('now idle status')
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE

        return py_trees.common.Status.SUCCESS

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskHealthCheck(Task):
    def __init__(self, name="healthCheck"):
        super(TaskHealthCheck, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")

    def update(self):
        self.logger.debug("update")

        #TODO add more healthCheck logic here

        return py_trees.common.Status.SUCCESS

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskInitReportFromExistReport(AsyncTask):
    def __init__(self, name="initReportFromExistReport"):
        super(TaskInitReportFromExistReport, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")

        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            coro_func = asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
            result = coro_func.result()
            #asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)

            print(self.async_task_status)
            print('done initialise')
        except Exception as err:
            print(err)
            err.with_traceback()


    async def _do_work(self):
        worker = self.context.blackboard.get('worker')
        id = worker['id']

        options = {'worker': id, 'status_ne': 'finished'}

        try:
            last_report = await self.context.api_report.get_reports(options)

            if len(last_report) == 0:
                print('There is no processing report for this worker')

            else:
                if last_report[0]['status'] == 'pending':
                    # self.context.blackboard.set_report(last_report[0])
                    self.context.blackboard.set('report', last_report[0])
                    self.async_task_status = py_trees.common.Status.SUCCESS
                    return
                else:
                    # TODO In future the worker can continuously process report after unexpected rebooting if possible

                    id = pydash.get(last_report[0], 'id')
                    msg = 'cannot resume processing report on this version of virtual worker now. cancel it.'
                    #future = asyncio.run_coroutine_threadsafe(self.context.api_report.cancel_report(id, msg, True),
                    #                                          event_loop)
                    result = await self.context.api_report.cancel_report(id, msg, True)

                    print(result)

        except Exception as err:
            print(err)
            #TODO 장시간 idle 상태에서 이곳으로 빠지는 경우 확인 필요 (pc 대기상태, 네트웍 상태등 확인)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.FAILURE

    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskRequestRecommendation(AsyncTask):
    def __init__(self, name="requestRecommendation"):
        super(TaskRequestRecommendation, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            coro_func = asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
            result = coro_func.result()
        except Exception as err:
            print(err)
            err.with_traceback()

    async def _do_work(self):
        worker = self.context.blackboard.get('worker')
        id = worker['id']

        try:
            recommend = await self.context.api_report.req_recommend(id)

            if recommend and len(recommend) > 0:
                self.context.blackboard.set('report_recommendation', recommend)
                self.async_task_status = py_trees.common.Status.SUCCESS
                return

        except Exception as err:
            print(err)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.FAILURE

    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskGetOwnership(AsyncTask):
    def __init__(self, name="getOwnership"):
        super(TaskGetOwnership, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
            #coro_func = asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
            #result = coro_func.result()
        except Exception as err:
            print(err)
            err.with_traceback()

    async def _do_work(self):

        worker = self.context.blackboard.get_worker()
        worker_id = worker['id']

        recommend = self.context.blackboard.get('report_recommendation')
        if recommend is None:
            print('failed to take ownership of report: empty recommendation')
            self.async_task_status = py_trees.common.Status.FAILURE
            return

        # event_loop = asyncio.get_event_loop()
        event_loop = self.context.event_loop
        try:
            id = pydash.get(recommend, '0.id')
            target_report = await self.context.api_report.req_ownership(id, worker_id)

            self.context.blackboard.set('recommend', None)

            print(target_report['worker'])
            print(worker_id)

            if target_report['worker'] == worker_id:
                self.context.blackboard.set('report', target_report)
                self.async_task_status = py_trees.common.Status.SUCCESS
                return

        except Exception as err:
            print(err)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.FAILURE

    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskHandleFirstRevision(AsyncTask):
    def __init__(self, name="handleFirstRevision"):
        super(TaskHandleFirstRevision, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

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

        report = self.context.blackboard.get_report()
        if report is None:
            self.async_task_status = py_trees.common.Status.FAILURE
            return

        if pydash.get(report, 'revision') is None:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return

        try:
            accepted_revision = await self.context.api_report.approve_revision(report)

            if pydash.get(accepted_revision, 'revision.status') == 'approved':
                self.context.blackboard.set('report', accepted_revision)
                self.async_task_status = py_trees.common.Status.SUCCESS
                return

        except Exception as err:
            print(err)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.FAILURE

    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskStartReport(AsyncTask):
    def __init__(self, name="startReport"):
        super(TaskStartReport, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

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
        worker = self.context.blackboard.get_worker()
        worker_id = worker['id']

        report = self.context.blackboard.get_report()
        if report is None:
            py_trees.common.Status.FAILURE
            return

        try:
            update_body={'status': 'running', 'worker': worker_id}
            updated_report = await  self.context.api_report.update_report(report['id'], update_body)

            if updated_report['status'] == 'running':
                self.context.blackboard.set('status', 'busy')
                self.async_task_status = py_trees.common.Status.SUCCESS
                return

        except Exception as err:
            print(err)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.FAILURE

    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")
