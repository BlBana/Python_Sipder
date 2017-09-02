# -*- coding: utf-8 -*-
import scrapy
import urlparse
import re
import datetime
from scrapy.http import Request
from Spider.items import JobBoleArticleItem
from Spider.utils.common import get_md5

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts']

    def parse(self, response):
        """
        1.获取列表页中url的地址解析出来，scrapy下载文章内容，并分析
        2.获取下一页的url并交给scarpy下载，下载完成后交给parse函数
        :param response:
        :return:
        """
        # 解析文章列表页中所有的url交给scrapy下载后进行解析
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for post_node in post_nodes:
            image_url = post_node.css('img::attr(src)').extract_first("")
            image_url = urlparse.urljoin(response.url, image_url)
            post_url = post_node.css('::attr(href)').extract_first("")
            yield Request(url=urlparse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)  # 4

        # 提取下一页进入下载
        next_urls = response.css('.next.page-numbers::attr(href)').extract_first()  # 2
        if next_urls:
            yield Request(url=urlparse.urljoin(response.url, next_urls), callback=self.parse)

    @staticmethod
    def parse_detail(response):
        article_item = JobBoleArticleItem()
        # 提取文章的具体字段
        front_image_url = response.meta.get('front_image_url', '')
        match = re.match(r'http:\/\/.*\/(\d+)\/', response.url)  # 文章ID
        title = response.css('.entry-header h1::text').extract_first()  # 文章标题
        create_time = response.css('p.entry-meta-hide-on-mobile::text').extract()[0].strip()[:11]  # 文章发布时间
        praise_nums = response.css('span.vote-post-up h10::text').extract_first()  # 点赞数
        fav_nums = response.css('.bookmark-btn::text').extract_first().strip()  # 收藏数
        match_re = re.match(r'.*?(\d+).*', fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0
        comment_nums = response.css('a[href="#article-comment"] span::text').extract_first()
        content = response.css('.entry').extract_first()  # 文章内容
        match_re = re.match(r'.*?(\d+).*', comment_nums)
        if match_re:
            comment_nums = int(match.group(1))
        else:
            comment_nums = 0
        tag_list = response.css('.entry-meta-hide-on-mobile a::text').extract()  # 文章标签
        tag_list = [element for element in tag_list if not element.strip().encode('utf8').endswith('评论')]
        tags = ','.join(tag_list)

        article_item['url_object_id'] = get_md5(response.url)
        article_item['title'] = title
        article_item['url'] = response.url
        try:
            create_time = datetime.datetime.strptime(create_time, "%Y/%m/%d").date()
        except Exception as e:
            create_time = datetime.datetime.now().date()
        article_item['create_date'] = create_time
        article_item['front_image_url'] = [front_image_url]
        article_item['praise_nums'] = praise_nums
        article_item['comment_nums'] = comment_nums
        article_item['fav_nums'] = fav_nums
        article_item['tags'] = tags
        article_item['content'] = content
        yield article_item
