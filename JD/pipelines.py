# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class JdPipeline(object):
    def process_item(self, item, spider):
        # print('保存数据')
        with open('D:/SCRAPY_FILES/JD/JD/data.txt','a+',encoding='utf-8') as f:
            f.write(item['sort_name']+ ' '+item['produce_img']+' '+str(item['produce_desc'])+' '+item['produce_href'] +' '+item['money']+' '+item['shop']+' '+str(item['content'])+'\n')
        print('保存成功')
        return item
