import py_trees
from .task import Task, AsyncTask
import asyncio
import pydash
from rocon_client_sdk_py.utils.util import *

class TaskIsBusyStatus(Task):
    def __init__(self, name="isBusyStatus"):
        super(TaskIsBusyStatus, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")



    def update(self):
        self.logger.debug("update")

        if self.context.blackboard.get('status') == 'busy':
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.FAILURE

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskValidateReport(AsyncTask):
    def __init__(self, name="validateReport"):
        super(TaskValidateReport, self).__init__(name)

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

        try:
            updated_report = await self.context.api_report.get_report_by_id(report['id'])

            if updated_report and updated_report['status'] == 'finished':
                print('report finished from outside')

                self.context.blackboard.clear_report()
                self.context.blackboard.set('status', 'idle')
                self.async_task_status = py_trees.common.Status.FAILURE
                return

            if pydash.has(updated_report, 'instructions') is False or len(updated_report['instructions']) == 0:
                print('This report is not contains any instruction, mark this abort')

                await self.context.api_report.abort_report(report['id'], 'It has not any instruction')

                self.context.blackboard.clear_report()
                self.context.blackboard.set('status', 'idle')
                self.async_task_status = py_trees.common.Status.FAILURE
                return

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


class TaskCheckRevision(AsyncTask):
    def __init__(self, name="checkRevision"):
        super(TaskCheckRevision, self).__init__(name)

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise checkRevision")
        self.async_task_status = py_trees.common.Status.RUNNING
        event_loop = self.context.event_loop

        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)

        except Exception as err:
            print(err)
            err.with_traceback()


    async def _do_work(self):
        print('checkRevision >> _do_work')

        report = self.context.blackboard.get_report()
        print('report : {}'.format(report))

        try:
            print('before call get_report_by_id')
            updated_report = await self.context.api_report.get_report_by_id(report['id'])
            print('after call get_report_by_id')
            revision = pydash.get(updated_report, 'revision.status')
            print('result of revision : {}'.format(revision))

            if revision == 'pending':
                print('unhandled revision detected')

                #TODO js 소스의 callHook 루틴 추가 구현 필요
                result = await self.context.worker.on_core_logic_task_hook_handler(self.context, self.name, 'checkRevision',
                                                                          updated_report)

            print('done _do_work of TaskCheckRevision')
        except Exception as err:
            self.async_task_status = py_trees.common.Status.FAILURE
            print(err)
            err.with_traceback()
            return

        self.async_task_status = py_trees.common.Status.SUCCESS

    def update(self):
        self.logger.debug("update checkRevision")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskProcessInstruction(AsyncTask):
    def __init__(self, name="processInstruction"):
        super(TaskProcessInstruction, self).__init__(name)
        self._now_working = False

    def setup(self):
        self.logger.debug("setup")

    def initialise(self):
        self.logger.debug("initialise")

        now_working = self.context.blackboard.get('NowProcessInstructionStatus')

        if now_working is None:
            self.async_task_status = py_trees.common.Status.RUNNING
            self.context.blackboard.set('NowProcessInstructionStatus', py_trees.common.Status.RUNNING)

        elif now_working == py_trees.common.Status.RUNNING:
            return
        elif now_working == py_trees.common.Status.SUCCESS:
            self.async_task_status = py_trees.common.Status.SUCCESS
            return
        elif now_working == py_trees.common.Status.FAILURE:
            self.async_task_status = py_trees.common.Status.FAILURE
            return


        event_loop = self.context.event_loop

        try:
            asyncio.run_coroutine_threadsafe(self._do_work(), event_loop)
        except Exception as err:
            print(err)
            err.with_traceback()



        print('leave initialise')

    async def _do_work(self):

        instructions = pydash.get(self.context.blackboard.get_report(), 'instructions')
        self.context.blackboard.update_report_result({'status': 'running', 'status_msg': 'just started'})

        for inst in instructions:
            print('start to process instruction : {}'.format(inst))

            self.context.blackboard.update_report_result({'current': inst['id']})

            act = inst['action']
            act_func_name = act['func_name']
            args = act['args']

            if act_func_name is None:
                print('unknown action')
                self.context.blackboard.set('status', 'error')
                self.async_task_status = py_trees.common.Status.FAILURE
                self._now_working = False
                return

            inst_result = {
                'id': inst['id'],
                'status': 'running',
                'started_at': current_datetime_utc_iso_format(),
                'finished_at': None,
                'retries': 0
            }

            self.context.blackboard.update_instruction_result(inst_result)
            #TODO move syncReport somewhere else or make queue for it
            try:
                await self.context.blackboard.sync_report()
            except Exception as e:
                pass

            try:
                inst_result['returns'] = await self.context.action_manager.run_func(act_func_name, args)
                inst_result['status'] = 'DONE_SUCCESS'
                inst_result['finished_at'] = current_datetime_utc_iso_format()
                print('success to process instruction with result')
                self.context.blackboard.update_instruction_result(inst_result)

                try:
                    await self.context.blackboard.sync_report()
                except Exception as e:
                    pass

            except Exception as err:
                inst_result['returns'] = None
                inst_result['status'] = 'failed'
                inst_result['finished_at'] = current_datetime_utc_iso_format()

                self.context.blackboard.update_instruction_result(inst_result)
                await self.context.blackboard.sync_report()

                report = self.context.blackboard.get_report()
                msg = 'failed to process instruction: {}'.format(inst['id'])

                await self.context.api_report.cancel_report(report['id'], msg, True)

                self.context.blackboard.clear_report()
                self.context.blackboard.set('status', 'idle')
                print('error occurred while processing instruction')
                self.async_task_status = py_trees.common.Status.FAILURE
                self.context.blackboard.set('NowProcessInstructionStatus', py_trees.common.Status.FAILURE)
                self._now_working = False
                return

        result = {
            'current': None,
            'status': 'success',
            'status_msg': 'finished successfully'
        }
        self.context.blackboard.update_report_result(result)
        print('finally reportResult updated')

        self._now_working = False
        self.context.blackboard.set('NowProcessInstructionStatus', py_trees.common.Status.SUCCESS)
        self.async_task_status = py_trees.common.Status.SUCCESS


    def update(self):
        self.logger.debug("update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("update >> SUCCESS")
        else:
            self.logger.debug("update >> RUNNING")

        return self.async_task_status

    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskFinishReport(AsyncTask):
    def __init__(self, name="finishReport"):
        super(TaskFinishReport, self).__init__(name)

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
        result_status = pydash.get(report, 'result.status')
        if result_status == 'success':

            try:
                update = {'finished_at': current_datetime_utc_iso_format(), 'status': 'finished'}
                print(update)
                self.context.blackboard.set_report(update)

                await self.context.blackboard.sync_report()

                self.context.blackboard.clear_report()
                self.context.blackboard.set('status', 'idle')

                self.context.blackboard.set('NowProcessInstructionStatus', None)

                self.async_task_status = py_trees.common.Status.SUCCESS
                return

            except Exception as err:
                print(err)
                err.with_traceback()
        else:
            print('unknown satus of report result')

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
