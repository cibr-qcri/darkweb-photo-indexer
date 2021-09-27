from datetime import datetime

from .es7 import ES7
from .support import TorHelper


class TorPipeline(object):

    def __init__(self):
        self.helper = TorHelper()
        self.es = ES7()

    def process_item(self, item, spider):
        url = item["url"]
        domain = item["domain"]
        images = item["meta"]

        reports = []
        for img_url, meta in images.items():
            tag = {
                "_id": self.helper.get_esid(url + img_url),
                "_source": {
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "type": "photo-index",
                    "source": "tor",
                    "method": "image",
                    "version": 1,
                    "info": {
                        "domain": domain,
                        "url": url,
                        "image_url": img_url,
                        "meta": meta
                    }
                }
            }
            reports.append(tag)

        self.es.bulk_persist_reports(reports)
