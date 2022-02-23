from scrapy import Spider, Request
from goodrx_part1.items import GoodRxItem
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

# (3) Scrapping drug's 'price' page
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
        info = response.xpath('//li[@data-qa="drug_info_btn"]/a/@href').extract_first()
        if info == None:
            info_name = ""
        else:
            info = re.search('\/(.*?)\/what-is', info).group(1).title()
            info_name = re.sub('-'," ", info)

        # form of the drug
        form = response.xpath('//div[@id="uat-dropdown-form"]//text()').extract_first()

        # Dosage: split by number and the type
        dosage = response.xpath('//div[@id="uat-dropdown-dosage"]//text()').extract_first()
        try:
            dosage_num = float(re.findall('^[0-9]*\.?[0-9]?', dosage)[0])
        except (ValueError, IndexError):
            dosage_num = dosage
        try:
            dosage_type = re.findall('[a-zA-Z]+\-?[a-zA-Z]*',dosage)[0]
        except (ValueError, IndexError):
            dosage_type = dosage

        # Quantity: split by number and the type 
        quantity = response.xpath('//div[@id="uat-dropdown-quantity"]//text()').extract_first()
        quantity_num = int(re.findall('^\d*', quantity)[0])
        quantity_type = re.findall('[a-zA-Z]+\-?[a-zA-Z]*', quantity)[0]

        # Generic: find out if the prices are based on generic or brand 
        price_generic = response.xpath('//div[@id="uat-dropdown-brand"]/text()').extract_first()
        if price_generic == " ":
            price_generic = response.xpath('//div[@id="uat-dropdown-brand"]/span[2]/text()[2]').extract_first()
        
        # find if drug is generic 
        generic = response.xpath('//div[@id="uat-drug-alternatives"]/text()').extract()
        for g in generic:
            gen = re.findall('\w+', g)
            if len(gen) !=0:
                generic = gen
            else:
                generic = ''

        # alternative drug name: this is usually brand name

        alternative = response.xpath('//div[@id="uat-drug-alternatives"]/a//text()').extract()
        if len(alternative)==0:
            alternative = response.xpath('//div[@id="uat-drug-alternatives"]//text()').extract()
        else:
            alist = []
            if type(alternative)== str:
                alt = re.findall('\w*\s?\w*\.?\w*', alternative)
                for a in alt:
                    if len(a)>0:
                        letters = e.strip().title()
                        alist.append(letters)
                alternative = ' '.join(map(str,elist))
            elif type(alternative)== list: 
                for alt in alternative:
                    alt = re.findall('\w*\s?\w*\.?\w*', alt)
                    sublist = []
                    for a in alt:
                        if len(a)>0:
                            a= a.strip().title()
                            sublist.append(a)  
                    subname = ' '.join(map(str,sublist))
                    alist.append(subname)
                    alternative = alist


        # Club: get club prices which represent the lowest option and remove the '$'
        try:
            club = response.xpath('//div[@data-qa="savingsClubs_tab_subtitle"]//text()').extract_first().split()[-1].replace('$','')
        except (AttributeError, IndexError):
            club = ""
        # Remove the ',' if the price is over $999
        try:
            club = [club.replace(',','') if (re.search(',', club)!=None) else club][0]
        except (AttributeError, IndexError):
            club = 'prices'
        # If there is no prices for club --> none
        try:
            club = [None if club =='prices' else club][0]
        except (AttributeError, IndexError):
            club = ""
        # Mailorder: price which represent the lowest option and remove the '$'
        try:
            mailorder = response.xpath('//div[@data-qa="mailOrder_tab_subtitle"]//text()').extract_first().split()[-1].replace('$','')
        except (AttributeError, IndexError):
            mailorder = ""
        # Remove the ',' if the price is over $999
        try:
            mailorder = [mailorder.replace(',','') if (re.search(',', mailorder)!=None) else mailorder][0]
        except (AttributeError, IndexError):
            mailorder = 'prices'
        # If there is no prices for mailorder --> none
        try:
            mailorder = [None if mailorder =='prices' else mailorder][0]
        except (AttributeError, IndexError):
            mailorder = ""

        # Freecoupons: get freecoupon prices which represent the lowest option and remove the '$'
        freecoupons = response.xpath('//div[@data-qa="coupons_tab_subtitle"]//text()').extract_first().split()[-1].replace('$','')
        # Remove the ',' if the price is over $999
        freecoupons = [freecoupons.replace(',','') if (re.search(',', freecoupons)!=None) else freecoupons][0]
        # If there is no prices for freecoupons --> none
        freecoupons = [None if freecoupons =='prices' else freecoupons][0]

        # Pharmacy: gathers each pharmacies name, free coupon price and retail price
        rows =  response.xpath('//li[@data-qa="price_row"]/div[1]')
        for row in rows:
            pharmacy = row.xpath('.//div[@data-qa="store_name"]/span[2]/text()').extract_first()
            coupon_type = row.xpath('.//div[@data-qa="price_description"]/text()').extract_first()

            # Retail:  retail price of freecoupon and remove the '$'
            retail = row.xpath('.//div[@data-qa="cash_price"]//span[1]/text()')
            try:
                retail = [None if len(retail)==0 else retail.extract_first().replace('$','')][0]
            except (AttributeError, IndexError):
                retail = None
            # Remove the ',' if the price is over $999
            if retail == None:
                retail = None
            else:
                retail = [retail.replace(',','') if (re.search(',', retail)!=None) else retail][0]

            # Price: price of freecoupon per pharmacy and remove the '$'
            price = row.xpath('.//div[@data-qa="drug_price"]//text()').extract()[-2].replace('$','')
            # Remove the ',' if the price is over $999
            price = [price.replace(',','') if (re.search(',', price)!=None) else price][0]


        # yields the items of interest 
            item = GoodRxItem()
            item['name'] = name
            item['pharmacy'] = pharmacy
            item['price'] = price
            item['retail'] = retail
            item['freecoupons'] = freecoupons
            item['club'] = club
            item['mailorder'] = mailorder
            item['coupon_type'] = coupon_type
            item['alternative'] = alternative
            item['price_generic'] = price_generic
            item['generic'] = generic
            item['form'] = form
            item['dosage_num'] = dosage_num
            item['dosage_type'] = dosage_type
            item['quantity_num'] = quantity_num
            item['quantity_type'] = quantity_type
            item['info_name'] = info_name

            yield item

