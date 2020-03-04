import py_trees
from overrides import overrides
from .task import Task, AsyncTask
import asyncio
import pydash


class TaskHandleControlMessage(AsyncTask):
    def __init__(self, name="handleControlMessage"):
        super(TaskHandleControlMessage, self).__init__(name)

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

        message_manager = self.context.message_manager;
        messages = self.context.blackboard.get('recv_messages')
        if messages and len(messages) > 0:

            msg_idx = pydash.find_index(messages, {'receiver': self.context.worker.uuid})
            if msg_idx != -1:
                msg = pydash.clone(messages[msg_idx])
                print('start handle message :{}'.format(msg))
                pydash.pull_at(messages, msg_idx)

                self.context.blackboard.set('recv_messages', messages)
                message_inst = message_manager.find_message(msg['name'])
                if message_inst is None:
                    print('malformed message handler: {}, {}'.format(msg['key'], {'message': msg}))
                    self.async_task_status = py_trees.common.Status.FAILURE
                    return

                try:
                    await message_inst.on_handler(self.context, msg['body'])
                except Exception as err:
                    print('error occurred while processing message : {}'.format({
                        'message':msg
                    }))

        self.async_task_status = py_trees.common.Status.SUCCESS


    @overrides
    def update(self):
        self.logger.debug("update")

        return py_trees.common.Status.SUCCESS

    @overrides
    def terminate(self, new_status):
        self.logger.debug("terminate")

