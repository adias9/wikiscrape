import scrapy
from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from wikiscrape.items import WikiscrapeItem
from bs4 import BeautifulSoup
import re


class WikiscrapeSpider(CrawlSpider):
    name = "wikiscrape"
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
            callback="parse", follow=True),
    )

    def filter_links(self, response):
        responseSelector = Selector(response)
        soup = BeautifulSoup(response.body)
        description = soup.find("div", {"id": "mw-content-text"})
        # get the first tag
        description = str(description.find('p'))
        # divs = responseSelector.xpath("//div[contains(@id, 'mw-content-text')]")
        # if divs.xpath(".//p")[0].re(r"born"):
        regexp1 = re.compile(r"born")
        if regexp1.search(description):
            regexp2 = re.compile(r"rapper")
            if regexp2.search(description):
            # if divs.xpath(".//p")[0].re(r"rapper"):
                item = WikiscrapeItem()
                item['title'] = soup.find("h1", {"id": "firstHeading"}).string
                # item['title'] = responseSelector.xpath("//*[contains(@id, 'firstHeading')]/text()").extract_first()
                item['link'] = response.url
                # extract all links from page
                all_links = responseSelector.xpath('*//a/@href').extract()
                item['connect_links'] = all_links
                yield item

    def parse(self, response):
        for link in SgmlLinkExtractor(allow ="https://en\.wikipedia\.org/wiki/.+_.+", 
                    deny = [
                        "https://en\.wikipedia\.org/wiki/Wikipedia.*",
                        "https://en\.wikipedia\.org/wiki/Main_Page",
                        "https://en\.wikipedia\.org/wiki/Free_Content",
                        "https://en\.wikipedia\.org/wiki/Talk.*",
                        "https://en\.wikipedia\.org/wiki/Portal.*",
                        "https://en\.wikipedia\.org/wiki/Special.*"
                    ]).extract_links(response):
            yield scrapy.http.Request(response.urljoin(link.url),callback=self.filter_links)
