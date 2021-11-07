from scrapy_redis.spiders import RedisSpider

from ..items import TorspiderItem
from ..support import TorHelper

from scrapy.exceptions import DontCloseSpider


class TorSpider(RedisSpider):
    name = "darkweb-photo-indexer"

    def __init__(self):
        RedisSpider.__init__(self)
        self.helper = TorHelper()

    def make_requests_from_url(self, url):
        return TorHelper.build_splash_request(url, callback=self.parse)

    def parse(self, response):
        images = response.data['images']
        url = response.url.strip("/")

        try:
            item = TorspiderItem()
            item["domain"] = self.helper.get_domain(url)
            item["url"] = url
            item["meta"] = TorHelper.fingerprint(images)

            yield item
        except:
            raise DontCloseSpider
