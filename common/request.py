import urllib3
import requests
from common.log import logger


class DealRequest(object):
    def __init__(self):
        self.logger = logger
        self.session = self.init_session()
        super().__init__()

    def init_session(self):

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        requests.adapters.DEFAULT_RETRIES = 10
        session = requests.session()
        session.keep_alive = False
        session.verify = False

        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def package(self, path, header={}, data=None, **kwargs):

        if not path or 'http' not in path:
            return False
        param = {}
        param['url'] = path
        param['headers'] = header
        param['data'] = data
        param['timeout'] = (3, 15)
        param['proxies'] = None
        param['cookies'] = kwargs.get('cookies')

        self.params = param

    def get(self):
        try:
            return self.session.get(**self.params)
        except Exception as exc:
            logger.error(
                f'the uri is error - {self.params.get("url")} - {exc}')

    def post(self):
        try:
            return self.session.post(**self.params)
        except Exception as exc:
            logger.error(
                f'the uri is error - {self.params.get("url")} - {exc}')

    def retry(self, get=True):
        retry_count = 5

        while retry_count:
            if get:
                resp = self.post()
            else:
                resp = self.get()

            if resp:
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 404:
                    return
            else:
                retry_count -= 1
                logger.info(f'第 {6-retry_count} 次尝试')

    def run(self, path, header={}, data=None, byte=None, json=None, **kwargs):
        self.package(path, header, data=None, **kwargs)

        resp = self.retry(data)

        if resp is None:
            return ""
        elif isinstance(resp, str):
            return resp
        elif isinstance(resp, int):
            return resp
        elif byte:
            return resp.content
        elif json:
            return resp.json
        else:
            return resp.text
