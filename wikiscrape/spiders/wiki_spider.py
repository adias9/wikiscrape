import scrapy
from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from wikiscrape.items import WikiscrapeItem
from wikiscrape.items import ConnectedNodeItem
from bs4 import BeautifulSoup
import re

import copy
import six

from scrapy.http import Request, HtmlResponse
from scrapy.utils.spider import iterate_spider_output
from scrapy.spiders import Spider

class WikiscrapeSpider(CrawlSpider):
    global seenLinks
    global seenTitles
    global seenTitleDict
    seenLinks = set()
    seenTitles = set()
    seenTitleDict = {}
    name = "wikiscrape"

    custom_settings = {
        'DEPTH_LIMIT': 2,
        'DEPTH_PRIORITY': 1,
        'CHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
    }

    allowed_domains = ["wikipedia.org"]
    start_urls = [
        "https://en.wikipedia.org/wiki/Kanye_West",
    ]

    rules = (
        Rule(SgmlLinkExtractor(allow="https://en\.wikipedia\.org/wiki/.+_.+", 
            deny = [
                "https://en\.wikipedia\.org/wiki/Wikipedia.*",
                "https://en\.wikipedia\.org/wiki/Main_Page",
                "https://en\.wikipedia\.org/wiki/Free_Content",
                "https://en\.wikipedia\.org/wiki/Talk.*",
                "https://en\.wikipedia\.org/wiki/Portal.*",
                "https://en\.wikipedia\.org/wiki/Special.*"
            ]),
            callback="filter_links", follow=True),
    )

    def filter_links(self, response):
        responseSelector = Selector(response)
        soup = BeautifulSoup(response.body)
        description = soup.find("div", {"id": "mw-content-text"})
        # get the first tag
        description = str(description.find('p'))

        regexp1 = re.compile(r"born")
        if regexp1.search(description):
            regexp2 = re.compile(r"rapper")
            if regexp2.search(description):
                title = soup.find("h1", {"id": "firstHeading"}).string
                prev_link = response.request.headers.get('Referer', None)

                if title not in seenTitles:
                    seenTitles.add(title)
                    seenTitleDict[title]=response.url
                    item = WikiscrapeItem()
                    item['title'] = title
                    item['link'] = response.url
                    # extract all links from page
                    item['prev_link'] = prev_link
                    yield item
                else:
                    item = ConnectedNodeItem()
                    item['source_link'] = prev_link
                    item['existent_link'] = seenTitleDict[title]
                    yield item
        return 

# Modifying source code of scrapy
# ---------------------------------------------------------------------------------------

    def process_results(self, response, results):
        return results

    # yes 
    def _build_request(self, rule, link):
        r = Request(url=link.url, callback=self._response_downloaded)
        r.meta.update(rule=rule, link_text=link.text)
        return r

    # yes 
    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        # seen = set() Made this a global variable to save all seen values
        filtered_response = self.filter_links(response)
        checker = filtered_response.next()
        if checker is not None:
            # if "existent_link" not in checker:
            for n, rule in enumerate(self._rules):
                links = []
                for lnk in rule.link_extractor.extract_links(response):
                    if lnk not in seenLinks:
                        links.append(lnk)
                if links and rule.process_links:
                    links = rule.process_links(links)
                for link in links:
                    seenLinks.add(link)
                    r = self._build_request(n, link)
                    yield rule.process_request(r)

    # yes 
    def _response_downloaded(self, response):
        rule = self._rules[response.meta['rule']]
        return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)

    # yes 
    def _parse_response(self, response, callback, cb_kwargs, follow=True):
        if callback:
            cb_res = callback(response, **cb_kwargs) or ()
            cb_res = self.process_results(response, cb_res)
            for requests_or_item in iterate_spider_output(cb_res):
                yield requests_or_item

        if follow and self._follow_links:
            for request_or_item in self._requests_to_follow(response):
                yield request_or_item
