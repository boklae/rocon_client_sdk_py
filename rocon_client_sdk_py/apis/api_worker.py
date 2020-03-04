import aiohttp
import pydash
import json

class ApiWorker():
    def __init__(self, httpclient):
        self._httpclient = httpclient

    async def find_one_by_uuid(self, uuid):
        request = self._httpclient.request()

        url = self._httpclient.scheduler_url('/workers?uuid=' + uuid)
        async with request.get(url) as r:
            #TODO error
            json_data = await r.json()
            print(r)
            #await request.close()
            if len(json_data) > 0:
                print(json_data[0])
                return json_data[0]

            print('Not registed : ' + uuid)
            return {}

    async def upsert(self, body):
        request = self._httpclient.request()
        req_body = pydash.pick(body, ['status', 'name', 'type_specific', 'release_version', 'type', 'uuid'])


        req_json_body = json.dumps(req_body)
        #req_json_body = req_body

        url = self._httpclient.scheduler_url('/workers/')
        try:

            headers = {'Content-type': 'application/json'}
            async with request.put(url, data=req_json_body) as r:
                #TODO error
                json_data = await r.json()
                #await request.close()

                print(r)
                print(json_data)
                print('upset done')
                return json_data

        except Exception as exc:

            print(exc)
            pass


    async def update_worker(self, worker_id, update):
        allowed_update = ['type_specific', 'status', 'name']
        update_body = pydash.pick(update, allowed_update)
        request = self._httpclient.request()

        req_json_body = json.dumps(update_body)

        url = self._httpclient.scheduler_url('/workers/' + worker_id)
        try:
            headers = {'Content-type': 'application/json'}
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                # await request.close()
                return json_data

        except Exception as exc:
            print(exc)