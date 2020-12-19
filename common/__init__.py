from .log import init_log
from .mongo import MongoOpea
from .request import DealRequest, magic
from .soup import DealSoup

logger = init_log()
mongo = MongoOpea()
request_proxy = DealRequest(
    proxy={
        "http": "http://dynamic.xiongmaodaili.com:8089",
        "https": "http://dynamic.xiongmaodaili.com:8089"
    })
soup = DealSoup()

__all__ = ['logger', 'request_proxy', 'soup']
