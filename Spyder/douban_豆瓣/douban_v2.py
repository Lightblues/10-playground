from requests_html import HTMLSession
import math, random
import os, sys, time
import lxml.html
import re
import collections
import mysql.connector
from bs4 import BeautifulSoup
import pandas as pd

from easonsi import utils
# import requests

""" 重新写了一遍豆瓣的爬虫 @220429
策略: 分成三个 数据表: book_read, book_raw, book_full 
爬去列表: 从「已读」列表如 book_read
缓存: 将 response.content 进行缓存

TODO: 增加 process_ 函数, 数据处理
重构代码: 分离 book/movie, 整理爬取的框架, 分离出 process 函数
整理无法爬取的那些电影.

联合飞书API, 上传到多维表格
https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/bitable-overview
图片只支持写入到电子表格中
https://open.feishu.cn/document/ukTMukTMukTM/uUDNxYjL1QTM24SN0EjN
---

新增一个字段的方式: 1) 调整 schema; 2) 重新对于 movie_raw 进行一遍处理

---

另外意外将 「release_date」 设置成了 datetime, 发现对于「2002-11-21(中国大陆) / 2002-06-14(美国)」这样的也可以录入, 很强!
"""

config_mysql = {
    "host": "localhost",
    "user": "syc",
    "password": "syc",
    "database": "douban",
}

header_book = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br',       # 加了这个会乱码
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'bid=5nbQStAdqKM; douban-fav-remind=1; ll="108296"; push_doumail_num=0; _vwo_uuid_v2=D775FE93F785D5CD29364110218272B27|9a0bf487142a581f62e241373e0b3968; push_noty_num=0; gr_user_id=c7049df8-bc53-4469-a129-f280486b81f7; douban-profile-remind=1; __utmv=30149280.12670; __utmz=30149280.1611328390.12.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); dbcl2="126702461:amZjC0G0H5M"; ck=ta2j; __utmc=30149280; ap_v=0,6.0; __utma=30149280.1933035276.1607142021.1612330823.1612970541.20; __utma=81379588.1911313370.1606059854.1611762127.1612970819.9; __utmc=81379588; __utmz=81379588.1612970819.9.6.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/people/easonshi99/; _pk_ref.100001.3ac3=%5B%22%22%2C%22%22%2C1612970819%2C%22https%3A%2F%2Fwww.douban.com%2Fpeople%2Feasonshi99%2F%22%5D; ct=y; _pk_id.100001.3ac3=ef17657febe75693.1606059854.8.1612971936.1611762233.; __utmb=30149280.42.10.1612970541',
    # 'Host': 'book.douban.com',
    # 'Referer': 'https://book.douban.com/mine?status=collect',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/',
}

header_movie = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br',       # 加了这个会乱码
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': "movie.douban.com",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    'Cookie': 'douban-fav-remind=1; gr_user_id=c7049df8-bc53-4469-a129-f280486b81f7; _vwo_uuid_v2=D775FE93F785D5CD29364110218272B27|9a0bf487142a581f62e241373e0b3968; __utmv=30149280.12670; push_doumail_num=0; bid=AEOtnR48qXk; ll="108296"; push_noty_num=0; dbcl2="126702461:AdhaeCjqJrA"; ck=vQZZ; _ga=GA1.1.1933035276.1607142021; _ga_RXNMP372GL=GS1.1.1650643092.2.1.1650644449.47; __utmc=30149280; __utmc=223695111; __utmz=223695111.1651215025.122.81.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/search; ct=y; __utma=30149280.1933035276.1607142021.1651240611.1651243594.82; __utmz=30149280.1651243594.82.32.utmcsr=search.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/book/subject_search; __utmb=30149280.4.10.1651243594; _pk_ref.100001.4cf6=["","",1651246014,"https://www.douban.com/search?source=suggest&q=%E6%9C%BA%E5%8A%A8%E8%AD%A6%E5%AF%9F"]; _pk_ses.100001.4cf6=*; __utma=223695111.628753872.1605258511.1651224120.1651246015.124; __utmb=223695111.0.10.1651246015; ap_v=0,6.0; _pk_id.100001.4cf6=6326dc3696eab636.1605258511.123.1651247890.1651225730.',
}

