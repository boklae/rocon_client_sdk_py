import asyncio

class AutodoorConsumer():
    def __init__(self):
        pass

    async def request_open_autodoor(self, autodoor_id, context):
        RETRY = 10
        INTERVAL = 1000
        request = context.api_configuration.request

        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/autodoors/{}/commands'.format(iot_op_url, autodoor_id)
        for i in range(RETRY):
            try:
                #req_json_body = json.dump({'action': 'open'})
                async with request.post(url, json={'action': 'open'}) as r:
                    if r.status == 200:
                        print('Open Autodoor: {} requested'.format(autodoor_id))
                        return True

            except Exception as exc:
                print(exc)
                print('there is problem while request open autodoor')

            await asyncio.sleep(INTERVAL/1000)

        return False

    async def request_close_autodoor(self, autodoor_id, context):
        RETRY = 10
        INTERVAL = 1000
        request = context.api_configuration.request

        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/autodoors/{}/commands'.format(iot_op_url, autodoor_id)
        for i in range(RETRY):
            try:
                #req_json_body = json.dump({'action': 'open'})
                async with request.post(url, json={'action': 'close'}) as r:
                    if r.status == 200:
                        print('Close Autodoor: {} requested'.format(autodoor_id))
                        return True

            except Exception as exc:
                print(exc)
                print('there is problem while request close autodoor')

            await asyncio.sleep(INTERVAL/1000)

        return False

    async def ensure_autodoor_opened(self, autodoor_id, context):
        RETRY = 20
        INTERVAL = 1000
        request = context.api_configuration.request

        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/autodoors/{}'.format(iot_op_url, autodoor_id)
        #url = context.api_configuration.get_url('temp.iot_operator/facilities/autodoors/{}'.format(autodoor_id))
        for i in range(RETRY):
            try:
                async with request.get(url) as r:
                    if r.status == 200:
                        json_data = await r.json()
                        if json_data['status'] == 'OPENED':
                            return True

                        print('Status of Autodoor: {} is {} it\'s not match with opended'.format(autodoor_id, json_data))

            except Exception as exc:
                print(exc)
                print('there is problem while checking autodoor is open or not')

            print('Check Autodoor : {} open 1000ms later'.format(autodoor_id))
            await asyncio.sleep(INTERVAL / 1000)

        print('failed to waiting autodoor, exceed timeout')
        return False

    async def ensure_autodoor_closed(self, autodoor_id, context):
        RETRY = 20
        INTERVAL = 1000
        request = context.api_configuration.request
        #url = context.api_configuration.get_url(
        #    'temp.iot_operator/facilities/autodoors/{}'.format(autodoor_id))
        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/autodoors/{}'.format(iot_op_url, autodoor_id)


        for i in range(RETRY):
            try:
                async with request.get(url) as r:
                    if r.status == 200:
                        json_data = await r.json()
                        if json_data['status'] == 'CLOSED':
                            return True

                        print('Status of Autodoor: {} is {} it\'s not match with opended'.format(autodoor_id, json_data))

            except Exception as exc:
                print(exc)
                print('there is problem while checking autodoor is open or not')

            print('Check Audtodoor: {} open 1000ms later'.format(autodoor_id))
            await asyncio.sleep(INTERVAL / 1000)

        print('failed to waiting autodoor, exceed timeout')
        return False
