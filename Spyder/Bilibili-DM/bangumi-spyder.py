""" 220525 @Lightblues
基于API的 bangumi.tv 爬虫, 将数据库换成了 mongo
API: https://bangumi.github.io/api/

subject: 爬取的原始 JSON 数据
subject_t: 处理输出表
"""

from requests_html import HTMLSession
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
from config.config import header_bangumi

base_url = "https://api.bgm.tv"
url_s = "https://api.bgm.tv/v0/subjects/{}" # 329906
url_s_persons = "https://api.bgm.tv/v0/subjects/{}/persons"
url_s_characters = "https://api.bgm.tv/v0/subjects/{}/characters"
url_s_subjects = "https://api.bgm.tv/v0/subjects/{}/subjects"

class SpyderBangumi(object):
    def __init__(self) -> None:
        """ 初始化数据库和 session """
        self.init_session(header_bangumi)
        self.db = MongoClient('mongodb://localhost:27017/').bangumi
        # self.init_logging()

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
        
    def db_find_one(self, dbname, version="1", **query):
        """ 封装 mongo 查询? """
        collection = self.db[dbname]
        query["version"] = version
        r = collection.find_one(query)
        if r:
            return 0, r
        return -1, None

    def get_subject(self, subject_id, version="1"):
        """ 爬取单条番剧信息
        url: https://api.bgm.tv/v0/subject/{subject_id}
        输出: subject 表
        """
        collection: Collection = self.db.subject
        d = collection.find_one({
            "subject_id": subject_id,
            "version": version,
            # "titlecn": {"$exists": True}
        })
        if d:
            return 0, d
        try:
            info = self.session.get(url_s.format(subject_id)).json()
            persons = self.session.get(url_s_persons.format(subject_id)).json()
            characters = self.session.get(url_s_characters.format(subject_id)).json()
            subjects = self.session.get(url_s_subjects.format(subject_id)).json()
            # assert info and info["name"], f"{subject_id} - {info}"
            title = info["name"] if "name" in info else ""
            titlecn = info["name_cn"] if "name_cn" in info else ""
            # assert persons, f"{subject_id} - {persons}"
            # assert characters, f"{subject_id} - {characters}"
            d = {
                "subject_id": subject_id,
                "title": title,
                "titlecn": titlecn,
                "info": info,
                "persons": persons,
                "characters": characters,
                "subjects": subjects,
                "version": version,
                "t_update": datetime.now()
            }
            collection.insert_one(d)
            return 1, d
        except Exception as e:
            # print(e)
            return -1, e
        
    def get_calendar(self, fn=None):
        """ 获取本季度番剧列表
        URL: https://api.bgm.tv/calendar
        """
        if fn is None:
            fn =  f"../data/calendar-{datetime.now().strftime('%Y%m%d')}.json"
        if os.path.exists(fn):
            return utils.LoadJson(fn)
        url = base_url + "/calendar"
        r = self.session.get(url)
        if r.status_code != 200:
            logging.error(f"{r.status_code} - {r.url}\n{r.text}")
        d = json.loads(r.text)
        utils.SaveJson(d, fn)
        return d
    
    def get_all_animes(self, taskname="get_all_animes"):
        """ 手动爬取所有的番剧id
        URL: https://bgm.tv/anime/browser
        """
        self.init_logging(taskname)
        url = "https://bgm.tv/anime/browser?sort=date&page={}"
        subject_ids = {}
        total_pages = 823
        for page in range(1, total_pages+1):
            sids = []
            r = self.session.get(url.format(page))
            soup = BeautifulSoup(r.content, 'html.parser')
            item_list = soup.find_all(id="browserItemList")[0]
            for item in item_list.find_all(name="li"):
                sids.append(item.attrs["id"].split("_")[1])
            subject_ids[page] = sids
            if page % 10 == 0:
                time.sleep(random.randint(1, 3))
                logging.info(f"{page}/{total_pages}")
        utils.SaveJson(subject_ids, "../data/subject_ids.json")
    
    def get_subjects_calendar(self, taskname="get_subjects_calendar"):
        """ 爬取列表对应的番剧信息
        保存: subject表"""
        self.init_logging(taskname)
        data = self.get_calendar()
        subject_ids = []
        for d in data:
            for item in d["items"]:
                subject_id = item["id"]
                subject_ids.append(str(subject_id))
        
        logging.info(f"start {taskname}.. total subjects: {len(subject_ids)}")
        count_success = count_crawled = 0
        for subject_id in subject_ids:
            e, d = self.get_subject(subject_id)
            if e<0:
                logging.error(f"error at {subject_id} !!!")
                logging.error(d)
                # break
            elif e==1:
                count_crawled += 1
            if count_crawled  and count_crawled%10==0:
                t = random.randint(3, 5)
                logging.info(f"crawled {count_crawled}, randomly sleep {t}s")
                time.sleep(t)
            count_success += 1
        logging.info(f"end {taskname}.. {count_success}/{len(subject_ids)} craweled")

    def get_subjects_list(self, subject_ids, taskname="get_subjects_list"):
        """ 爬取 subject_ids 所指定的番剧信息 """
        self.init_logging(taskname)

        count_total = len(subject_ids)
        logging.info(f"start {taskname}.. total subjects: {count_total}")
        count_success = count_crawled = 0
        for subject_id in subject_ids:
            e, d = self.get_subject(subject_id)
            if e<0:
                logging.error(f"error at {subject_id} !!!")
                logging.error(d)
                continue
            elif e==1:
                count_crawled += 1
            if count_crawled  and count_crawled%10==0:
                t = random.randint(3, 5)
                logging.info(f"[{count_success}/{count_total}] crawled {count_crawled}, randomly sleep {t}s")
                time.sleep(t)
            count_success += 1
        logging.info(f"end {taskname}.. {count_success}/{count_total} craweled")

    def get_all_anime_info(self, taskname="get_all_anime_info"):
        """ 爬取 subject_ids.json 中的所有番剧信息 """
        data = utils.LoadJson("../data/subject_ids.json")
        subjects = []
        for k,v in data.items():
            subjects += v
        self.get_subjects_list(subjects, taskname)
        
    def process_animes_info(self):
        """ 处理番剧列表
        输出: subject_t"""
        collection_raw = self.db.subject
        self.db.drop_collection("subject_t")
        collection_subject_t = self.db.subject_t
        for s in tqdm(collection_raw.find()):
            d = {}
            
            info = s["info"]
            # 有些不给爬, 例如 '372317'
            if "id" not in info: continue
            for c in cols_animeinfo:
                d[c] = info[c]

            # 用户标记 on_hold dropped wish collect doing
            d.update(info['collection'])
            # 评分相关
            rating = info['rating']
            ratingcount = rating.pop('count')
            # rank total score
            d.update(rating)
            for k,v in ratingcount.items():
                d[f"raint_{k}"] = v
            
            # 下面的 infobox, tags, persons 保留为 array
            # infobox 包括: 别名 放松开始 官方网站 原作...
            # for o in info['infobox']:
            #     d[o['key']] = o['value']
            d['infobox'] = info['infobox']
            # tag 列表直接保留 [{name, count}]
            d['tags'] = info['tags']
            
            persons = s["persons"]
            ps = []
            for person in persons:
                p = {k: v for k,v in person.items() if k in "name relation type id".split()}
                ps.append(p)
            d['persons'] = ps
            
            collection_subject_t.insert_one(d)

    def process_subjects(self, version="1"):
        """ TODO
         """
        collection: Collection = self.db.subject
        findfilter = {
            "version": version,
        }
        for s in tqdm(collection.find(findfilter)):
            # 调整 subject 表列: 构建 title, titlecn 列方便检索
            # subject_id = s["subject_id"]
            # title, titlecn = s['info']['name'], s['info']['name_cn']
            # collection.update_one({
            #     "subject_id": subject_id, "version": version
            # }, { "$set": { 
            #         "title": title,
            #         "titlecn": titlecn
            #     } 
            # })
            
            # 将 subject_id 列转为 str
            subject_id = s["subject_id"]
            collection.update_one({
                "subject_id": subject_id, "version": version
            }, { "$set": {
                "subject_id": str(subject_id)
            } })

cols_animeinfo = "id date platform name name_cn total_episodes summary " \
    "eps volumes locked nsfw".split()

spyder = SpyderBangumi()
# spyder.get_calendar()
# spyder.get_subject(310263)
# spyder.get_subjects_calendar()
if False:
    spyder.get_all_animes()
    spyder.get_all_anime_info()
    spyder.process_animes_info()
# spyder.process_subjects()

