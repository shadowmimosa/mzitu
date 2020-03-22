import bs4

from bs4 import BeautifulSoup


class DealSoup(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def find_tag_by_attr(self):
        if self.all_tag is False:
            return self.soup.find(attrs=self.attr)
        else:
            return self.soup.find_all(attrs=self.attr)

    def find_tag_by_name(self):
        if self.all_tag is False:
            return self.soup.find(self.attr)
        else:
            return self.soup.find_all(self.attr)

    def find_tag(self):
        if isinstance(self.attr, dict):
            return self.find_tag_by_attr()
        elif isinstance(self.attr, str):
            return self.find_tag_by_name()

    def init_soup(self):
        if isinstance(self.content, str):
            self.soup = BeautifulSoup(self.content, "lxml")
        elif isinstance(self.content, bs4.Tag):
            self.soup = self.content
        elif isinstance(self.content, bs4.BeautifulSoup):
            print("略略略")
    
    def judge(self, content, attr: dict = None, all_tag: bool = False):
        self.content = content
        self.attr = attr
        self.all_tag = all_tag

        self.init_soup()

        if self.attr is None:
            return self.soup
        else:
            return self.find_tag()