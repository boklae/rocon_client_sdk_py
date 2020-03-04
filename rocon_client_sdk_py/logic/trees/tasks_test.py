import py_trees
from .task import Task, AsyncTask
import asyncio
from .deco import CustomDecoBase
from rocon_client_sdk_py.utils.waiter import Waiter

"""
    이 소스 파일은 py_trees로 커스텀 트리를 만드는 것을 테스트하는 파일이다.
    create_test_trees()를 통해 root 노드를 리턴 받는다.
    trees_manager.py의 _create_root()에서 
    root = py_trees.composites.Sequence(
            name="RootTree",
            children=[create_test_trees()]
        )
    으로 선언해서 test tasks를 확인하면 된다. 
    
    
    ==주요 테스트 비즈니스 로직==
    1. process_instruction이 비동기로 러닝되면 Success/Fail 되기전까지 Running 상태이다.
       상태값은 Blackbord에 'NowProcessInstructionStatus'으로 기록한다.
    2. check_process_inst는 process_instruction이 Running상태이면 fail로 변환한다.
       Running상태에서 check_revision_then_keep_processing에 의해 check_revision를 계속 확인하기 위함.
    3. check_revision_then_keep_processing 는 sequence로 check_revision과 process_instruction을 success일때까지 확인한다.
    4. rewind_when_running은 DecoRewindWhenRunning로 만든 커스텀 데코이다.
        Blackbord에 기록된  'NowProcessInstructionStatus' 상태값이 Running을 완료할때까지 무한 반복하는 데코이다.
    5. NowProcessInstructionStatus가 success일때 finish_report가 수행된다.
        'NowProcessInstructionStatus' 상태값을 초기화 한다.
    
"""

g_count = 0


def create_test_trees():

    check_revision = TaskCheckRevision()
    process_instruction = TaskProcessInstruction()

    check_process_inst = py_trees.decorators.RunningIsFailure(
        name="checkProcessInstruction",
        child=process_instruction
    )

    check_revision_then_keep_processing = py_trees.composites.Sequence(
        name="checkRevisionThenKeepProcessing",
        children=[check_revision, check_process_inst]
    )

    rewind_when_running = DecoRewindWhenRunning(
        child=check_revision_then_keep_processing,
        name="RewindWhenRunning"
    )

    is_busy = TaskIsBusyStatus()
    finish_report = TaskFinishReport()

    busy_status = py_trees.composites.Sequence(
        name="busyStatus",
        children=[is_busy, rewind_when_running, finish_report]
    )

    repeater = py_trees.decorators.FailureIsRunning(
        child=busy_status,
        name="Repeater"
    )

    return repeater


class TaskIsBusyStatus(Task):
    def __init__(self, name="isBusyStatus"):
        super(TaskIsBusyStatus, self).__init__(name)

    def initialise(self):
        self.logger.debug("initialise")

        self.async_task_status = py_trees.common.Status.SUCCESS

    def update(self):
        self.logger.debug("TaskIsBusyStatus update")

        return self.async_task_status


class TaskCheckRevision(AsyncTask):
    def __init__(self, name="checkRevision"):
        super(TaskCheckRevision, self).__init__(name)

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

        try:
           print('_do_work')
        except Exception as err:
            print(err)
            err.with_traceback()

        self.async_task_status = py_trees.common.Status.SUCCESS

    def update(self):
        self.logger.debug("TaskCheckRevision update")

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
        self.async_task_status = None

        self.g_count = 0


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
        print('waiting.... for 10sec')

        #await asyncio.sleep(100)

        timeout = 1000*60*60
        self.waiter = Waiter(timeout)

        result = await self.waiter.wait()


        #while(True):
        #    pass

        print('done...TaskProcessInstruction')

        self.context.blackboard.set('NowProcessInstructionStatus', py_trees.common.Status.SUCCESS)

        self.async_task_status = py_trees.common.Status.SUCCESS

    def update(self):
        self.logger.debug("TaskProcessInstruction update")

        self.g_count += 1
        if self.g_count > 5:
            self.g_count = 0
            self.waiter.set_next('success')


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

    def initialise(self):
        self.logger.debug("initialise")
        self.async_task_status = py_trees.common.Status.SUCCESS

        self.context.blackboard.set('NowProcessInstructionStatus', None)


    def update(self):
        self.logger.debug("TaskFinishReport update")

        if self.async_task_status is py_trees.common.Status.SUCCESS:
            self.logger.debug("TaskFinishReport update >> SUCCESS")
        else:
            self.logger.debug("TaskFinishReport update >> RUNNING")

        return self.async_task_status



class DecoRewindWhenRunning(CustomDecoBase):

    def update(self):

        status = self.context.blackboard.get('NowProcessInstructionStatus')
        if status is None:
            status = py_trees.common.Status.RUNNING
        elif status is py_trees.common.Status.SUCCESS:
            pass
            print('success')

        return status