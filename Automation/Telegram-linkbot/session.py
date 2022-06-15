from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from pymongo import MongoClient
from pymongo.collection import Collection

import arxiv

import logging
from datetime import datetime
from config import config_mongo, header_base
from collections import OrderedDict


""" 处理 links
# 小宇宙
https://www.xiaoyuzhoufm.com/episode/62a3739bb32f552f54730f2a
# arXiv

https://arxiv.org/abs/2206.04673
# GitHub
API: https://docs.github.com/en/rest/repos/repos#get-a-repository
https://github.com/Vincentqyw/cv-arxiv-daily
"""

class Session(object):
    def __init__(self) -> None:
        """ 初始化数据库和 session """
        self.init_session(header_base)
        self.db = MongoClient(**config_mongo).links
        
    def init_session(self, header):
        session = HTMLSession()
        session.headers.update(header)
        self.session: HTMLSession = session
    
    def get_latest(self, n:int):
        """ 返回最近添加的 n 条记录 """
        try:
            links = self.db.htmls.find({}, ['url', 't_update']).sort("t_update", -1).limit(n)
            message = "\n".join([f"{i['url']} {i['t_update']}" for i in links])
            logging.info(f"\tReturned latest {n} links")
            return 0, message
        except Exception as e:
            logging.error(f"\terror: {e}")
            return -1, e
        
    def resolve_url(self, url, taskname='resolve_url'):
        """ 处理链接的入口函数 """
        # 去除 params
        url = urljoin(url, urlparse(url).path)
        
        # 在上层函数中处理错误, 下面不再处理
        try:
            code, d = self.get_html(url)
            
            # https://www.xiaoyuzhoufm.com/episode/62a3739bb32f552f54730f2a
            if "xiaoyuzhou.com" in url: code, info = self.process_xiaoyuzhou_episode(url, d['content'])
            # https://arxiv.org/abs/2206.04673
            if "arxiv.org" in url: code, info = self.process_arxiv(url)
            # https://github.com/Vincentqyw/cv-arxiv-daily
            if "github.com" in url: code, info = self.process_github(url)
            return code, info
        except Exception as e:
            logging.error(f"\terror: {e}")
            return -1, e
        
        
    def get_html(self, url, taskname='get_html'):
        """ 获取html """
        c: Collection = self.db.htmls
        d = c.find_one({"url": url})
        if d is not None:
            logging.info(f"\thit {url}")
            return 1,d
        # 错误处理统一放在上层函数
        r = self.session.get(url)
        content = r.content.decode('utf-8')
        d = {
            "url": url,
            "content": content,
            "t_update": datetime.now()
        }
        c.insert_one(d)
        logging.info(f"\tcrawelled {url}")
        return 0, d
        
    
    def process_xiaoyuzhou_episode(self, url, content):
        """ 获取单条episode信息 """
        episode_id = urlparse(url).path.split('/')[-1]
        collection: Collection = self.db.xiaoyuzhou_episode_info
        d = collection.find_one({"episode_id": episode_id})
        if d is not None:
            logging.info(f"\tepisode_id {episode_id} already in db")
            return 1,  {k:v for k,v in d.items() if k in ['episode_title', 'podcast_title']}
        
        soup = BeautifulSoup(content, 'html.parser')
        episode_title = soup.find('h1').text
        podcast_tag = soup.find(class_='podcast-title')
        podcast_title = podcast_tag.find('a').text
        podcast_id = podcast_tag.find('a').get('href').split('/')[-1]
        audio_url = soup.find("meta", property="og:audio").get('content')
        d = {
            "episode_title": episode_title,
            "podcast_title": podcast_title,
            "episode_id": episode_id,
            "podcast_id": podcast_id,
            "url": url,
            "audio_url": audio_url,
            "t_update": datetime.now()
        }
        collection.insert_one(d)
        logging.info(f"\tepisode_id {episode_id} inserted")
        # code, return_info
        return 0, {k:v for k,v in d.items() if k in ['episode_title', 'podcast_title']}


    def process_douban(self, ):
        pass
    
    def process_arxiv(self, url):
        aid = urlparse(url).path.split('/')[-1]
        return_fields = "title code_url summary".split()

        collection: Collection = self.db.arxiv_paper_info
        d = collection.find_one({"url": url})
        if d is not None:
            logging.info("\tarxiv paper {aid} already in db")
            return 1, {k:v for k,v in d.items() if k in return_fields}

        r = arxiv.Search(id_list=[aid]).results()
        paper = next(r)
        fields = "entry_id pdf_url title summary comment primary_category categories doi journal_ref updated published".split()
        d = {k:getattr(paper, k) for k in fields}
        d['first_author'] = paper.authors[0].name
        d['authors'] = [a.name for a in paper.authors]
        d['links'] = [l.href for l in paper.links]
        d['t_update'] = datetime.now()
        d['code_url'] = self.process_paperwithcode(aid)
        
        arxiv_key_order = "title first_author summary comment entry_id pdf_url code_url updated published primary_category categories doi journal_ref authors links t_update".split()
        # {k:v for k,v in d.items() if k in arxiv_key_order}
        ordered = OrderedDict()
        for key in arxiv_key_order:
            ordered[key] = d[key]
        collection.insert_one(ordered)
        logging.info(f"\tarxiv paper {aid} inserted")
        return 0, {k:v for k,v in ordered.items() if k in return_fields}
        
    def process_paperwithcode(self, aid):
        # 利用 paperswithcode 的 API 获取代码地址
        # 2206.04673v1 后面的 v 不去掉也无所谓
        r = self.session.get(f"https://arxiv.paperswithcode.com/api/v0/papers/{aid}").json()
        return r["official"]["url"] if "official" in r and r["official"] else None

    def process_github(self, url):
        owner, repo = urlparse(url).path.split('/')[-2:]
        return_fields = "description topics stargazers_count".split()
        collection: Collection = self.db.github_repo_info
        d = collection.find_one({"url": url})
        if d is not None:
            logging.info("\tarxiv paper {aid} already in db")
            return 1, {k:v for k,v in d.items() if k in return_fields}
        r = self.session.get(f"https://api.github.com/repos/{owner}/{repo}").json()
        fields = "html_url description language topics homepage forks_count stargazers_count watchers_count open_issues_count size created_at pushed_at updated_at default_branch visibility license".split()
        d = OrderedDict()
        d['owner'] = owner
        d['repo'] = repo
        for k in fields:
            d[k] = r[k]
        collection.insert_one(d)
        logging.info(f"\tGithub repo {url} inserted")
        return 0, {k:v for k,v in d.items() if k in return_fields}
        
if __name__=="__main__":
    session = Session()
    session.resolve_url("https://arxiv.org/abs/2206.04673")
    