import py_trees
from .constants import *
from rocon_client_sdk_py.logic.context import Context
import asyncio


class TaskBase(py_trees.behaviour.Behaviour):
    def __init__(self, name="NoNamed"):
        super(TaskBase, self).__init__(name)

    @property
    def context(self) -> Context:
        blackboard = py_trees.blackboard.Client(name=MASTER_BLACKBOARD_NAME)
        blackboard.register_key(key=KEY_CONTEXT, access=py_trees.common.Access.READ)
        value = blackboard.get(KEY_CONTEXT)
        return value

    @asyncio.coroutine
    def bug(self):
        raise Exception('not consumed')


class Task(TaskBase):
    def __init__(self, name="Task NoNamed"):
        super(Task, self).__init__(name)


class AsyncTask(TaskBase):
    def __init__(self, name="AsyncTask NoNamed"):
        super(AsyncTask, self).__init__(name)

        self.async_task_status = py_trees.common.Status.RUNNING
