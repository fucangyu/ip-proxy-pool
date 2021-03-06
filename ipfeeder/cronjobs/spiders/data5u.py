import traceback

import gevent
from cronjob.apps.spider_app import SpiderJob
from lxml import etree

from ipfeeder.db import db
from ipfeeder.utils import ProxyIP, decode_port


class Data5uProxy(SpiderJob):
    rule = [3600, 5400]  # 一个小时到一个半小时之间随机执行一次
    right_now = True  # 程序启动之后立马执行
    cancelled = False

    urls = [
        'http://www.data5u.com/',
        'http://www.data5u.com/free/gngn/index.shtml',
        'http://www.data5u.com/free/gnpt/index.shtml',
    ]

    def run(self) -> None:
        for url in self.urls:
            response = self.http.get(url)
            if not response.ok:
                self.logger.error(f'request failed {response.status_code}')
                continue
            html = etree.HTML(response.content)
            trs = html.xpath('.//ul[@class="l2"]')
            for tr in trs:
                try:
                    tds = tr.xpath('.//li//text()')
                    if len(tds) < 6:
                        continue
                    ip = tds[0]
                    protocol = tds[3]
                    raw_port = tr.xpath('.//li[1]/@class')[0].split(' ')[1]
                    port = decode_port(raw_port)
                    proxy_ip = ProxyIP(ip, port, protocol)
                    if proxy_ip.ok:
                        self.logger.info(f'got raw proxy_ip {str(proxy_ip)}')
                        db.add_raw(str(proxy_ip))
                except Exception:
                    self.logger.error(f'error occurred when crawl {url}')
                    traceback.print_exc()
            gevent.sleep(10)
