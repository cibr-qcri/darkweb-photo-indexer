import base64
import re
from datetime import datetime
from hashlib import sha256
from io import BytesIO
from urllib.parse import urlparse

import imagehash
import numpy as np
import piexif
from PIL import Image
from scrapy.utils.project import get_project_settings
from scrapy_splash import SplashRequest

from .es7 import ES7
from .prnu import extract_single

request_count = dict()


class TorHelper:

    def __init__(self):
        settings = get_project_settings()
        self.es = ES7()

    @staticmethod
    def unify(url, scheme):
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            pass
        else:
            url = "/" + url if not url.startswith("/") else url
            url = scheme + "://" + url
        return url.strip("/")

    @staticmethod
    def get_scheme(url):
        return urlparse(url).scheme

    @staticmethod
    def get_domain(url):
        net_loc = urlparse(url).netloc
        domain_levels = re.split("[.:]", net_loc)
        for idx, oni in enumerate(domain_levels):
            if idx == 0:
                continue
            if oni == "onion" and len(domain_levels[idx - 1]) in (16, 56):
                return domain_levels[idx - 1] + "." + oni

        return net_loc

    @staticmethod
    def get_esid(url):
        es_id = url + datetime.today().strftime("%d-%m-%y")
        es_id = sha256(es_id.encode("utf-8")).hexdigest()

        return es_id

    @staticmethod
    def get_lua_script():
        return """
                    treat = require("treat")

                    function main(splash, args)
                        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0')
                        
                        splash:on_request(function(request)
                            request:enable_response_body()
                        end)

                        images = {}
                        splash:on_response(function(response)
                            request_accept_type = response.request.headers['Accept']
                            response_accept_type = string.lower(response.headers['Content-Type'])
                            s = response.status                            
                            if s >= 200 and s < 400 then
                                if string.find(request_accept_type, "image") or string.find(response_accept_type, "image") then
                                    images[response.request.url] = response.body
                                end
                            end
                        end)

                        splash:with_timeout(function()
                            splash:go(args.url)
                            splash:wait(args.wait)
                        end, 150)
                        return {
                            images = images
                        }
                    end
                    """

    @staticmethod
    def build_splash_request(url, callback=None, wait=15):
        args = {'lua_source': TorHelper.get_lua_script(), 'timeout': 200, "wait": wait}

        request = SplashRequest(url, method='POST', callback=callback, args=args, endpoint='execute')
        return request

    @staticmethod
    def fingerprint(images):
        fingerprint = {}
        for url, image in images.items():
            im = Image.open(BytesIO(base64.b64decode(image)))

            fingerprint[url] = {
                "exif": TorHelper.get_exif(im),
                "hash": TorHelper.get_hashes(im),
                "fingerprint": TorHelper.get_fingerprint(im)
            }

        return fingerprint

    @staticmethod
    def get_fingerprint(image):
        fingerprint = None
        try:
            fingerprint = extract_single(np.asarray(image)).tolist()
        except ValueError:
            pass

        return fingerprint

    @staticmethod
    def get_exif(image):
        if "exif" not in image.info:
            return {}
        exif_dict = piexif.load(image.info["exif"])
        w, h = image.size
        exif_dict["0th"][piexif.ImageIFD.XResolution] = (w, 1)
        exif_dict["0th"][piexif.ImageIFD.YResolution] = (h, 1)

        return exif_dict

    @staticmethod
    def get_hashes(image):
        return {
            "perceptual_hash": str(imagehash.phash(image)),
            "distance_hash": str(imagehash.dhash(image))
        }
