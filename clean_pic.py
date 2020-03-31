import os
from common.mongo import MongoOpea
from collect_baby import image_download, magic, MONGO


class CheckBrockImage(object):
    def __init__(self, train_dir):
        self.train_dir = train_dir
        self.completeFile = 0
        self.incompleteFile = 0

    def get_imgs(self):
        """遍历某个文件夹下的所有图片"""
        for root, _, files in os.walk(self.train_dir):
            for filename in files:
                fullpath = os.path.join(root, filename)
                if os.path.splitext(
                        fullpath)[1].lower() == '.jpg' or os.path.splitext(
                            fullpath)[1].lower() == ".jpeg":
                    ret = self.check_img(fullpath)
                    if ret:
                        self.completeFile += 1
                    else:
                        self.incompleteFile = self.incompleteFile + 1
                        print(fullpath)
                        reget(fullpath)
                        # self.img_remove(file)  # 删除不完整图片

    def img_remove(self, file):
        """删除图片"""
        os.remove(self.train_dir + file)

    def check_img(self, img_file):
        """检测图片完整性，图片完整返回True,图片不完整返回False"""
        return CheckImage(img_file).check_jpg_jpeg()

    def run(self):
        """执行文件"""
        self.get_imgs()
        print('不完整图片 : %d个' % self.incompleteFile)
        print('完整图片 : %d个' % self.completeFile)


class CheckImage(object):
    def __init__(self, img):
        with open(img, "rb") as f:
            f.seek(-2, 2)
            self.img_text = f.read()
            f.close()

    def check_jpg_jpeg(self):
        """检测jpg图片完整性，完整返回True，不完整返回False"""
        buf = self.img_text
        return buf.endswith(b'\xff\xd9')

    def check_png(self):
        """检测png图片完整性，完整返回True，不完整返回False"""

        buf = self.img_text
        return buf.endswith(b'\xaeB`\x82')


def save(path, url):
    dirpath = path.replace(path.split('/')[-1], '')

    while True:
        content = image_download(url)
        if isinstance(content, bytes):
            break
        else:
            magic()

    with open(path, 'wb') as fn:
        fn.write(content)

    return True


def reget(fullpath: str):
    fullpath = fullpath.replace('\\', '/').strip('.').strip('/')
    img_url = f'https://i3.mmzztt.com/{fullpath.replace("static/images", "")}'
    result = MONGO.select('images', {'image': fullpath})
    save(fullpath, img_url)


if __name__ == '__main__':
    train_dir = './static/images/'  # 检测文件夹
    imgs = CheckBrockImage(train_dir)
    imgs.run()
