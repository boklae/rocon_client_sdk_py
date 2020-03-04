import py_trees
from overrides import overrides
from .task import Task, AsyncTask

class TaskIsOfflineStatus(Task):
    def __init__(self, name="isOfflineStatus"):
        super(TaskIsOfflineStatus, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")

    @overrides
    def update(self):
        self.logger.debug("update")

        if self.context.blackboard.get('status') is 'offline':
            print('now offline status')
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE




    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")


class TaskIsErrorStatus(Task):
    def __init__(self, name="isErrorStatus"):
        super(TaskIsErrorStatus, self).__init__(name)

    @overrides
    def setup(self):
        self.logger.debug("setup")

    @overrides
    def initialise(self):
        self.logger.debug("initialise")

    @overrides
    def update(self):
        self.logger.debug("update")

        if self.context.blackboard.get('status') is 'error':
            print('now error status')
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")