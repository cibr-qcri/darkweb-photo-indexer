import signal

from scrapy_redis.spiders import RedisSpider

from ..items import TorspiderItem
from ..support import TorHelper


class TorSpider(RedisSpider):
    name = "darkweb-photo-indexer"

    def __init__(self):
        RedisSpider.__init__(self)

        signal.signal(signal.SIGINT, self.handler_stop_signals)
        signal.signal(signal.SIGTERM, self.handler_stop_signals)
        self.helper = TorHelper()

    def handler_stop_signals(self, signum, frame):
        self.logger.error("SIGTERM RECV")

    def make_requests_from_url(self, url):
        self.logger.info(f'start request url:{url}')
        return TorHelper.build_splash_request(url, callback=self.parse)

    def parse(self, response):
        images = response.data['images']
        url = response.url.strip("/")

        item = TorspiderItem()
        item["domain"] = self.helper.get_domain(url)
        item["url"] = url
        is_success, item["meta"] = TorHelper.fingerprint(images)

        if not is_success:
            return

        yield item