class Douban(object):
    def __init__(self) -> None:
        self.init_mysql(config_mysql)
        self.init_session(header_book)
    
    def init_mysql(self, config):
        # self.conn = pymysql.connect(**config)
        self.conn = mysql.connector.connect(**config)
        
    def init_session(self, header):
        session = HTMLSession()
        session.headers.update(header)
        self.session = session

    def get_book_list(self, douban_id="easonshi99"):
        """ 从个人主页爬取书籍列表
        输出: book_read
            id, url, title, author, my_rate, my_rate_time, my_tags, my_comment, 
            考虑增加: user_id 多用户; t_update 更新时间
        处理重复主键: REPLACE
        """
        url_book = 'https://book.douban.com/people/{}/collect'.format(douban_id)        # https://book.douban.com/people/easonshi99/collect
        # 下面的链接其实只需要一个 start=15 的参数即可
        url_book_pattern = url_book + '?start={}&sort=time&rating=all&filter=all&mode=grid'  # 第二页则 start=15

        # 以下得到总的书籍数量
        r = self.session.get(url_book)
        _info = r.html.xpath('//*[@id="content"]/div[2]/div[1]/div[1]/div[2]/span')[0].text
        _, _, total_number = re.findall('[\d]+', _info)
        total_number = int(total_number)        # 书籍数量
        page_size = 15  # 默认一个的数量

        cursor = self.conn.cursor()
        # 分页请求，提取相关信息
        for page in range(math.ceil(total_number/page_size)):
            url = url_book_pattern.format(page*page_size) # 'https://book.douban.com/people/easonshi99/collect?start=0&sort=time&rating=all&filter=all&mode=grid'
            r = self.session.get(url)
            books = r.html.xpath('//li[@class="subject-item"]')
            print(f'Processing page {page+1}/{total_number}: {len(books)} books')
            for book in books:
                title_info = book.xpath('//h2/a')[0]
                url = title_info.attrs['href']
                id = url.strip('/').split('/')[-1]
                title = title_info.text
                author = book.xpath('//div[@class="pub"]/text()')[0].strip()
                
                short_note = book.xpath('//div[@class="short-note"]')[0]
                # rate: 是 short_note 下面的 span 中的第一个所决定的, 例如 <span class="rating5-t"> 就是五星
                my_rate_span = short_note.xpath('//span')[0]
                my_rate_class = my_rate_span.attrs['class'][0]
                my_rate = int(re.findall('\d', my_rate_class)[0]) if "rating" in my_rate_class else 0
                # 其他的 span
                my_rate_time = short_note.xpath('//span[@class="date"]')[0].text.strip()
                my_tags = short_note.xpath('//span[@class="tags"]')
                my_tags = my_tags[0].text.strip() if len(my_tags) > 0 else ''
                my_comment = short_note.xpath('//span[@class="comment"]')
                my_comment = my_comment[0].text.strip() if len(my_comment) > 0 else ''
                query = "REPLACE INTO book_read (id, url, title, author, my_rate, my_rate_time, my_tags, my_comment) " \
                    "VALUES(%s, %s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(query, (id, url, title, author, my_rate, my_rate_time, my_tags, my_comment))
                self.conn.commit()
        cursor.close()

    def get_book_all(self):
        """ 从 book_read 表爬取所有书籍信息
        输入: 
        输出: 
        """
        query = "SELECT id, url, title, author, my_rate, my_rate_time, my_tags, my_comment FROM book_read;"
        cursor = self.conn.cursor()
        cursor.execute(query)
        books_read = cursor.fetchall()
        cursor.close()
        
        total = len(books_read)
        for i,d_book_read in enumerate(books_read):
            # id, url, title, author, my_rate, my_rate_time, my_tags, my_comment
            if self.check_book_is_in_db(d_book_read[0], version=1, my_rate_time=d_book_read[5]):
                continue
            
            # id, url, title, cover_link, info_text, rating_text, content
            is_cached, d_book_raw = self.get_book(d_book_read[0]) # is_cached 记录是否已经缓存, 若未缓存, 说明发起了请求
            if not is_cached:
                t = random.randint(1, 5)
                print(f'[sleep] {t}s')
                time.sleep(t)
            self.process_book(d_book_read, d_book_raw)
            print(f'[done] {i+1}/{total}: book {d_book_read[0], d_book_read[2]}')

    def get_book(self, book_id):
        """ 爬取书籍, 保存原始信息
        输入: 书籍id
        输出: 保存到 book_raw 表
        数据格式: is_cached, (id, url, title, cover_link, info_text, rating_text, content)
            其中 is_cached 标记是否已经缓存, 若未缓存, 说明发起了请求
        """
        query = "SELECT id, url, title, cover_link, info_text, rating_text, content FROM book_raw WHERE id=%s"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query, (book_id,))
        if cursor.rowcount > 0:
            print(f'{book_id} is cached')
            return True, (cursor.fetchone())
        cursor.close()
        
        url = f'https://book.douban.com/subject/{book_id}/'
        response = self.session.get(url)
        html = response.html
        # 直接用 find 也OK
        # title = resonse.html.find('h1', first=True).text
        # 标题
        title = html.xpath('//*[@id="wrapper"]/h1/span')[0].text
        # 封面图
        cover_link = html.xpath('//*[@id="mainpic"]/a/img/@src')[0]

        # 书籍信息
        info_text = html.xpath('//*[@id="info"]')[0].text
        rating_text = html.xpath('//*[@id="interest_sectl"]/div/div[2]')[0].text
        # 无法保存结构信息
        # related_info_text = html.xpath('//*[@id="content"]/div/div[1]/div[3]')[0].text
        content = response.content.decode()
        
        cursor = self.conn.cursor(buffered=True)
        query_insert_bookraw = "INSERT INTO book_raw (id, url, title, cover_link, info_text, rating_text, content) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query_insert_bookraw, (book_id, url, title, cover_link, info_text, rating_text, content,))
        self.conn.commit()
        cursor.close()
        print(f"[request] {book_id} {title}")
        return False, (book_id, url, title, cover_link, info_text, rating_text, content)
    
    def process_book(self, d_book_read, d_book_raw, version=1):
        """ 处理原始数据, 入库
        输出: book_full
        输出结构:
            id, url, title, 
            rate, rate_num, 
            my_rate, my_tags, my_rate_time, my_comment, 
            author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, 
            info_content, info_author, # info_series, 
            version,
            其中, 值为数字的: id, rate_num 为整数, rate, my_rate 为浮点数
        重复主键处理: 若version不同则更新, 否则不更新
        """
        
        id, url, title, cover_link, info_text, rating_text, content = d_book_raw
        id, url, title, author, my_rate, my_rate_time, my_tags, my_comment = d_book_read
        
        if self.check_book_is_in_db(id, version, my_rate_time):
            return 1
        
        # id, url, title, cover_link, 
        author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn = self.process_book_info_text(info_text)
        rate, rate_num = self.process_rating_text(rating_text)
        info_content, info_author = self.process_book_related_info_with_content(content)
        
        cursor = self.conn.cursor(buffered=True)
        query_insert_book = "INSERT IGNORE INTO book_full (id, url, title, cover_link, my_rate, my_rate_time, my_tags, my_comment, "\
            "author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, " \
                "rate, rate_num, info_content, info_author, version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, " \
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," \
                        "%s, %s, %s, %s, %s)"
        cursor.execute(query_insert_book, (
            id, url, title, cover_link, my_rate, my_rate_time, my_tags, my_comment, 
            author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, 
            rate, rate_num, info_content, info_author, version,
        ))
        self.conn.commit()
        cursor.close()
        return 0
        
    def check_book_is_in_db(self, id, version=1, my_rate_time=None):
        """ 检查书籍是否已经存在 """
        cursor = self.conn.cursor(buffered=True)
        query = "SELECT id, url, title, my_rate, my_tags, my_rate_time, my_comment, author, version FROM book_full WHERE id=%s"
        cursor.execute(query, (id,))
        if not cursor.rowcount > 0: return False
        old_id, old_url, old_title, old_my_rate, old_my_tags, old_my_rate_time, old_my_comment, old_author, old_version = cursor.fetchone()
        # 不更新的条件: 
        if version!=old_version: return False
        if my_rate_time: 
            return my_rate_time==old_my_rate_time
        return True
    
    @staticmethod
    def process_book_info_text(info_text):
        """ 处理豆瓣的基础信息表, 方便起见输出均为 str
        输入: 原始的文本, 例如: '作者: 张成思\n出版社: 中国人民大学出版社\n出版年: 2016-3-1\n页数: 309\n定价: CNY 80.00\n装帧: 精装\nISBN: 9787300226040'
        输出格式: author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, 
        """
        infos = []
        for i in info_text.split('\n'):
            try: 
                e = i.split(":", 1)
                infos.append([j.strip() for j in e])
            except Exception as e:
                print(e)
                continue
        res = {}
        for name, value in infos:
            if name not in map_book_info_ch2key:
                print(f"[warning] 未知的信息: {name}")
                continue
            key = map_book_info_ch2key[name]
            res[key] = value
        r = []
        for key in map_book_info_key2ch:
            r.append(res.get(key, ''))
        return r
    
    @staticmethod
    def process_rating_text(rating_text):
        """ 
        '9.5\n49人评价'
        '暂无评分'
        """
        rates = rating_text.split('\n')
        if len(rates) == 2:
            rate = float(re.findall(r"[\d\.]+", rates[0])[0])
            rate_num = int(re.findall(r"\d+", rates[1])[0])
            return rate, rate_num
        return .0, 0
    
    @staticmethod
    def process_book_related_info_with_content(content):
        """ 
        输入: raw_content
        输出: 
        """
        soup = BeautifulSoup(content, 'html.parser')
        intros = soup.find_all(class_="intro")
        
        info_content, info_author = "", ""
        if len(intros) >= 3:
            info_content, info_author =  intros[1].text.strip(), intros[2].text.strip()
        elif len(intros) == 2:
            info_content, info_author =  intros[0].text.strip(), intros[1].text.strip()
        elif len(intros) == 1:
            info_content = intros[0].text.strip()
        elif len(intros) == 0:
            pass
        else:
            return ["", ""]
        return info_content, info_author


    def get_movie_list(self, user_id="easonshi99"):
        """ 从个人主页爬取列表
        输出: movie_watched
            movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment
        处理重复主键: REPLACE
        """
        url_book = 'https://movie.douban.com/people/{}/collect'.format(user_id)        # https://book.douban.com/people/easonshi99/collect
        # 下面的链接其实只需要一个 start=15 的参数即可
        url_book_pattern = url_book + '?start={}&sort=time&rating=all&filter=all&mode=grid'  # 第二页则 start=15

        # 以下得到总的书籍数量
        r = self.session.get(url_book)
        # 1-15 / 403
        _info = r.html.xpath('//*[@class="subject-num"]/text()')[0]
        _, _, total_number = re.findall('[\d]+', _info)
        total_number = int(total_number)        # 书籍数量
        page_size = 15  # 默认一个的数量

        cursor = self.conn.cursor()
        # 分页请求，提取相关信息
        total = math.ceil(total_number/page_size)
        for page in range(total):
            url = url_book_pattern.format(page*page_size) # 'https://book.douban.com/people/easonshi99/collect?start=0&sort=time&rating=all&filter=all&mode=grid'
            r = self.session.get(url)
            items = r.html.xpath('//div[@class="item"]') 
            print(f'Processing page {page+1}/{total}: {len(items)} movies')
            for item in items:
                title_info = item.xpath('//li[@class="title"]')[0]
                url = title_info.xpath('//a')[0].attrs['href']
                movie_id = url.strip('/').split('/')[-1]
                title = title_info.text.split("/", 1)[0].strip()
                
                intro = item.xpath('//li[@class="intro"]/text()')[0].strip()
                
                my_rate_span = item.xpath('//span[@class="date"]/..')[0]
                my_rate = 0
                my_rate_class = my_rate_span.xpath('//span')[0].attrs['class'][0]
                if my_rate_class.startswith('rating'):
                    my_rate = int(re.findall('\d', my_rate_class)[0])
                date_span = item.xpath('//span[@class="date"]')[0]
                my_rate_time = date_span.text.strip()
                
                my_comment = item.xpath('//span[@class="comment"]')
                my_comment = my_comment[0].text.strip() if len(my_comment) > 0 else ''
                
                query = "REPLACE INTO movie_watched (movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment) " \
                    "VALUES(%s, %s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(query, (movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment))
                self.conn.commit()
        cursor.close()

    def get_movie_all(self):
        """ 从 movie_watched 表爬取所有书籍信息
        输入: movie_watched 所包括的电影 (movie_id)
        中间结果: 调用 self.get_movie(movie_id) 将原始文本保存在 movie_raw
        输出: movie_full 记录所有电影的信息
            通过调用 process_movie(self, d_movie_watched, d_movie_raw, version=1) 得到完整的电影信息
        """
        query = "SELECT movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment FROM movie_watched;"
        cursor = self.conn.cursor()
        cursor.execute(query)
        movies = cursor.fetchall()
        cursor.close()
        
        total = len(movies)
        for i,d_movie_watched in enumerate(movies):
            # movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment
            if self.check_movie_is_in_db(d_movie_watched[0], version=1, my_rate_time=d_movie_watched[6]):
                continue
            
            # movie_id, url, title, year, cover_link, info_text, rating_text, content
            try: # 例如 安东尼奥尼的中国 https://movie.douban.com/subject/1292327/
                is_cached, d_movie_raw = self.get_movie(d_movie_watched[0]) # is_cached 记录是否已经缓存, 若未缓存, 说明发起了请求
            except Exception as e:
                print(f"[error] {d_movie_raw[:3]}")
                print(e)
                continue
            if not is_cached:
                t = random.randint(1, 5)
                print(f'[sleep] {t}s')
                time.sleep(t)
            self.process_movie(d_movie_watched, d_movie_raw)
            print(f'[done] {i+1}/{total}: mvoies {d_movie_watched[0], d_movie_watched[3]}')

    def check_movie_is_in_db(self, movie_id, version=1, my_rate_time=None):
        """ 检查书籍是否已经存在
        """
        cursor = self.conn.cursor(buffered=True)
        query = "SELECT movie_id, my_rate_time, version FROM movie_full WHERE movie_id=%s"
        cursor.execute(query, (movie_id,))
        if not cursor.rowcount > 0: return False
        old_movie_id, old_my_rate_time, old_version = cursor.fetchone()
        # 不更新的条件: 
        if version!=old_version: return False
        if my_rate_time: 
            return my_rate_time==old_my_rate_time
        return True


    def get_movie(self, movie_id):
        """ 爬取书籍, 保存原始信息
        输入: movie_id
        输出: 保存到 movie_raw 表
        数据格式: is_cached, (movie_id, url, title, year, cover_link, info_text, rating_text, content)
            其中 is_cached 标记是否已经缓存, 若未缓存, 说明发起了请求
        """
        query = "SELECT movie_id, url, title, year, cover_link, info_text, rating_text, content FROM movie_raw WHERE movie_id=%s"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query, (movie_id,))
        # if cursor.fetchone():
        if cursor.rowcount > 0:
            print(f'{movie_id} is cached')
            return True, (cursor.fetchone())
        cursor.close()
        
        url = f'https://movie.douban.com/subject/{movie_id}/'
        response = self.session.get(url)
        html = response.html
        
        
        # 标题
        title_span_text = html.xpath('//*[@id="content"]/h1')[0].text
        title_span_text = title_span_text.replace(")", "").strip()
        title, year = title_span_text.split("(")
        title = title.strip()
        
        # 封面图 
        cover_link = html.xpath('//*[@id="mainpic"]/a/img/@src')[0]

        # 信息
        info_text = html.xpath('//*[@id="info"]')[0].text # '导演: 道格·里曼\n编剧: 
        rating_text = html.xpath('//*[@id="interest_sectl"]/div[1]/div[2]')[0].text # '8.6\n385686人评价'
        content = response.content.decode()
        
        cursor = self.conn.cursor(buffered=True)
        query_insert_movie_raw = "INSERT INTO movie_raw (movie_id, url, title, year, cover_link, info_text, rating_text, content) VALUES " \
            "(%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query_insert_movie_raw, (movie_id, url, title, year, cover_link, info_text, rating_text, content,))
        self.conn.commit()
        cursor.close()
        print(f"[request] {movie_id} {title}")
        return False, (movie_id, url, title, year, cover_link, info_text, rating_text, content)
    
    def process_movie(self, d_movie_watched, d_movie_raw, version=1):
        """ 处理原始数据, 入库
        输入: d_movie_watched 为个人已看页面信息, d_movie_raw 为详情页的原始信息
        输出: movie_full
        输出结构:
            movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment, 
            director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website, 
            rate, rate_num, link_report, version
            其中, 值为数字的: movie_id, rate_num 为整数, rate, my_rate 为浮点数
        重复主键处理: 若version不同则更新, 否则不更新
        """
        
        movie_id, url, title, year, cover_link, info_text, rating_text, content = d_movie_raw
        movie_id, user_id, url, _, intro, my_rate, my_rate_time, my_comment = d_movie_watched
        
        if self.check_movie_is_in_db(movie_id, version, my_rate_time):
            return 1
        

        director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website = self.process_movie_info_text(info_text)
        rate, rate_num = self.process_rating_text(rating_text)
        link_report = self.process_link_report_with_content(content)
        
        cursor = self.conn.cursor(buffered=True)
        query_insert_movie = "INSERT IGNORE INTO movie_full (movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment, "\
            "director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website, " \
                "rate, rate_num, link_report, version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, " \
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s," \
                        "%s, %s, %s, %s)"
        cursor.execute(query_insert_movie, (
            movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment, 
            director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website, 
            rate, rate_num, link_report, version
        ))
        self.conn.commit()
        cursor.close()
        return 0
    
    @staticmethod
    def process_link_report_with_content(content):
        # html = lxml.html.fromstring(content)
        # return html.xpath('//div[id="link-report"')[0].text_content()
        soup = BeautifulSoup(content, 'html.parser')
        return soup.find_all(id="link-report")[0].text.strip()
    
    @staticmethod
    def process_movie_info_text(info_text):
        """ 处理豆瓣的基础信息表, 方便起见输出均为 str
        输入: 原始的文本, 例如: "导演: 道格·里曼\n编剧: "
        输出格式: director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website
        """
        infos = []
        for i in info_text.split('\n'):
            try: 
                key, value = i.split(":", 1)
                infos.append((key.strip(), value.strip()))
            except Exception as e:
                print(f"i: {i}")
                print(e)
                continue
        res = {}
        for name, value in infos:
            if name not in map_movie_info_ch2key:
                print(f"[warning] 未知的信息: {name}")
                continue
            key = map_movie_info_ch2key[name]
            res[key] = value
        r = []
        for key in map_movie_info_key2ch:
            r.append(res.get(key, ''))
        return r

    def to_feishu_csv_movie(self, ofn):
        """ 
        输出列
        movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment, rate, rate_num, 
        link_report, 
        director, scriptwriter, actors, types, alias, 
        release_date, duration, 
        """
        cursor = self.conn.cursor(buffered=True)
        query = "SELECT title, year, link_report, my_rate, my_rate_time, my_comment, url, rate, rate_num, director, scriptwriter, actors, types, release_date, duration, alias movie_id, cover_link FROM movie_full;"
        cursor.execute(query)
        movies = cursor.fetchall()
        
        # for title, year, link_report, my_rate, my_rate_time, my_comment, url, rate, rate_num, director, scriptwriter, actors, types, release_date, duration, alias movie_id, cover_link in movies:
        result = pd.DataFrame(movies, columns="title, year, link_report, my_rate, my_rate_time, my_comment, url, rate, rate_num,  director, scriptwriter, actors, types, release_date, duration, alias movie_id, cover_link".split(", "))
        
        # 将分隔符转为 `,`
        for col in "director, scriptwriter, actors, types, alias".split(', '):
            result[col] = result[col].apply(self.process_split_parts)
        # 简介去除多余的空格
        result["link_report"] = result["link_report"].apply(self.process_link_report)
        # 将 star 转为符号类型
        result['my_rate'] = result['my_rate'].apply(self.process_my_rate_to_stars)
        result.to_csv(ofn, index=False)
    
    @staticmethod
    def process_split_parts(s:str, sep='/', new_sep=','):
        """ 将「姜文 / 史建全 / 述平 / 尤凤伟」这种形式分割的转为「,」分割 """
        parts = s.split(sep)
        return new_sep.join(i.strip() for i in parts)

    @staticmethod
    def process_link_report(link_report:str):
        """ 简介文本「第一段　　第二段」, 去除段首空格 """
        lines = link_report.split('\n')
        return '\n'.join([l.strip() for l in lines if l.strip()])
    
    @staticmethod
    def process_my_rate_to_stars(my_rate:str, star="⭐️"):
        """ 将 "3" 转为 "⭐️⭐️⭐️" """
        if star in my_rate: return star
        if star not in "012345": return ""
        rate = int(my_rate)
        return star*rate

    def update_movie_full_single_col(self, col_input: str, col_update:str, f):
        """ 基于所定义的处理函数 f, 用表的若干 col_input 列更新表的 col_update 列
        参数: 
            f: 处理函数, 输入为 columnns 所定义的列, 输出为要更新的列的值
            columnns: f 的输入参数, 例如 `"author, subtitle, publisher"` 筛选三个列, 这三个就作为 f输入参数
            col_update: 进行更新的列名
        注意在 SELECT 时自动加上了 movie_id 列, 从而进行对应的 UPDATE
        
        TODO: update_movie_full_multiple_col 支持更新多个列
        """
        query_select = f"SELECT movie_id, {col_input} FROM movie_full;"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query_select)
        rows = cursor.fetchall()
        cursor.close()
        
        query_update = f"UPDATE movie_full SET {col_update} = %s WHERE movie_id = %s;"
        cursor = self.conn.cursor(buffered=True)
        for row in rows:
            movie_id, *rest = row
            r = f(*rest)
            cursor.execute(query_update, (r, movie_id))
            self.conn.commit()
        cursor.close()
        return 
    
    def select_multiple_from_db(self, table_name:str, columns:str, where:str, params:tuple):
        """ 查询数据库
        参数: params 用于放一些辅助信息. 例如 `self.select_one_from_db("book_raw", "*", "book_id = %s AND version = %s", (book_id, version))`
        返回: 查询失败则返回 None
        """
        query = f"SELECT {columns} FROM {table_name} WHERE {where};"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            return None
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    def select_one_from_db(self, table_name:str, columns:str, where:str, params:tuple):
        """ 查询数据库
        返回: 失败则返回 None
        """
        query = f"SELECT {columns} FROM {table_name} WHERE {where};"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            return None
        row = cursor.fetchone()
        cursor.close()
        return row
    
    def crawl_book_content_from_list(self, book_id_list: list, source_tag="None", version=1):
        """ 从书籍列表中抓取书籍内容 """
        count_crawel = 0
        for i, book_id in enumerate(book_id_list):
            db_res = self.select_one_from_db("book_raw", "*", "book_id = %s AND version = %s", (book_id, version))
            if db_res: continue
            print(f"[info] crawling {i+1}/{len(book_id_list)}")
            self.crawl_book_by_id(book_id, source_tag, version)
            count_crawel += 1
            t = random.randint(1, 3)
            print(f"[sleep] {t}s")
            time.sleep(t)
        return


    def crawl_book_by_id(self, book_id, source_tag="None", version=1):
        """ 爬取书籍, 保存原始信息
        输入: 书籍id
        输出: 保存到 book_raw 表
        数据格式: book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version
        """
        url = f'https://book.douban.com/subject/{book_id}/'
        response = self.session.get(url)
        html = response.html
        # 直接用 find 也OK
        # title = resonse.html.find('h1', first=True).text
        # 标题
        title = html.xpath('//*[@id="wrapper"]/h1/span')[0].text
        # 封面图
        cover_link = html.xpath('//*[@id="mainpic"]/a/img/@src')[0]

        # 书籍信息
        info_text = html.xpath('//*[@id="info"]')[0].text
        rating_text = html.xpath('//*[@id="interest_sectl"]/div/div[2]')[0].text
        # 无法保存结构信息
        # related_info_text = html.xpath('//*[@id="content"]/div/div[1]/div[3]')[0].text
        content = response.content.decode()
        
        cursor = self.conn.cursor(buffered=True)
        query_insert_bookraw = "INSERT INTO book_raw (book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version) "\
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query_insert_bookraw, (book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version))
        self.conn.commit()
        cursor.close()
        print(f"[crawled] {book_id} {title}")
        return book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version
    
    def check_exists(self, table_name, query):
        """ 检查是否存在
        示例: self.check_exists("book_list", f"version=1 AND book_id={book_id}")
        """
        cursor = self.conn.cursor(buffered=True)
        query = f"SELECT * FROM {table_name} WHERE {query};"
        cursor.execute(query, ())
        if not cursor.rowcount > 0: return False
        return True
    
    def process_book_content(self, filter, version=1):
        """ 处理 raw 网页文本, 提取信息入库
        参数: filter 进行筛选 (例如进处理 version=1 的原始数据)
        输入: book_raw 表的原始文本, 包括: book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version
        输出: 整合进 book_list 表
            重复key处理: REPLACE
        """
        rows = self.select_multiple_from_db("book_raw", "book_id, url, title, cover_link, info_text, rating_text, content, source_tag, version", filter, ())
        
        query_insert_book = "REPLACE INTO book_list (book_id, url, title, cover_link, "\
            "author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, " \
                "rate, rate_num, info_content, info_author, version, source_tag) VALUES (%s, %s, %s, %s, " \
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," \
                        "%s, %s, %s, %s, %s, %s); "
        cursor = self.conn.cursor(buffered=True)
        for book_id, url, title, cover_link, info_text, rating_text, content, source_tag, _version in rows:
            if self.check_exists("book_list", f"version={version} AND book_id={book_id}"):
                continue
            author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn = self.process_book_info_text(info_text)
            rate, rate_num = self.process_rating_text(rating_text)
            info_content, info_author = self.process_book_related_info_with_content(content)
        
            cursor.execute(query_insert_book, (
                book_id, url, title, cover_link, 
                author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn, 
                rate, rate_num, info_content, info_author, version, source_tag, 
            ))
            self.conn.commit()
        cursor.close()
        return 0

