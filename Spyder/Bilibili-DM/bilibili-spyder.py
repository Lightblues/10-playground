""" 220520 @Lightblues
基于API的 Bilibili 爬虫
API: 
---
220526 转到 mongo
"""

from requests_html import HTMLSession
import math, random
import os, sys, time
import lxml.html
import re
import collections
import mysql.connector
from mysql.connector import MySQLConnection, Error
from mysql.connector.cursor import MySQLCursor
from bs4 import BeautifulSoup
import pandas as pd
import logging
import json
from datetime import datetime
from tqdm import tqdm

from pymongo import MongoClient
from pymongo.collection import Collection

from easonsi import utils
from config.config import config_mysql, header_bilibili


class SpyderBilibili(object):
    def __init__(self) -> None:
        self.init_mysql(config_mysql)
        # logging.info(f"init mysql database {config_mysql['database']}")
        self.init_session(header_bilibili)
        # self.init_logging()
        self.db = MongoClient('mongodb://localhost:27017/').bilibili
    
    def init_mysql(self, config):
        self.conn: mysql.connector.MySQLConnection = mysql.connector.connect(**config)
        
    def init_session(self, header):
        session = HTMLSession()
        session.headers.update(header)
        self.session: HTMLSession = session

    def db_check_exists(self, table_name, query):
        """ 检查是否存在
        示例: self.check_exists("book_list", f"version=1 AND book_id={book_id}")
        """
        cursor = self.conn.cursor(buffered=True)
        query = f"SELECT * FROM {table_name} WHERE {query};"
        cursor.execute(query, ())
        if not cursor.rowcount > 0: return False
        return True

    def db_select_one(self, table_name, where=None, params=tuple(), columns="*"):
        """ 查询单条
        示例: code, result = self.db_select_one("video_info", f"version=%s AND bvid=%s", (1, bvid), columns="raw")
        """
        query = f"SELECT {columns} FROM {table_name} WHERE {where};"
        cursor = self.conn.cursor(buffered=True)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            return -1, None
        row = cursor.fetchone()
        cursor.close()
        return 0, row

    def db_select_many(self, table_name, where=None, params=tuple(), columns="*"):
        """ 查询单条
        示例: self.db_select_one("book_list", f"version=%s AND book_id=%s", (1, book_id))
        """
        query = f"SELECT {columns} FROM {table_name} WHERE {where};"
        cursor: MySQLCursor = self.conn.cursor(buffered=True)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            return -1, None
        rows = cursor.fetchall()
        cursor.close()
        return 0, rows


    def init_logging(self, logname=f"{__file__}", dir="logs/bilibili/", level=logging.INFO):
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



    def get_popular_weekly(self, numbers=166, taskname="get_popular_weekly"):
        """ 爬取「每周必看」
            输出: popular_weekly"""
        self.init_logging(taskname)
        logging.info(f"start get_popular_weekly... total number {numbers}")
        # url = 'https://api.bilibili.com/x/web-interface/popular/series/list'
        url = 'https://api.bilibili.com/x/web-interface/popular/series/one?number={}'
        
        cursor = self.conn.cursor()
        # number 从1开始
        for number in range(1, numbers):
            if self.db_check_exists("popular_weekly", f"version={1} AND number={number}"):
                continue
            r = self.session.get(url.format(number))
            if r.status_code != 200:
                logging.error(f"{r.status_code} - {r.url}\n{r.text}")
                break
            query = "INSERT INTO popular_weekly (version, number, raw) VALUES (%s, %s, %s)"
            cursor.execute(query, (1, number, r.text))
            self.conn.commit()
            logging.info(f"{number}/{numbers} has been inserted")
        cursor.close()
        logging.info(f"end get_popular_weekly... ended at number {number}")

    def get_video_info_one(self, bvid):
        """ 爬取单条视频信息
            输出: video_info"""
        # if self.db_check_exists("video_info", f"version={1} AND bvid={bvid}"):
        #     return 0, None
        code, result = self.db_select_one("video_info", f"version=%s AND bvid=%s", (1, bvid), columns="raw")
        if code!=-1:
            return 0, result
        
        url = "http://api.bilibili.com/x/web-interface/view?bvid={}"
        cursor = self.conn.cursor()
        r = self.session.get(url.format(bvid))
        if r.status_code != 200:
            logging.error(f"{r.status_code} - {r.url}\n{r.text}")
            return -1, r
        query = "INSERT INTO video_info (version, bvid, raw) VALUES (%s, %s, %s)"
        cursor.execute(query, (1, bvid, r.text))
        self.conn.commit()
        return 1, r.text

    def get_video_infos(self, bvids, taskname="get_video"):
        """ 爬取多条视频信息 """
        # self.init_logging(taskname)
        
        n = len(bvids)
        count_success = 0
        count_crawled = 0
        logging.info(f"start get_video_infos... total number {n}")
        for bvid in bvids:
            code, _ = self.get_video_info_one(bvid)
            if code < 0:
                logging.error(f"{bvid} - {code}")
                continue
            count_success += 1
            count_crawled += code==1    # 返回码 1 定义为爬取得到的
            if count_success % 10 == 0:
                logging.info(f"{count_success}/{n} has been inserted")
            if count_crawled>0 and count_crawled % 10 == 0:
                t = random.randint(3, 5)
                logging.info(f"crawled {count_crawled}, randomly sleep {t}s")
                time.sleep(t)
                
        logging.info(f"end get_video_infos... ended at number {count_success}/{n} success")
        
    def get_popular_weekly_videos(self, taskname="get_popular_weekly_videos"):
        """ 爬取「每周必看」视频信息
            输出: video_info"""
        self.init_logging(taskname)
        logging.info(f"start get_popular_weekly_videos...")
        code, videos = self.db_select_many("popular_weekly_a", f"version=%s", (1,), columns="bvid")
        if code<0:
            logging.error(f"{code}")
            return
        bvids = [row[0] for row in videos]
        self.get_video_infos(bvids, taskname)
        logging.info(f"end get_popular_weekly_videos...")

    def process_popular_weekly(self, taskname="process_popular_weekly"):
        """ 整理 popular_weekly 表
            输入: popular_weekly 
            输出: popular_weekly_a
        """
        """ 相关id、分区、标题、描述、推荐理由 """
        keys = "aid bvid cid tid tname title desc duration rcmd_reason short_link".split()

        self.init_logging(taskname)
        logging.info("start process_popular_weekly...")
        code, result = self.db_select_many("popular_weekly", f"version=%s", (1,), columns="number, raw")
        
        cursor: MySQLCursor = self.conn.cursor()
        # 注意 desc 字段和 mysql 关键字冲突
        query = "INSERT IGNORE INTO popular_weekly_a (version, number, aid, bvid, cid, " \
            "tid, tname, title, `desc`, duration, rcmd_reason, short_link) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        # output = []
        for number, raw in result:
            output = []
            data = json.loads(raw)['data']
            for item in data["list"]:
                values = [1, number] + [str(item[key]) for key in keys]
                output.append(values)
                # cursor.execute("INSERT INTO popular_weekly_a (version, number, bvid) VALUES (%s, %s, %s)", (1, number, 778))
            cursor.executemany(query, output)
            self.conn.commit()
            logging.info(f"{number}/{len(result)} has been inserted")
            
        logging.info("end process_popular_weekly...")

    def process_video_info(self, taskname="process_video_info"):
        self.init_logging(taskname)
        logging.info(f"start {taskname}...")
        code, result = self.db_select_many("video_info", f"version=%s", (1,), columns="bvid, raw")
        
        cursor: MySQLCursor = self.conn.cursor()
        query = ""
        """ 相关id、分区、标题、描述、推荐理由 """
        keys = "aid bvid cid tid tname videos title desc pubdate ctime duration state copyright teenage_mode".split()
        keys_owner = "mid name face".split()
        keys_stat = "view danmaku reply favorite coin share now_rank his_rank like dislike evaluation argue_msg".split()
        # TODO: 修改逻辑
        query = "REPLACE INTO video_info_a (version, bvid, " \
            "aid, cid, tid, tname, videos, title, `desc`, pubdate, ctime, duration, `state`, copyright, teenage_mode, " \
                "mid, name, face, view, danmaku, reply, favorite, coin, share, now_rank, his_rank, `like`, dislike, evaluation, argue_msg, " \
                    "honor_reply) VALUES (" + ",".join(["%s"] * (len(keys) + len(keys_owner) + len(keys_stat) + 2)) + ")"
        # keys_rights = "bp elec download movie pay hd5 no_reprint autoplay ugc_pay is_cooperation ugc_pay_preview no_background clean_mode is_stein_gate is_360 no_share".split()
        for i, (bvid, raw) in enumerate(result):
            raw = json.loads(raw)
            if raw['code'] != 0:
                logging.error(f"{bvid} - {raw['code']}")
                continue
            data = raw['data']
            values = [1] + [data[key] for key in keys]
            values += [data["owner"][key] for key in keys_owner]
            values += [data["stat"][key] for key in keys_stat]
            values += data['honor_reply']
            cursor.execute(query, values)
            self.conn.commit()
            
            if i%100==0:
                logging.info(f"{i}/{len(result)} has been inserted")
            
        logging.info(f"end {taskname}...")

    def get_all_animes(self, taskname="get_all_animes"):
        """ 
        URL: https://www.bilibili.com/anime/index/
        """
        self.init_logging(taskname)
        url_pgc_season_index = "https://api.bilibili.com/pgc/season/index/result?season_version=-1&spoken_language_type=-1&area=-1&is_finish=-1&copyright=-1&season_status=-1&season_month=-1&year=-1&style_id=-1&order=3&st=1&sort=0&page={}&season_type=1&pagesize=20&type=1"
        total_pages = math.ceil(3241/20) # 163
        collection: Collection = self.db.bilibili_animelist
        count_success = count_craweled = 0
        for page in range(1, total_pages+1):
            if collection.find_one({"page": page}):
                count_success += 1
                continue
            r = self.session.get(url_pgc_season_index.format(page)).json()
            if r['code'] != 0:
                logging.error(f"page {page} code {r['code']}. {r}")
            collection.insert_one({
                "page": page,
                "data": r['data']
            })
            count_craweled += 1
            count_success += 1
            if count_craweled%20==0:
                t = random.randint(1, 3)
                logging.info(f"{count_success}/{total_pages} has been crawled. random sleep {t}s")
                time.sleep(t)
        logging.info(f"{count_success}/{total_pages} has been crawled")
    
    
    def get_anime_info(self, ssid, version="1"):
        """ 
        API: http://api.bilibili.com/pgc/view/web/season?season_id=41410
        """
        collection: Collection = self.db.anime_info
        d = collection.find_one({
            "ssid": ssid,
            "version": version,
            # "titlecn": {"$exists": True}
        })
        if d:
            return 0, d
        try:
            r = self.session.get("http://api.bilibili.com/pgc/view/web/season?season_id={}".format(ssid)).json()
            d = {
                "ssid": ssid,
                "info": r["result"],
                "version": version,
                "t_update": datetime.now()
            }
            collection.insert_one(d)
            return 1, d
        except Exception as e:
            return -1, e
        
    def get_anime_list(self, ssids, taskname="get_anime_list"):
        """ 爬取ssid列表. 调用 get_anime
        """
        self.init_logging(taskname)
        count_total = len(ssids)
        logging.info(f"start {taskname}.. total subjects: {count_total}")
        count_success = count_crawled = 0
        for ssid in ssids:
            e, d = self.get_anime_info(ssid)
            if e<0:
                logging.error(f"error at {ssid} !!!")
                logging.error(d)
                continue
            elif e==1:
                count_crawled += 1
            if count_crawled  and count_crawled%20==0:
                t = random.randint(3, 5)
                logging.info(f"[{count_success}/{count_total}] {count_crawled} items crawled, randomly sleep {t}s")
                time.sleep(t)
            count_success += 1
        logging.info(f"end {taskname}.. {count_success}/{count_total} craweled")

    
    def get_all_animes_info(self, taskname="get_all_animes_info"):
        collection_animelist = self.db.bilibili_animelist
        season_ids = []
        for item in collection_animelist.find():
            for anime in item['data']['list']:
                season_ids.append(str(anime['season_id']))
        # 
        self.get_anime_list(season_ids, taskname)
        
    def transfer(self, taskname="transfer"):
        """ 转移数据 """
        code, result = self.db_select_many("video_info", f"version=%s", (1,), columns="bvid, raw")
        # cursor: MySQLCursor = self.conn.cursor()
        collection: Collection = self.db.video_info
        for bvid,raw in tqdm(result):
            collection.insert_one({
                "bvid": bvid,
                "raw": raw,
                "version": 1,
                "t_update": datetime.now()
            })

    def process_animes_info(self):
        """ 处理番剧列表
        输出: anime_info_t"""
        collection_raw = self.db.anime_info
        self.db.drop_collection("anime_info_t")
        collection_anime_info_t = self.db.anime_info_t
        for item in tqdm(collection_raw.find()):
            info = item['info']
            d = {"ssid": item['ssid']}
            # 
            for c in cols_animeinfo:
                d[c] = info[c] if c in info else None
            # 统计指标 coins, danmakus favorites likes reply share views
            d.update(info['stat'])
            # 评分 count score 注意可能不存在该字段
            rating = info['rating'] if 'rating' in info else {}
            d.update(rating)
            # 权限相关 allow_bp allow_bp_rank allow_download allow_review area_limit ban_area_show can_watch copyright forbid_pre freya_white is_cover_show is_preview only_vip_download resource watch_platform
            d.update(info['rights'])
            # 发布相关 is_finish is_started pub_time pub_time_show weekday
            if "publish" in info:
                d.update(info["publish"])
            # desc id is_new title
            if "new_ep" in info:
                d.update(info["new_ep"])
            
            # episodes 例如柯南列表过长, 超出xlsx限制, 因此加以限制
            episodes = info['episodes'] if 'episodes' in info else []
            e = []
            if len(episodes) > 200:
                logging.warning(f"{item['ssid'], d['season_title']} episodes {len(episodes)} too long, only keep first 200")
            for episode in episodes[:200]:
                e.append({k:v for k,v in episode.items() if k in cols_episodes})
            if len(str(e)) > 30000:
                logging.error(f"{item['ssid']} episodes too long, {e}")
            seasons = info['seasons']
            s = []
            for season in seasons:
                s.append({k:v for k,v in season.items() if k in cols_seasons})
            d['seasons'] = s
            d['episodes'] = e
            for ii in "series".split():
                d[ii] = info[ii] if ii in info else None
            collection_anime_info_t.insert_one(d)


cols_animeinfo = "evaluate season_id season_title title subtitle total type subtitle "  \
    "link bkg_cover cover share_url".split()
# "episodes new_ep payment positive publish rating rights seasons section series stat"
# cols_episodes = "aid bvid cid id badge duration from is_view_hide long_title pub_time release_date link".split()
cols_episodes = "id bvid long_title".split()
cols_seasons = "season_id season_title".split()
# dimension 

spyder = SpyderBilibili()
# 「每周必看」
if False:
    spyder.get_popular_weekly()
    spyder.process_popular_weekly()

if False:
    spyder.get_popular_weekly_videos()
    spyder.process_video_info()

if False:
    spyder.get_all_animes()
    spyder.get_all_animes_info()
# spyder.transfer()
spyder.process_animes_info()

# spyder.get_video_single("BV14b411J7ML")
# code, result = spyder.db_select_one("video_info", f"version=%s AND bvid=%s", (1, "BV14b411J7ML"), columns="raw")
# code, result = spyder.db_select_one("popular_weekly", f"version=%s AND number=%s", (1, 1), columns="raw")
print()