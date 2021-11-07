import os
import scipy.io as sio
from datetime import datetime

from .es7 import ES7
from .support import TorHelper


class TorPipeline(object):

    def __init__(self):
        self.helper = TorHelper()
        self.es = ES7()

    def persist_fingerprint(self, domain, image_url, fingerprint):
        base_path = "/mnt/data/{domain}".format(domain=domain)
        image_id = self.helper.get_esid(image_url)
        try:
            os.makedirs(base_path)
        except OSError:
            pass

        path = "{base}/{id}".format(base=base_path, id=image_id)
        sio.savemat(path, fingerprint)

        return "{base}/{id}".format(base=domain, id=image_id)

    def process_item(self, item, spider):
        url = item["url"]
        domain = item["domain"]
        images = item["meta"]

        reports = []
        for img_url, meta in images.items():
            fingerprint_path = self.persist_fingerprint(domain, img_url, meta["fingerprint"]) if meta["fingerprint"] \
                else None
            tag = {
                "_id": self.helper.get_esid(url + img_url),
                "_source": {
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "source": "tor",
                    "method": "image",
                    "version": 1,
                    "info": {
                        "domain": domain,
                        "url": url,
                        "image_url": img_url,
                        "fingerprint_path": fingerprint_path,
                        "hash": meta["hash"],
                        "meta": meta["exif"],
                        "type": meta["type"],
                        "dimensions": {
                            "height": meta["height"],
                            "width": meta["width"]
                        }
                    }
                }
            }
            reports.append(tag)

        self.es.bulk_persist_reports(reports)
