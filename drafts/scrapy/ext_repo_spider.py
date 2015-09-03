import scrapy
import urllib
from scrapy.crawler import CrawlerProcess


class ExternalRepoSpider(scrapy.Spider):
    name = "typo3-extscan"
    start_urls = ['https://typo3.org/extensions/repository/']

    def parse(self, response):
        # process extensions page from repository index
        for item in self.parse_page(response):
            yield item

        # grab last pagination ID
        n = response.xpath('//a[starts-with(@href, "/extensions/repository/?tx_solr")]/@href').extract()
        n = n[-1].split('=')[1]
        # request each page of extensions
        for i in xrange(1, int(n) + 1):
            url = 'https://typo3.org/extensions/repository/?tx_solr' + urllib.quote('[page]') + '=' + str(i)
            yield scrapy.Request(url=url, callback=self.parse_page)


    def parse_page(self, response):
        # process a page of extensions
        extensions = response.xpath('//a[starts-with(@href, "/extensions/repository/view/")]/@href').extract()
        for i in extensions:
            yield scrapy.Request('https://typo3.org' + i, callback=self.parse_item_page)


    def parse_item_page(self, response):

        # some extensions don't exist but are listed on the repo page, let's filter and ignore that
        if str(response.xpath('//p/text()').extract()[0]) == 'Extension not found':
            return

        name = str(response.xpath('//tr[th[text()="Extension key"]]/td/strong/text()').extract()[0])
        updated = str(response.xpath('//tr[th[text()="Last updated"]]/td/text()').extract()[0])
        uploaded = str(response.xpath('//tr[th[text()="First upload"]]/td/text()').extract()[0])
        downloads = str(response.xpath('//tr[th[text()="Downloads"]]/td/text()').extract()[0])

        version = response.xpath('//tr[th[text()="Version"]]/td')
        version = str(version.xpath('text()').extract()[0] + ' ' + version.xpath('span/text()').extract()[0])

        category = str(response.xpath('//tr[th[text()="Category"]]/td/text()').extract()[0])
        category = category.replace('\t', '').replace('\n', '')

        # TODO: populate database with this data (via API calls or plain DB connection)
        print {
            'name': name,
            'version': version,
            'uploaded': uploaded,
            'updated': updated,
            'downloads': downloads,
            'category': category if len(category) != 0 else 'Unknown',
            # dependencies, external repo?
        }


process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
    'LOG_LEVEL': 'ERROR',
})

process.crawl(ExternalRepoSpider)
process.start()
