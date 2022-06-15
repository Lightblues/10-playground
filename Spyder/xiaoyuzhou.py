
from requests_html import HTMLSession
from urllib.parse import urlparse
import math, random
import os, sys, time
import lxml.html
import re
import collections
import mysql.connector
from bs4 import BeautifulSoup
import pandas as pd
import logging
import json
from datetime import datetime
from tqdm import tqdm

import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

from easonsi import utils

""" @220613
小宇宙爬虫, 主要的需求是存档(可能会404的)的音频文件. 目前仅存档小宇宙的ID信息和音频文件.
URL: https://www.xiaoyuzhoufm.com/episode/62a3739bb32f552f54730f2a
TODO: 1) 基于Telegram Bot等方案自动整合链接; 2) 提取ShowNotes和评论区.

MongoDB: xiaoyuzhou
    episode_info
"""

from config.config import config_mongo, header_xiaoyuzhou

class SpyderXiaoyuzhou(object):
    def __init__(self) -> None:
        """ 初始化数据库和 session """
        self.init_session(header_xiaoyuzhou)
        self.db = MongoClient(**config_mongo).xiaoyuzhou  # 'mongodb://IP:27017/'
        
    def init_session(self, header):
        session = HTMLSession()
        session.headers.update(header)
        self.session: HTMLSession = session
        
    def init_logging(self, logname=f"{__file__}", dir="logs/", level=logging.INFO):
        # 统一将日志记录在 logs 中, logname/taskname 不需要加后缀 .log
        os.makedirs(dir, exist_ok=True)
        logging.root.handlers = []
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
            level=level,
            handlers=[
                logging.FileHandler(os.path.join(dir, f"{logname}.log")),
                logging.StreamHandler()
            ]
        )
        
    def get_single_episode(self, url, taskname='get_single_episode'):
        """ 获取单条episode信息 """
        episode_id = urlparse(url).path.split('/')[-1]
        
        logging.info(f"[{taskname}] start crawlling {episode_id}")
        collection: Collection = self.db.episode_info
        if collection.find_one({"episode_id": episode_id}) is not None:
            logging.info(f"  episode_id {episode_id} already in db")
            return
        
        try:
            r = self.session.get(url)
            content = r.content.decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            # soup.find_all(class_='title')
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
                "content": content,
                "t_update": datetime.now()
            }
            collection.insert_one(d)
        except Exception as e:
            logging.error(f"  error: {e}")
        logging.info(f"  episode_id {episode_id} done")
        
    def download_episode(self, episode_id, dir="audio/xiaoyuzhou", taskname='download_episode'):
        """ 下载单条episode """
        logging.info(f"[{taskname}] start downloading {episode_id}")
        apath = f'{dir}/{episode_id}.mp3'
        if os.path.exists(apath):
            logging.info(f"  episode_id {episode_id} already downloaded")
            return 0
        
        collection: Collection = self.db.episode_info
        d = collection.find_one({"episode_id": episode_id})
        if d is None:
            logging.error(f"  episode_id {episode_id} not found in db!!")
            return -1
        audio_url = d['audio_url']
        
        try:
            # with open(apath, 'wb') as f:
            #     r = self.session.get(audio_url)
            #     f.write(r.content)
            self.download_use_stream(audio_url, apath)
        except Exception as e:
            logging.error(f"  error downloading: {e}")
        logging.info(f"  episode_id {episode_id} done")
    
    def get_single_episode_and_download(self, url):
        # 封装两个任务
        self.get_single_episode(url)
        episode_id = urlparse(url).path.split('/')[-1]
        self.download_episode(episode_id)

    def download_use_stream(self, url: str, fname: str):
        """ 采用stream下载文件, 显示进度条
        from https://www.qycn.com/xzx/article/1182.html """
        # 用流stream的方式获取url的数据
        resp = self.session.get(url, stream=True)
        # 拿到文件的长度，并把total初始化为0
        total = int(resp.headers.get('content-length', 0))
        # 打开当前目录的fname文件(名字你来传入)
        # 初始化tqdm，传入总数，文件名等数据，接着就是写入，更新等操作了
        with open(fname, 'wb') as file, tqdm(
            desc=fname,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

spyder = SpyderXiaoyuzhou()
spyder.init_logging("xiaoyuzhou")
# spyder.get_single_episode(url = "https://www.xiaoyuzhoufm.com/episode/629b2adf525536dd0293626e")
# spyder.download_episode(episode_id = "629b2adf525536dd0293626e")
spyder.get_single_episode("https://www.xiaoyuzhoufm.com/episode/62a3739bb32f552f54730f2a")
