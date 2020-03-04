from rx.subject import Subject
import threading
from rx.scheduler.eventloop import AsyncIOScheduler
from rx import operators as ops
from rx.scheduler import ImmediateScheduler
import rx
import asyncio

class Waiter():
    def __init__(self, event_loop, timeout_msec = -1):
        self._timeout_msec = timeout_msec
        self._event = Subject()
        self._wait_exit = False
        self.result_ob = None
        self._event_loop = event_loop
        self._timer = None

        self.scheduler = AsyncIOScheduler(loop=event_loop)
        self.done = asyncio.Future()

        print('done init')

    def set_timeout(self, timeout_msec):
        self._timeout_msec = timeout_msec

    def _timeout_callback(self):
        print('called _timeout_callback')
        self._event.on_next('timeout')

    async def wait(self):
        if self._timeout_msec > 0:
            self._timer = threading.Timer(self._timeout_msec/1000, self._timeout_callback)
            self._timer.start()

        self._wait_exit = False

        def cb_next(data):
            print('received data : {}'.format(data))

            if self._timer:
                self._timer.cancel()

            self._wait_exit = True
            self.done.set_result(data)


        def cb_completed():
            print('received completed')
            self.done.set_result('done')

        #self._event.subscribe(on_next=cb_next, on_completed=cb_completed, scheduler=self.scheduler)
        self._event.subscribe(on_next=cb_next, scheduler=self.scheduler)
        result = await self.done

        print('done wait')
        return result

    def end(self, msg):
        self._event.on_next(msg or 'success')
        self._event.on_completed()
        #self.result_ob.dispose()

    def set_next(self, msg):
        self._event.on_next(msg)