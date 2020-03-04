import asyncio
import pydash


STATUS = {
    'initializing': 'INITIALIZING',
    'idle': 'IDLE',
    'error': 'ERROR',
    'toDeparture': 'TO_DEPARTURE',
    'onDeparture': 'ON_DEPARTURE',
    'toDestination': 'TO_DESTINATION',
    'onDestination': 'ON_DESTINATION'
}

class ElevatorConsumer():
    def __init__(self):
        pass

    def is_door_open(self, status):
        return status == STATUS['onDeparture'] or status == STATUS['onDestination']

    async def ensure_elevator(self, context, teleported_id, status):
        TIMEOUT = 5*60*1000
        CHECKING_INTERVAL = 1000

        request = context.api_configuration.request
        url = context.api_configuration.get_url(
            'temp.iot_operator/facilities/elevators/{}'.format(teleported_id))

        for i in range(TIMEOUT/CHECKING_INTERVAL):
            try:
                async with request.post(url, json={'action': 'open'}) as r:
                    if r.status == 200:
                        json_data = await r.json()
                        if json_data['status'] == status:
                            print('elevator status is {}'.format(status))
                            return True

            except Exception as exc:
                print(exc)
                print('there is problem while request open autodoor')

            await asyncio.sleep(CHECKING_INTERVAL/1000)

        print('failed to waiting for keep opening elevator door: timeout exceed')
        return False

    async def call_elevator(self, context, teleporter, departure_gate, destination_gate):
        request = context.api_configuration.request

        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/elevators/{}/services'.format(iot_op_url, teleporter['id'])

        req_body={
            'departure_floor': str(pydash.get(departure_gate, 'properties.floor_id')),
            'destination_floor': str(pydash.get(destination_gate, 'properties.floor_id'))
        }

        if 'departure_floor' not in req_body or 'destination_floor' not in req_body:
            raise Exception('req body for calling elevator is not enough, {}'.format(req_body))

        #req_json_body = json.dumps(req_body)
        try:
            async with request.post(url, json=req_body) as r:
                if r.status == 200:
                    json_data = await r.json()
                    return json_data['serviceId']
                else:
                    print('response not success while calling Elevator')
                    raise Exception('response not success while calling Elevator')

        except Exception as exc:
            print(exc)
            print('call_elevator() failed')

    async def ensure_elevator_door_open(self, context, teleporter_id):
        TIMEOUT = 5*60*1000
        CHECKING_INTERVAL = 1000

        request = context.api_configuration.request
        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/elevators/{}'.format(iot_op_url, teleporter_id)

        for i in range(int(TIMEOUT/CHECKING_INTERVAL)):
            try:
                async with request.get(url) as r:
                    if r.status == 200:
                        json_data = await r.json()
                        if self.is_door_open(json_data['status']):
                            print('elevator door keep opening detected')
                            return True

            except Exception as exc:
                print(exc)
                print('there is problem while request open autodoor')

            await asyncio.sleep(CHECKING_INTERVAL/1000)

        print('failed to waiting for keep opening elevator door: timeout exceed')
        return False

    async def close_elevator_door(self, context, teleported_id, service_id, message, result):
        RETRY = 10
        RETRY_INTERVAL = 1000

        request = context.api_configuration.request
        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/elevators/{}/services/{}/messages'.format(iot_op_url, teleported_id, service_id)

        desire_status = None
        if message == 'board':
            desire_status = STATUS['onDeparture']
        elif message == 'unboard':
            desire_status = STATUS['onDestination']

        if desire_status is None:
            raise Exception('unkown message to close_elevator_door: {}'.format(message))

        req_json_body = {
            'message': message,
            'status': desire_status,
            'result': result
        }

        for i in range(RETRY):
            try:
                async with request.post(url, json=req_json_body) as r:
                    if r.status == 200:
                        return True
                    else:
                        print('there is problem while request close_elevator_door : {}'.format(r.status))

            except Exception as exc:
                print(exc)
                print('there is problem while request close_elevator_door')

            await asyncio.sleep(RETRY_INTERVAL/1000)

        print('failed to request close elevator door: maximum retry exceed')
        return False

    async def ensure_elevator_door_closed(self, context, teleporter_id):
        RETRY = 10
        RETRY_INTERVAL = 1000

        request = context.api_configuration.request
        worker = context.worker
        iot_op_url = worker._configs['temp']['iot_operator']
        url = 'http://{}/facilities/elevators/{}'.format(iot_op_url, teleporter_id)

        json_data = None
        try:
            async with request.get(url) as r:
                if r.status == 200:
                    json_data = await r.json()

        except Exception as exc:
            print(exc)
            print('there is problem while request ensure_elevator_door_closed')
            return False

        for i in range(RETRY):
            if self.is_door_open(json_data['status']) == False:
                return True

            await asyncio.sleep(RETRY_INTERVAL/1000)

        print('failed to ensure elevator door closed: maximum retry exceed')
        return False