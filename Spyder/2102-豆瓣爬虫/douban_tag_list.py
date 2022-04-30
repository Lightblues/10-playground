from requests_html import HTMLSession
import math, random
import os, sys, time
import lxml.html
import re
import collections
import urllib.parse, urllib.request
# import mysql.connector
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

from config import header_douban

class DoubanTagList(object):
    def __init__(self) -> None:
        self.init_session(header_douban)
        
    def init_session(self, header):
        session = HTMLSession()
        session.headers.update(header)
        self.session = session
        
    def crawel_tag_list(self, book_tag:str, page_start=0, page_end=10, books_per_page=20):
        """ 爬取 book_tag 的 start-end 列表
        输出: book_id, title, desc, book_url 列表"""
        url_book_tag = "https://book.douban.com/tag/{}?start={}"
        #url='http://www.douban.com/tag/%E5%B0%8F%E8%AF%B4/book?start=0' # 小说 转义
        
        book_list = []
        for page_num in range(page_start, page_end):
            url = url_book_tag.format(urllib.parse.quote(book_tag), page_num*books_per_page)
            # time.sleep(np.random.rand()*5)

            r = self.session.get(url)
            print(f"[info] code {r.status_code}; url {url}")
            content = r.html.html # == r.content.decode()

            # soup = BeautifulSoup(content, 'lxml')
            soup = BeautifulSoup(content, 'html.parser')
            list_soup = soup.find('ul', {'class': 'subject-list'})
            
            
            for book_info in list_soup.findAll(class_="info"):
                title_a = book_info.find('a')
                title = title_a.text.strip()
                book_url = title_a.get('href')
                # https://book.douban.com/subject/4913064/
                book_id = book_url.split('/')[-2]

                infos = book_info.find('div', {'class':'pub'}).string.strip()
                desc = book_info.find('p') # 其实就是书籍简介
                desc = desc.text.strip() if desc else ''
                book_list.append([book_tag, title, book_id, infos, desc, book_url])
        return book_list
    
    

douban = DoubanTagList()
# https://book.douban.com/tag/

""" 爬取多个 tag 的书籍列表, 方便起见没有 sleep, 居然没被封 IP """
tags = "历史 心理学 哲学 社会学 传记 文化 艺术 社会 政治"
# 建筑 回忆录 国学 西方哲学 

book_all = []
for tag in tags.split():
    book_list = douban.crawel_tag_list(tag, 0, 10)
    book_all.extend(book_list)
pd.DataFrame(book_all, columns="book_tag, title, book_id, infos, desc, book_url".split(', ')).to_csv(f'./data/book/tag_book_list.csv', index=False)