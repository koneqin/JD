# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JdItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    sort_name = scrapy.Field()
    produce_img = scrapy.Field()
    produce_desc = scrapy.Field()
    produce_href = scrapy.Field()
    money = scrapy.Field()
    shop = scrapy.Field()
    content = scrapy.Field()