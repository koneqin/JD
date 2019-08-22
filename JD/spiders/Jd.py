# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisSpider
from copy import deepcopy
import requests,json,re

from urllib.parse import unquote

class JdSpider(scrapy.Spider):  #将scrapy.Spider修改为RedisSpider
    name = 'Jd'
    allowed_domains = ['jd.com','p.3.cn']
    start_urls = ['https://channel.jd.com/1315-1342.html']
    # redis_key = 'JD'

    def parse(self, response):
        item ={}
        #大分类
        All_sort = response.xpath('//div[@class="man-floor160531-01"]/div[@class="title"]/dl')
        # print(All_sort)
        for i in All_sort:
            li_list = i.xpath('./dd/ul/li')
            for li in li_list:
                sort_url = li.xpath('./a/@href').extract_first()   #获取分类的url
                item['sort_url'] = sort_url
                m = re.match('https:', str(item['sort_url']))  #有些sort_url在获得时就是一个完整的url，通过re匹配判断url是否完整
                if m is None:
                    item['sort_url'] = 'https:' + item['sort_url']
                sort_name = li.xpath('./a/text()').extract_first()  #获取分类的名称
                item['sort_name'] = sort_name.strip()
                # print(item['sort_url'], item['sort_name'])
                item['num'] = 0                                  #发送一个值，为网页翻页做准备
                yield scrapy.Request(
                    item['sort_url'],
                    callback=self.small_sort,
                    meta={'item':deepcopy(item)}                #防止信息被重写
                )





    def small_sort(self,response):
        item = response.meta['item']
        produce_list = response.xpath('//ul[@class="gl-warp clearfix"]/li')
        # print(produce_list)
        for produce in produce_list:
            # print(produce)
            item['id'] = produce.xpath('./@data-sku').extract_first()   #获得商品的id，为商品的评论做准备
            # print(item['id'])
            item['produce_img'] = 'https:' +  str(produce.xpath('./div/div[@class="p-img"]/a/img/@source-data-lazy-img').extract_first())  #获取图片url
            item['produce_desc'] = produce.xpath('./div/div[@class="p-img"]/a/@title').extract()      #获取商品的描述
            item['produce_href'] = produce.xpath('./div/div[@class="p-img"]/a/@href').extract_first()  #获取商品的url
            m = re.match('https:', str(item['produce_href']))                                           #与sort_url同理
            if m is None:
                item['produce_href'] = 'https:' + item['produce_href']
            money = produce.xpath('./div/div[@class="p-price"]/strong/i/text()').extract_first()        #获取商品价格
            if money is not None:     #当价格获取不到时，使用下面的url可以获得价格的信息
                if len(money) == 0:
                    aid = produce.xpath('./div/div[@class="p-price"]/strong/@class').extract_first()
                    money_s = requests.get('https://p.3.cn/prices/mgets?callback=jQuery4477881&skuIds=%s'%str(aid),headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36'})
                    money = re.compile('"p":"(.*?)"').findall(money_s.content.decode())[0]
            else:
                money = ''
            # money = money.xpath('string(.)')
            # print(money)
            shop = produce.xpath('./div/div[@class="p-shop"]/span/a/text()').extract_first()
            # print(item['produce_href'])
            item['money'] = money
            item['shop'] = shop
            yield scrapy.Request(
                item['produce_href'],
                callback=self.C_comment,
                meta={'item':deepcopy(item)}
            )


        #下一页
        # 通过观察猜测，下一页的规律：page为1,3,5...2*a+1,s(大概是商品的数量）大约在50~60的范围，我取最大值，keyword是不同于之前获取的商品名称
        #所以直接在url中获取。click.......
        keyword = re.compile('keyword=(.*?)&').findall(response.url)  #获取响应url中的keyword，构造下页的url
        # print(keyword)
        if len(keyword) > 0:
            keyword = unquote(keyword[0])
            b_str = str(keyword)+'&enc=utf-8&wq='+str(keyword)+'&page=%s&s=%s&click=0'
            next_url = 'https://search.jd.com/Search?keyword='+b_str
            item['num'] = item['num'] +1
            next_page = 2 * item['num'] + 1
            page_num = 60 * item['num']
            next_url = next_url % (next_page,page_num)
            # print(next_url)
            print(str(item['sort_name'])+'下一页为：'+str(item['num']))
            if item['num'] < 100:
                yield scrapy.Request(
                    next_url,
                    callback=self.small_sort,
                    meta={'item':item}
                )

    def C_comment(self,response):
        item = response.meta['item']
        if item['id'] is None:
            item['id'] = response.xpath('//div[@class="preview-info"]/div[@class="left-btns"]/a/@data-id').extract_first()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36',
            'Referer':str(response.url)}
        #在获取商品评论时，headers需要添加'Referer':response.url，才能得到网页数据，利用获取的id构造url
        comment_url = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv482&productId='+str(item['id'])+'&score=0&sortType=5&page=%s&pageSize=10&isShadowSku=0&fold=1'
        content_list = []
        for i in range(0,100):
            a = requests.get(comment_url%str(i),headers=headers)
            # print(str(item['produce_href']) +'---a的长度'+str(len(a.content)))
            data = a.content.decode('gbk')
            content = re.compile('"content":"(.*?)"').findall(data)
            # print(len(content))
            for i in content:
                lr = i.split('<',1)    #去除评论中的网页标签
                # print(lr)
                content_list.append(lr[0])
            if len(content) < 10:
                break
        if len(content_list) == 0:
            item['content'] = ''
        else:
            item['content'] = content_list
        # print(item)
        return item