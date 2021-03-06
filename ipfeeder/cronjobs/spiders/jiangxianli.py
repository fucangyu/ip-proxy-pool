import random

import gevent
from cronjob.apps.spider_app import SpiderJob
from lxml import etree

from ipfeeder.db import db
from ipfeeder.utils import ProxyIP, shuffle_pages


class JiangxianliProxy(SpiderJob):
    rule = '20m'
    right_now = True
    cancelled = False

    urls = [
        f'http://ip.jiangxianli.com/?page={i}' for i in shuffle_pages(1, 5)
    ]

    def run(self) -> None:
        for url in self.urls:
            response = self.http.get(url)
            if not response.ok:
                self.logger.error(f'request failed {response.status_code}')
                continue
            html = etree.HTML(response.content)
            trs = html.xpath('.//table//tr')
            for tr in trs:
                tds = tr.xpath('./td/text()')
                if len(tds) < 5:
                    continue
                ip = tds[1]
                port = tds[2]
                protocol = tds[4]
                proxy_ip = ProxyIP(ip, port, protocol)
                if proxy_ip.ok:
                    self.logger.info(f'got raw proxy_ip {str(proxy_ip)}')
                    db.add_raw(str(proxy_ip))
            gevent.sleep(random.randint(11, 23))
