from rocon_client_sdk_py.virtual_core.actions.base import Action
import pydash
from rocon_client_sdk_py.utils.waiter import Waiter
from rocon_client_sdk_py.virtual_core.components.button_requests import ButtonRequests
from rx.subject import Subject


class Wait(Action):
    def __init__(self):
        self.name = 'Wait'
        self.func_name = 'wait'

    async def on_define(self, context):
        print('define action of ' + self.name)

        domain_door_behavior = [{'alias': 'True', 'value': True}, {'alias': 'False', 'value': False}];

        return {
            'name': self.name,
            'func_name': self.func_name,
            'args':[
                {
                    'key': 'type',
                    'type': 'string',
                    'default': 'human_input',
                    'domain': [
                        {'alias': 'Duration', 'value': 'duration'},
                        {'alias': 'Controlled by system', 'value': 'signal'},
                        {'alias': 'Until button press', 'value': 'human_input'}
                    ],
                    'options':{
                        'user_input': False,
                        'regex': None
                    }
                },
                {
                    'key': 'timeout',
                    'type': 'number',
                    'default': '30000',
                    'domain': [
                        {'alias': 'forever', 'value': '-1'},
                        {'alias': '10000 ms', 'value': '10000'},
                        {'alias': '20000 ms', 'value': '20000'},
                        {'alias': '30000 ms', 'value': '30000'},
                        {'alias': '40000 ms', 'value': '40000'},
                        {'alias': '50000 ms', 'value': '50000'},
                        {'alias': '60000 ms', 'value': '60000'}
                    ],
                    'options':{
                        'user_input': True,
                        'regex': None
                    }
                },
                {
                    'key': 'param',
                    'type': 'string',
                    'default': 'revision',
                    'domain': ['revision', 'success', 'fail']
                },
                {
                    'key': 'door_behavior',
                    'type': 'boolean',
                    'default': domain_door_behavior[1],
                    'domain': domain_door_behavior
                }
            ]
        }


    def cb_next(self, data):
        print('finish wait with signal')
        if data == 'test':
            return

        self.result = True
        self._wait_exit = True
        self.waiter.end('success')
        self.waiter_inf.end('success')
        #self.done.set_result('success')
        return True

    def cb_completed(self):
        print('received completed')

    async def type_signal(self, context, args):
        timeout = pydash.find(args, {'key':'timeout'})['value']
        brs = ButtonRequests(context)
        self.waiter = Waiter(context.event_loop, timeout)
        self.waiter_inf = Waiter(-1)
        self.result = False
        SIGNAL = 'signal'
        self._wait_exit = False

        subj = Subject()
        button_req = {
            'button_id': SIGNAL,
            'uuid': context.worker.uuid,
            'button': 'O',
            'notify': subj
        }

        #scheduler = AsyncIOScheduler(loop=context.event_loop)
        #self.done = asyncio.Future()


        #subj.subscribe(on_next=self.cb_next, scheduler=scheduler)
        #result = await self.done

        subj.subscribe(on_next=self.cb_next, on_completed=self.cb_completed)

        #subj.on_next('test')


        brs.set_button_request(button_req)

        if timeout > 0:
            timeout_result = await self.waiter.wait()
            if timeout_result == 'timeout':
                print('finish wait, exceed timeout')
                brs.remove_button_request(SIGNAL, context.worker.uuid)
                raise Exception('timeout exceed')
            elif timeout_result is not None:
                print('timeout waiter has been terminated with message: '.format(timeout_result))
                brs.remove_button_request(SIGNAL, context.worker.uuid)
            else:
                #None case
                pass

        else:
            inf_wait_result = await self.waiter_inf.wait()
            if inf_wait_result != 'success':
                print('timeout waiter has been terminated with message: {}'.format(inf_wait_result))

        #TODO 이 루틴 외의 솔루션 검토 필요
        #while (self._wait_exit == False):
        #    pass

        print('done type_signal of action_wait')
        return self.result

    async def type_human_input(self, context, args):
        pass


    async def on_perform(self, context, args):
        type = pydash.find(args, {'key': 'type'})['value']
        timeout = pydash.find(args, {'key': 'timeout'})['value']

        if type == 'duration':
            print('start to waiting... for {}sec'.format(timeout/1000))
            waiter = Waiter(context.event_loop, timeout)
            await waiter.wait()
            return True
        elif type == 'signal':
            return await self.type_signal(context, args)
        elif type == 'human_input':
            return await self.type_human_input(context, args)
        else:
            print('unknown wait type')
            return False
