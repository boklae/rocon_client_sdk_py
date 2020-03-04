import aiohttp
import pydash
import json

class ApiTask():
    def __init__(self, httpclient):
        self._httpClient = httpclient

    async def init_task(self, worker_id, task_body):
        task_body['worker'] = worker_id
        return await self.upsert(task_body)

    async def upsert(self, req_body):
        request = self._httpClient.request()
        url = self._httpClient.scheduler_url('/tasks/')

        """
        req_body = {
            "name": "7th_floor_delivery(v)",
            "description": "same with real_delivery but difference domains (like locations)",
            "actions": [
                {
                    "func_name": "undock",
                    "args": [],
                    "fixed": False
                },
                {
                    "func_name": "move",
                    "args": [
                        {
                            "key": "destination",
                            "type": "string",
                            "value": None,
                            "domain": [
                                "homebase",
                                "1@7@etri12b",
                                "1-2@7@etri12b",
                                "1-3@7@etri12b",
                                "1-4@7@etri12b",
                                "3@7@etri12b",
                                "4@7@etri12b",
                                "5@7@etri12b",
                                "6@7@etri12b",
                                "7@7@etri12b",
                                "8@7@etri12b",
                                "10@7@etri12b",
                                "10@7@etri12b",
                                "10@7@etri12b"
                            ],
                            "default": "homebase"
                        },
                        {
                            "key": "gesture",
                            "type": "string",
                            "value": None,
                            "domain": [
                                "confirming",
                                "rf_auth",
                                "move"
                            ]
                        }
                    ],
                    "fixed": False
                },
                {
                    "func_name": "dock",
                    "args": [
                        {
                            "key": "destination",
                            "type": "string",
                            "value": None,
                            "domain": [
                                "homebase",
                                "charging_station_1",
                                "in_hell_fire",
                                "nearest"
                            ],
                            "default": "homebase"
                        },
                        {
                            "key": "gesture",
                            "type": "string",
                            "value": None,
                            "domain": []
                        }
                    ],
                    "fixed": False
                }
            ],
            "fixed": False,
            "worker": "5948e00718a0b0c51b0f38ca"
        }
        """

        req_json_body = json.dumps(req_body)


        try:

            headers = {'Content-type': 'application/json'}
            async with request.put(url, data=req_json_body, headers = headers) as r:
                # TODO error
                json_data = await r.json()
                #await request.close()
                print('ApiTask >> response of upset!! \n' + str(json_data))
                return json_data

        except Exception as exc:
            print(exc)
            return None
