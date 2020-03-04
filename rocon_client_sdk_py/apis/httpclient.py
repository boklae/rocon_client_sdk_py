import aiohttp
from .api_worker import ApiWorker
from .api_report import ApiReport
from .api_task import ApiTask
from .api_configuration import ApiConfiguration
from .api_site_configuration import ApiSiteConfiguration
from .api_worker_pool import ApiWorkerPool

class HttpClient():
    def __init__(self, hostname_concert='localhost:10602', hostname_config='localhost:10605', hostname_site_config='localhost:10604', hostname_worker_pool='localhost:10999'):
        self._hostname_concert = hostname_concert
        self._hostname_config = hostname_config
        self._hostname_site_config = hostname_site_config
        self._hostname_worker_pool = hostname_worker_pool

        # http client instance 생성
        #TODO instance 생성 및 request/response interceptor 처리 루틴 방안 검토 필요
        headers = {'Content-type': 'application/json'}

        self._request = aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(force_close=True))

        # api 속성 설정
        self.api_worker = ApiWorker(self)
        self.api_report = ApiReport(self)
        self.api_task = ApiTask(self)
        self.api_config = ApiConfiguration(self)
        self.api_site_config = ApiSiteConfiguration(self)
        self.api_worker_pool = ApiWorkerPool(self)

    def ensure_path(self, path):
        if path[0] != '/':
            path = '/' + path

        return path

    def gateway_url(self, path):
        return 'http://{}{}'.format(self._hostname_concert, self.ensure_path(path))

    def scheduler_url(self, path):
        return 'http://{}/scheduler/v0{}'.format(self._hostname_concert, self.ensure_path(path))

    def site_config_url(self, path):
        return 'http://{}{}'.format(self._hostname_site_config, self.ensure_path(path))

    def config_url(self, path):
        return 'http://{}{}'.format(self._hostname_config, self.ensure_path(path))

    def worker_pool_url(self, path):
        return 'http://{}{}'.format(self._hostname_worker_pool, self.ensure_path(path))

    def request(self):
        if self._request.closed:
            self._request = self._request

        return self._request

