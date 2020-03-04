import aiohttp
import pydash
import json

class ApiReport():
    def __init__(self, httpclient):
        self._httpclient = httpclient

    async def req_recommend(self, worker_id):
        request = self._httpclient.request()
        url = self._httpclient.scheduler_url('/reports/recommend')
        try:
            async with request.post(url, json={'worker': worker_id}) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def req_ownership(self, report_id, worker_id):
        request = self._httpclient.request()

        req_json_body = json.dumps({'worker': worker_id})
        url = self._httpclient.scheduler_url('/reports/' + report_id + '/ownership')
        try:
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def update_report(self, report_id, update_body):
        request = self._httpclient.request()

        req_json_body = json.dumps(update_body)
        url = self._httpclient.scheduler_url('/reports/' + report_id)
        try:
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_reports(self, options):
        request = self._httpclient.request()

        url = self._httpclient.scheduler_url('/reports')
        try:
            async with request.get(url, params=options) as r:
                #TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def get_report_by_id(self, report_id):
        request = self._httpclient.request()

        url = self._httpclient.scheduler_url('/reports/' + report_id)
        try:
            async with request.get(url) as r:
                #TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:

            if r.status is 404:
                return None
            else:

                print('unhandled error on get_report_by_id')

            print(exc)
            return None

    async def cancel_report(self, report_id, message, force=False):
        request = self._httpclient.request()

        req_json_body = json.dumps({'message': message, 'force': force})

        url = self._httpclient.scheduler_url('/reports/' + report_id + '/cancel')
        try:
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def abort_report(self, report_id, message):
        request = self._httpclient.request()

        req_json_body = json.dumps({'message': message})

        url = self._httpclient.scheduler_url('/reports/' + report_id + '/abort')
        try:
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def handle_revision(self, report, propositions, action):
        request = self._httpclient.request()

        report_body = {'action': action, 'propositions': propositions}
        req_json_body = json.dumps(report_body)

        rep = report['id'] if 'id' in report else report

        url = self._httpclient.scheduler_url('/reports/' + rep + '/revision')
        try:
            async with request.put(url, data=req_json_body) as r:
                # TODO error
                json_data = await r.json()
                print(r)

                return json_data

        except Exception as exc:
            print(exc)
            return None

    async def approve_revision(self, report):
        return await self.handle_revision(report['id'], report['revision']['propositions'], 'approve')

    async def reject_revision(self, report):
        return await self.handle_revision(report['id'], report['revision']['propositions'], 'reject')