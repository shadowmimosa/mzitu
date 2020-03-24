import time
import random
import urllib3
import requests
from common.log import logger


def magic():
    sleep_time = round(random.uniform(0, 3), 2)
    logger.info(f'魔法时间 - {sleep_time}')
    time.sleep(sleep_time)


class DealRequest(object):
    def __init__(self, proxy=None):
        self.proxy = proxy
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
        param['timeout'] = (4, 20)
        param['proxies'] = self.proxy
        param['cookies'] = kwargs.get('cookies')
        param['allow_redirects'] = False

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

            status_code = resp.status_code
            if status_code == 200:
                if self.proxy and resp.text == '{"code":200,"msg":"超过并发限制"}':
                    logger.info('超过并发限制')
                    magic()
                    self.retry(get)
                else:
                    return resp
            elif 400 <= status_code < 500:
                return status_code
            elif 300 <= status_code <= 304:
                self.params['url'] = resp.headers['Location']
                return self.retry(get)
            else:
                retry_count -= 1
                logger.info(f'第 {5-retry_count} 次尝试')

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
