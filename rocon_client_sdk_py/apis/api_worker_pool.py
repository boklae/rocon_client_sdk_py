import pydash
import json

class ApiWorkerPool():
    def __init__(self, httpclient):
        self._httpclient = httpclient

    async def register_worker(self, worker_id, reg_data):
        request = self._httpclient.request()

        url = self._httpclient.worker_pool_url('/api/workers/{}/register/'.format(worker_id))

        try:
            async with request.post(url, json=reg_data) as r:

                response = await r.read()
                print(response)
                #json_data = await r.json()
                #print(json_data)
        except Exception as exc:
            print(exc)
