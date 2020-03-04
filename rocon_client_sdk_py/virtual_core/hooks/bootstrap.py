import pydash

class HookBootstrap():
    def __init__(self, context):
        self._iniitializers = {'battery':self._init_battery, 'location': self._init_location}
        self._validators = {'battery': self._validate_battery, 'location': self._validate_location}
        self._api_config = context.api_configuration

    async def load_worker_context(self, uuid, worker_record):

        await self.download_maps()

        if(not worker_record):
            worker_record = {}
            print('Cannot found worker ({}) context file. Generate default worker context'.format(uuid))
            worker_record['uuid'] = uuid
            worker_record['name'] = 'VirtualWorker({})'.format(uuid)
            worker_record['type_specific'] = {}

            for item in self._iniitializers:
                worker_record = await self._iniitializers[item](worker_record)

            return worker_record
        else:
            return await self._patch(worker_record)


        return None

    async def _init_battery(self, worker_record):
        type_specific = worker_record['type_specific']
        pydash.set_(type_specific, 'battery',
                    {
                        'battery_level': 75,
                        'charging_status': 0
                    })

        return worker_record

    async def _init_location(self, worker_record):
        stations = await self._api_config.get_stations()
        for s in stations:
            map = await self._api_config.get_maps(s['map'])
            if map:
                type_specific = worker_record['type_specific']

                if 'location' not in type_specific:
                    type_specific['location'] = {}

                pydash.set_(type_specific['location'], 'map', s['map'])
                pydash.set_(type_specific['location'], 'pose2d', s['pose'])
                return worker_record

        assert(False)

    async def _validate_battery(self, worker_record):
        if pydash.get(worker_record['type_specific'], 'battery') is None:
            return {'result': False, 'message': 'battery information is not exist'}

        return {'result': True}

    async def _patch(self, worker_record):
        for item in self._validators:
            check = await self._validators[item](worker_record)
            if check['result'] is False:
                worker_record = await self._iniitializers[item](worker_record)
                print('validation failed while path() {}:{}'.format(check['message'], {'updated_worker': worker_record}))

        return worker_record

    async def _validate_location(self, worker_record):
        pose = pydash.get(worker_record['type_specific']['location'], 'pose2d')
        map = pydash.get(worker_record['type_specific']['location'], 'map')

        if pose is None:
            return {'result': False, 'message': 'pose information is not loaded correctly'}

        if map is None:
            return {'result': False, 'message': 'map information is not loaded correctly'}

        return {'result': True}

    async def download_maps(self):
        try:
            map_list = await self._api_config.get_maps()
            def cb(m):
                return pydash.get(m, 'site')
            map_list = pydash.filter_(map_list, cb)
            if len(map_list) is 0:
                print('there are no maps on site configuration')
                return False


        except Exception as err:
            print('failed to download maps')
            return False

        return True