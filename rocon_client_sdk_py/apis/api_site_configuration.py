
class ApiSiteConfiguration():
    def __init__(self, httpclient):
        self._httpclient = httpclient

    async def get_zones(self, zone_type, map_id):
        query = {'map':map_id, 'type':zone_type}
        request = self._httpclient.request()
        url = self._httpclient.site_config_url('/api/zones')

        try:
            async with request.get(url, params=query) as r:
                json_data = await r.json()
                return json_data

        except Exception as exc:
            print(exc)
            return None
