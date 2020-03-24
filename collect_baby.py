import os
import time
import hashlib
import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

from config import PROXY
from common.request import *
from common.soup import DealSoup
from common.mongo import MongoOpea

MONGO = MongoOpea()
REQ = DealRequest({
    "http": "http://dynamic.xiongmaodaili.com:8089",
    "https": "http://dynamic.xiongmaodaili.com:8089"
}).run
SOUP = DealSoup().judge
HEADER = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # Referer: https://www.mzitu.com/tag/xingganneiyi/
    # Cookie: Hm_lvt_dbc355aef238b6c32b43eacbbf161c3c=1584844917; Hm_lpvt_dbc355aef238b6c32b43eacbbf161c3c=1584941199
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}
IMAGE_HEADER = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Referer': 'https://www.mzitu.com/tag/xinggan/page/5/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}
DOMAIN = MONGO.select('domain', _id=False)
ALBUM_HOST = DOMAIN.get('album_host')


def made_secret():
    timestamp = int(time.time())
    orderno = PROXY.get('orderno')
    secret = PROXY.get('secret')
    txt = f'orderno={orderno},secret={secret},timestamp={timestamp}'
    sign = hashlib.md5(txt.encode('utf-8')).hexdigest().upper()

    return f'sign={sign}&orderno={orderno}&timestamp={timestamp}&change=true'


def build_header(image=False):
    if image:
        header = IMAGE_HEADER
    else:
        header = HEADER

    if PROXY.get('proxy'):
        header.update({'Proxy-Authorization': made_secret()})

    return header


def image_download(uri):
    return REQ(uri, build_header(image=True), byte=True)


def save(path, url):
    dirpath = path.replace(path.split('/')[-1], '')
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    if os.path.isfile(path):
        logger.warning(f'已存在 - {path}')
        return

    while True:
        content = image_download(url)
        if isinstance(content, bytes):
            break
        else:
            magic()

    with open(path, 'wb') as fn:
        fn.write(content)

    return True


class CollectBaby(object):
    def __init__(self, item: dict):
        self._id = item.get('_id')
        self.album_id = item.get('album_id')
        self.album_info = {}
        self.pics = []

    def detail(self, html, page):
        if page == 1:
            soup = SOUP(html, {'class': 'main-meta'})
            self.album_info['category'] = soup.a.text
            self.album_info['post_at'] = SOUP(soup, 'span',
                                              all_tag=True)[-1].text.replace(
                                                  '发布于 ', '')

        soup = SOUP(html, {'class': 'main-image'})

        nextpage = soup.a['href']
        img_url = soup.img['src']
        temp = img_url.split('//')
        domain = f'{temp[0]}//{temp[-1].split("/")[0]}'
        fullpath = f'static/images{img_url.replace(domain, "")}'
        save_status = save(fullpath, img_url)
        if not save_status:
            result = MONGO.select('images', {
                'album': self._id,
                'image': fullpath,
                'page': page
            })
            if not result:
                result = MONGO.insert(
                    {
                        'image': fullpath,
                        'page': page,
                        'album': self._id,
                    }, 'images')
                logger.info(f'已下载 - {result}')      
            else:          
                logger.info(f'已读取 - {result}')
        else:
            result = MONGO.insert(
                {
                    'image': fullpath,
                    'page': page,
                    'album': self._id,
                }, 'images')
            logger.info(f'已下载 - {result}')

        self.pics.append(result)

    def page(self, page=1):
        retry_count = 5
        while retry_count:
            if page == 1:
                resp = REQ(f'{ALBUM_HOST}{self.album_id}/', build_header())
            else:
                resp = REQ(f'{ALBUM_HOST}{self.album_id}/{page}/',
                           build_header())

            if resp == 404:
                logger.info(f'下载完成 - {self.album_id}')
                return 404
            elif resp == 429:
                magic()
                continue
            else:
                # self.detail(resp, page)
                # page += 1
                # if self.page(page) == 404:
                #     return 404
                try:
                    self.detail(resp, page)
                except Exception as exc:
                    logger.error(f'{self.album_id} - detail is error - {traceback.format_exc()}')
                    retry_count -= 1
                else:
                    page += 1
                    if self.page(page) == 404:
                        return 404

    def collect(self):
        self.page()
        self.album_info.update({'children': self.pics, 'collected': 1})
        MONGO.update({'_id': self._id}, self.album_info, 'albums')


def thead_collect():
    results = MONGO.select('albums', {'collected': {'$ne': 1}}, limit=200)
    # thead_pool = ThreadPoolExecutor(5)
    thead_pool = ProcessPoolExecutor(5)

    while results:
        for result in results:
            baby = CollectBaby(result)
            # magic()
            thead_pool.submit(baby.collect)
            # baby.collect()

        results = MONGO.select('albums', {
            '_id': {
                '$gt': result.get('_id')
            },
            'collected': {
                '$ne': 1
            }
        },
                               limit=200)

    thead_pool.shutdown(wait=True)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    thead_collect()