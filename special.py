import os
from common.request import *
from common.soup import DealSoup
from common.mongo import MongoOpea

MONGO = MongoOpea()
REQ = DealRequest().run
SOUP = DealSoup().judge
HEADER = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
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
CONFIG = MONGO.select('domain', _id=False)
ROOT_PATH = {
    'special_thumb': f'./static/{CONFIG.get("special_thumb_root")}',
    'album_thumb': f'./static/{CONFIG.get("album_thumb_root")}',
    'images': f'./static/{CONFIG.get("album_root")}',
}
HOSTS = {
    'album_thumb_host': CONFIG.get('album_thumb_host'),
    'special_thumb_host': CONFIG.get('special_thumb_host'),
    'album_host': CONFIG.get('album_host'),
    'special_host': CONFIG.get('special_host'),
}


def init_path():
    for key in ROOT_PATH:
        if os.path.isdir(ROOT_PATH[key]):
            continue
        os.makedirs(ROOT_PATH[key])


def save(path, content):
    with open(path, 'wb') as fn:
        fn.write(content)


def image_download(uri):
    return REQ(uri, IMAGE_HEADER, byte=True)


def special_thumb():
    init_path()
    domain = f'{HOSTS["special_thumb_host"]}{ROOT_PATH["special_thumb"]}'
    results = MONGO.select('special', limit=200)
    for result in results:
        path = result.get('special_thumb')
        _id = result.get("_id")
        if domain not in path:
            logger.error(f'special host not in {_id}')
            return

        content = image_download(path)
        filename = path.split('/')[-1]
        save(f'static/mw690/{filename}', content)
        logger.info(f'已保存 - {filename}')

        result = MONGO.update({'_id': result.get('_id')},
                              {'special_thumb': path.replace(domain, '')},
                              'special')

        logger.info(f'已更新 - {_id}')


def albums_thumb():
    init_path()
    domain = f'{HOSTS["album_thumb_host"]}{ROOT_PATH["album_thumb"]}'
    results = MONGO.select('albums', limit=200)
    while results:
        for result in results:
            path = result.get('album_thumb')
            _id = result.get("_id")
            if domain not in path:
                logger.error(f'albums host not in {_id}')
                continue

            content = image_download(path)
            fullpath = f'static/thumb/{path.split("thumb/")[-1]}'
            dirpath = fullpath.replace(fullpath.split('/')[-1], '')
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
            save(fullpath, content)
            logger.info(f'已保存 - {fullpath}')

            result = MONGO.update({'_id': _id},
                                  {'album_thumb': path.replace(domain, '')},
                                  'albums')

            logger.info(f'已更新 - {_id}')

        results = MONGO.select('albums', {'_id': {'$gt': _id}}, limit=200)


def home_page():
    special = None

    resp = REQ(HOSTS['special_host'], HEADER)
    tag = SOUP(resp, {'class': 'tags'})

    for dd in tag.contents:
        if isinstance(dd, str):
            continue
        if dd.name == 'dt':
            if dd.text == '标签':
                label = True
            else:
                label = False

        elif dd.name == 'dd':
            info = {}
            temp = dd.a
            href = temp['href']
            info['special_thumb'] = temp.img['data-original']
            info['special_tag'] = href.strip('/').split('/')[-1]
            name = 'label' if label == True else 'girl'
            info[name] = temp.text

            result = secondary_page(href)
            info['children'] = result

            result = MONGO.repeat({'special_tag': info['special_tag']}, info,
                                  'special')
            logger.info(f'已插入 - special - {result}')


def secondary_page(uri, page=1):
    data = []
    resp = REQ(uri, HEADER)

    if not resp:
        return data

    pin = SOUP(resp, {'id': 'pins'})

    for li in pin.contents:
        if isinstance(li, str):
            continue
        if li.name == 'li':
            info = {}
            temp = li.a
            href = temp['href']
            info['album_id'] = href.split('/')[-1]
            info['album_thumb'] = temp.img['data-original']
            info['album_title'] = temp.img['alt']
            info['page'] = page

            condition = {'album_id': info['album_id']}
            result = MONGO.repeat(condition, info, 'albums')
            if not result:
                result = MONGO.select('albums', condition)
                logger.info(f'已存在 - albums - {result}')
            else:
                logger.info(f'已插入 - albums - {result}')

            data.append(result)
        else:
            logger.warning(f'secondary page tag is {li.name}')

    page += 1
    uri = f'{uri.split("page")[0]}page/{page}'
    data.extend(secondary_page(uri, page))

    return data


def main():
    pass


if __name__ == "__main__":
    # home_page()
    # special_thumb()
    albums_thumb()