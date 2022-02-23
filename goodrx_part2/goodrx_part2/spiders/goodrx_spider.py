from scrapy import Spider, Request
from goodrx_part2.items import GoodRxItem
import string
import re


class GoodRxSpider(Spider):
    name = 'goodrx_spider'
    allowed_urls = ['https://www.goodrx.com/']
    start_urls = ['https://www.goodrx.com/drugs']


# (1) Get to each letter of the alphabet page with drugs by letter
    def parse(self, response):
        alphabet = string.ascii_lowercase
        letter_urls = [f'https://www.goodrx.com/drugs/{l}' for l in alphabet]

        for url in letter_urls:
            yield Request(url=url, callback=self.parse_letter_page)


# (2) Get to each drug's 'price' page with first details to scrape
    def parse_letter_page(self, response):

        # Get drug URL from the drug's name
        drug_urls = response.xpath('//div[@class="topDrugGrid-3ZxaH"]//a/@href').extract()
        drug_urls = ['https://www.goodrx.com' + url for url in drug_urls]

        for url in drug_urls:
            yield Request(url=url, callback=self.parse_price_page)



##############
    # # Get drug URL from the drug's name
    #     drug_urls = response.xpath('//div[@class="topDrugGrid-3ZxaH"]//a/@href').extract()
    #     drug_urls = ['https://www.goodrx.com' + url for url in drug_urls]
    #     drug_urls = ['{}/what-is'.format(url) for url in drug_urls]
        

    #     for url in drug_urls:
    #         # capture name before the /what-is gets requested, since sometimes the drug name changes
    #         name = re.search('https://www.goodrx.com/(.*)/what-is', url).group(1).replace("-", " ").title()

    #         yield Request(url=url, meta={'name': name}, callback=self.parse_info_page)

 ############

# (3) Scrape drug price page to get name and go to info page
    def parse_price_page(self, response):

        # Name
        name = response.xpath('//h1[@id="uat-drug-title"]//text()').extract_first()
        nlist = []
        names = re.findall('\w*\s?\w*\.?\w*', name)
        for n in names:
            if len(n)>0:
                name= n.strip().title()
                nlist.append(name)
        name = ' '.join(map(str,nlist))


        # name that will tie to the second spider extract
        info_name = response.xpath('//li[@data-qa="drug_info_btn"]/a/@href').extract_first()
        if info_name == None:
            info_name = ""
        else:
            info_name = re.search('\/(.*?)\/what-is', info_name).group(1).title()
            info_name = re.sub('-'," ", info_name)

        meta = {'name': name, 'info_name': info_name}

        info = response.xpath('//li[@data-qa="drug_info_btn"]/a/@href').extract_first()
        if info == None:
            item = GoodRxItem()
            item['name'] = name
            item['info_name'] = info_name
            yield item
        else:
            # url to click into
            info_url = 'https://www.goodrx.com' + info 
            yield Request(url=info_url, meta=meta, callback=self.parse_info_page)

# (4) Scrapping drug's 'info' page
    def parse_info_page(self, response):
        
        name = response.meta['name']
        info_name = response.meta['info_name']

        # Brand name
        try:
            brand_name = response.xpath('//div[@data-qa="ColumnContainer"]/div[1]//p[1]//text()').extract_first()
        except AttributeError:
            brand_name = ""
        # Generic status
        try:
            generic_status = response.xpath('//div[@data-qa="ColumnContainer"]/div[2]//p[1]//text()').extract_first()
        except AttributeError:
            generic_status = ""

        # Drug class
        try:
            drug_class = response.xpath('//div[@data-qa="ColumnContainer"]/div[1]//p[2]//text()').extract_first()
        except AttributeError:
            drug_class = ""
        # Medical Uses
        try:
            medical_use = response.xpath('//ul[@class="list-disc my-component-4"]//text()').extract_first()
        except AttributeError:
            medical_use = ""
        # Alternative drug name
        try:
            alt_drug_name = response.xpath('//div[@data-qa="DrugComparisonItem"]/div[1]/div[1]/text()').extract()
        except AttributeError:
            alt_drug_name = ""
        # Alternative drug price
        try:
            alt_drug_price =  response.xpath('//div[@data-qa="DrugComparisonItem"]//h3[1]//span[1]/text()').extract()
        except AttributeError:
            alt_drug_price = ""


        # Yields the items of interest 
        item = GoodRxItem()
        item['name'] = name
        item['info_name'] = info_name
        item['brand_name'] = brand_name
        item['generic_status'] = generic_status
        item['drug_class'] = drug_class
        item['medical_use'] = medical_use
        item['alt_drug_name'] = alt_drug_name
        item['alt_drug_price'] = alt_drug_price

        yield item

