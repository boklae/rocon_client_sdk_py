from aiohttp import web
import asyncio
import pydash

class WebServer():
    def __init__(self, worker_agent, port):
        self._owner_worker_agent = worker_agent

        self._server = None
        self._runner = None

        self._port = port
        self._host_url = 'localhost'
        self._handler = Handler(self._owner_worker_agent)

        self._routers = [

            web.get('/{uuid}/hello', self._handler.handle_test_hello),

            web.post('/{uuid}/controls/tick', self._handler.handle_start_worker),
            web.delete('/{uuid}/controls/tick', self._handler.handle_stop_worker),
            web.delete('/{uuid}/blackboard', self._handler.handle_reset_worker),
            web.put('/{uuid}/controls/tick', self._handler.handle_set_interval),
            web.get('/{uuid}', self._handler.handle_get_virtual_worker),
            web.get('/{uuid}/options', self._handler.handle_get_options),
            web.get('/{uuid}/blackboard', self._handler.handle_get_blackboard),
            web.get('/{uuid}/location', self._handler.handle_get_location),
            web.get('/{uuid}/controls/messages', self._handler.handle_get_messages),
            web.post('/{uuid}/controls/messages', self._handler.handle_add_messages),
        ]

    async def start(self):
        app = web.Application()
        app.add_routes(self._routers)

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, 'localhost', self._port)

        print("======= Serving on http://{}:{}/ ======".format(self._host_url, self._port))
        await site.start()


class Handler():
    def __init__(self, worker_agent):
        self._owner_worker_agent = worker_agent

    async def handle_intro(self, request):
        return web.Response(text='Hi there!')

    async def handle_test_hello(self, request):
        txt = 'Hello, world'
        return web.Response(text=txt)

    def _check_valid_request(self, request):
        id = request.match_info['uuid']
        if self._owner_worker_agent.uuid != id:
            print('Not matched uuid')
            return False

        return True

    async def handle_get_options(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        response_data = self._owner_worker_agent.worker.options
        return web.json_response(response_data)

    async def handle_get_blackboard(self, request):
        txt = 'handle_get_blackboard'
        return web.Response(text=txt)

    async def handle_reset_worker(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')


        #TODO reset blackborad
        self._owner_worker_agent.reset()

        return web.Response(text='success')

    #TODO JS 구현과 확인 필요 (all)
    async def handle_get_location(self, request):
        txt = 'handle_get_location'
        return web.Response(text=txt)

    async def handle_get_messages(self, request):
        txt = 'handle_get_messages'
        return web.Response(text=txt)

    async def handle_add_messages(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        data = await request.json()
        name = data['name']
        body = data['body']
        overwrite = data['overwrite']

        messages = self._owner_worker_agent.context.blackboard.get('recv_messages') or []
        if overwrite:
            exist_msg_idx = pydash.find_last_index(messages, {'name': name, 'receiver': self._owner_worker_agent.uuid})
            if exist_msg_idx != -1:
                messages[exist_msg_idx]['body'] = body
                return web.json_response({'messages_length': len(messages)})

        new_messages = {'name': name, 'body': body, 'receiver': self._owner_worker_agent.uuid}
        messages.append(new_messages)
        self._owner_worker_agent.context.blackboard.set('recv_messages', messages)
        return web.json_response({'messages_length': len(messages)})


    async def handle_start_worker(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        data = await request.json()
        interval = data['interval']

        self._owner_worker_agent.start(interval)
        return web.Response(text='success')

    async def handle_stop_worker(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        data = await request.json()
        offline = data['offline']
        #TODO set offline

        self._owner_worker_agent.stop()
        return web.Response(text='success')

    async def handle_set_interval(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        data = await request.json()
        interval = data['interval']

        self._owner_worker_agent.start_tick_timer(interval)
        return web.Response(text='success')

    #TODO 정리
    async def handle_get_virtual_worker(self, request):
        if self._check_valid_request(request) is False:
            return web.Response(text='Not matched uuid')

        response_data = self._owner_worker_agent.worker.to_json()
        return web.json_response(response_data)