map_book_info_ch2key = dict(zip(
    # 统一书号 
    "作者 副标题 出版社 出品方 原作名 译者 出版年 页数 定价 装帧 丛书 ISBN".split(),
    "author, subtitle, publisher, producer, origin_title, translator, publish_year, pages, price, binding, series, isbn".split(", ")
))
map_book_info_key2ch = {v: k for k, v in map_book_info_ch2key.items()}

map_movie_info_ch2key = dict(zip(
    # 
    "导演 编剧 主演 类型 官方网站 制片国家/地区 语言 上映日期 片长 又名 IMDb 首播 季数 集数 单集片长 官方小站".split(),
    "director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website".split(", ")
))
map_movie_info_key2ch = {v: k for k, v in map_movie_info_ch2key.items()}

douban_crawler = Douban()
# douban_crawler.get_book_list()
# douban_crawler.get_book_all()

# douban_crawler.get_movie_list()
# douban_crawler.get_movie(1304102)
# douban_crawler.get_movie_all()

def to_csv():
    douban_crawler.to_feishu_csv_movie("data/douban_movie.csv")

""" 更新某一列 """
# douban_crawler.update_movie_full_single_col("link_report", "link_report", douban_crawler.process_link_report)

def crawl_tag_list():
    # "历史 心理学 哲学 社会学 传记 文化 艺术 社会 政治"
    book_tag_list = pd.read_csv('./data/book/tag_book_list.csv', header=0)
    for tag in book_tag_list['book_tag'].unique():
        book_ids = book_tag_list[book_tag_list['book_tag']==tag]['book_id']
        print(f"=== crawling {tag} [{len(book_ids)}] ===")
        douban_crawler.crawl_book_content_from_list(book_ids, source_tag=tag, version=1)

def process_book():
    douban_crawler.process_book_content(filter="version=1", version=1)