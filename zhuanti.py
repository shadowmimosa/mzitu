import os
from common.request import *
from common.soup import DealSoup
from common.mongo import MongoOpea

mongo = MongoOpea()
req = DealRequest().run
soup = DealSoup().judge
header = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}
image_header = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Referer': 'https://www.mzitu.com/tag/xinggan/page/5/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}


def init_path():
    for path in ['./static/mw690/', './static/thumb/', './static/images/']:
        if os.path.isdir(path):
            continue
        os.makedirs(path)


def save(path, content):
    with open(path, 'wb') as fn:
        fn.write(content)


def image_download(uri):
    return req(uri, image_header, byte=True)


def special_thumb():
    init_path()

    results = mongo.select('special', limit=200)
    for result in results:
        path = result.get('special_thumb')
        _id = result.get("_id")
        if 'https://wxt.sinaimg.cn/mw690/' not in path:
            logger.error(f'special host not in {_id}')
            return

        content = image_download(path)
        filename = path.split('/')[-1]
        save(f'static/mw690/{filename}', content)
        logger.info(f'已保存 - {filename}')

        result = mongo.update({'_id': result.get('_id')}, {
            'special_thumb':
            path.replace('https://wxt.sinaimg.cn/mw690/', '')
        }, 'special')

        logger.info(f'已更新 - {_id}')


def albums_thumb():
    init_path()

    results = mongo.select('albums', limit=200)
    while results:
        for result in results:
            path = result.get('album_thumb')
            _id = result.get("_id")
            if 'https://i.mmzztt.com/thumb/' not in path:
                logger.error(f'albums host not in {_id}')
                continue

            content = image_download(path)
            dirpath = f'static/thumb/{path.split("thumb/")[-1]}'
            os.makedirs(dirpath)
            save(dirpath, content)
            logger.info(f'已保存 - {dirpath}')

            result = mongo.update({'_id': result.get('_id')}, {
                'album_thumb':
                path.replace('https://i.mmzztt.com/thumb/', '')
            }, 'special')

            logger.info(f'已更新 - {_id}')

        results = mongo.select('albums', {'$gt': _id}, limit=200)


def home_page():
    special = None

    resp = req('https://www.mzitu.com/zhuanti/', header)
    tag = soup(resp, {'class': 'tags'})

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

            result = mongo.repeat({'special_tag': info['special_tag']}, info,
                                  'special')
            logger.info(f'已插入 - special - {result}')


def secondary_page(uri, page=1):
    data = []
    resp = req(uri, header)

    if not resp:
        return data

    pin = soup(resp, {'id': 'pins'})

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
            result = mongo.repeat(condition, info, 'albums')
            if not result:
                result = mongo.select('albums', condition)
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