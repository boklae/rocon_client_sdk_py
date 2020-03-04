import pydash
from PIL import Image, ImageFilter
import io
import json

class ApiConfiguration():
    def __init__(self, httpclient):
        self._httpclient = httpclient

    @property
    def request(self):
        return self._httpclient.request()

    def get_url(self, sub_url):
        url = self._httpclient.config_url(sub_url)
        return url

    async def get_stations(self, station_id=''):
        request = self._httpclient.request()

        sub_id = '/' + station_id if station_id != '' else ''
        url = self._httpclient.config_url('/api/stations' + sub_id)

        try:
            async with request.get(url) as r:
                json_data = await r.json()
                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_locations(self, destination_id=''):
        request = self._httpclient.request()

        if len(destination_id) > 0:
            url = self._httpclient.config_url('/api/locations/' + destination_id)
        else:
            url = self._httpclient.config_url('/api/locations')

        try:
            async with request.get(url) as r:
                #print(r.status)
                json_data = await r.json()
                #print('get_stations : \n' + str(json_data))

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_resource(self, resource_id):
        request = self._httpclient.request()

        url = self._httpclient.config_url('/api/resources/' + resource_id)

        try:
            async with request.get(url) as r:
                json_data = await r.json()
                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_resources(self):
        request = self._httpclient.request()

        url = self._httpclient.config_url('/api/resources')

        try:
            async with request.get(url) as r:
                #print(r.status)
                json_data = await r.json()

                #print('get_stations : \n' + str(json_data))
                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_maps(self, map=''):
        request = self._httpclient.request()
        map_sub = '/' + map if len(map) > 0 else ''
        url = self._httpclient.config_url('/api/maps' + map_sub)

        try:
            async with request.get(url) as r:
                json_data = await r.json()
                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_map_image(self, path) -> Image:
        request = self._httpclient.request()
        url = self._httpclient.config_url(path)
        print(url)

        try:
            async with request.get(url) as r:
                data = await r.read()
                f = io.BytesIO(data)
                image = Image.open(f)

            if image is None:
                print('image is none')

            return image

        except Exception as exc:
            print(exc)
            exc.with_traceback()
            return None


    async def get_zones(self, zone_type, map_id):
        query = {'map':map_id, 'type':zone_type}
        request = self._httpclient.request()
        url = self._httpclient.config_url('/api/zones')
        print('@get_zones')
        print(url)
        print(query)
        try:
            async with request.get(url, params=query) as r:
                json_data = await r.json()
                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def return_resource(self, worker_id, resource_id, slot_id = None):
        resource = await self.get_resource(resource_id)

        if slot_id:
            target_slots = pydash.find(resource['resource_slots'], {'id': slot_id})
        else:
            target_slots = pydash.find(resource['resource_slots'], {'user_id': worker_id, 'status': 'occupied'})

        if target_slots:
            request = self._httpclient.request()
            url = self._httpclient.config_url('/api/resources/{}/slots/{}'.format(resource_id, target_slots['id']))
            req_json_body = json.dumps({'status': 'gone'})

            try:
                async with request.put(url, data=req_json_body) as r:
                    # TODO error
                    json_data = await r.json()
                    print(r)

                    return json_data

            except Exception as exc:
                print(exc)
                return None

        else:
            #raise Exception('can return only occupied resource')
            print('can return only occupied resource')


    async def get_teleporter_gate(self, teleporter_id, map_id):
        request = self._httpclient.request()
        url = self._httpclient.config_url('/api/teleporter-gates')
        query = {
            'teleporter': teleporter_id,
            'map': map_id,
            'populate':'resource_slots'
        }

        try:
            async with request.get(url, params=query) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data[0]

        except Exception as exc:
            print(exc)
            return None