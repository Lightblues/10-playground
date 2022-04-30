from requests_html import HTMLSession
import math
import re
import pymysql


"""210216
目前爬取了前 30 页也就是排名前 720 条数据（每页 24 条记录）；
其中第 464 号《悲伤的贝拉多娜》 https://bangumi.tv/subject/13871 不知道为何有时会出现数据库中不存在的问题，暂且搁置；

TODO: 切换到新的框架

数据格式

CREATE TABLE bangumi(
    rank int PRIMARY KEY,
    name varchar(200),
    rate decimal(5,1),
    ratepeople int,
    中文名 varchar(200),
    话数 varchar(200),
    上映年度 varchar(200),
    片长 varchar(200),
    别名 varchar(200),
    放送开始 varchar(200),
    放送星期 varchar(200),
    原作 varchar(200),
    导演 varchar(200),
    脚本 varchar(200),
    分镜 varchar(2000),   --
    演出 varchar(2000),    --演出也有超的如《灌篮高手》
    音乐 varchar(200),   
    人物设定 varchar(200),
    分镜构图 varchar(200),
    美术监督 varchar(200),
    色彩设计 varchar(200),
    作画监督 varchar(2000),      --
    摄影监督 varchar(200),
    原画 varchar(2000),           --会有很长的
    主题歌编曲 varchar(200),
    主题歌作曲 varchar(200),
    主题歌演出 varchar(200),
    企画 varchar(200),
    制片人 varchar(200),
    制作 varchar(200),
    动画制作 varchar(200),
    官方网站 varchar(200),
    url varchar(200)
);
"""


##########################################
# 配置数据库
##########################################
host = 'localhost'
user = 'syc'
password = 'syc'
database = 'douban'

conn = pymysql.connect(host=host, user=user, password=password, database=database,
                       charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()


##########################################
# 网络请求
##########################################

session = HTMLSession()
header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br',       # 加了这个会乱码
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/',
}
session.headers.update(header)      # 更新请求 header，直接从 Chrome 抄来的

# url = 'https://bangumi.tv/subject/253'
def get_one(url):
    # 根据一个网页记录
    r = session.get(url)
    # title = r.html.xpath('//*[@id="headerSubject"]/h1/a')[0].attrs['title']
    title_ori = r.html.xpath('//*[@id="headerSubject"]/h1/a')[0].text
    infobox = r.html.xpath('//*[@id="infobox"]')[0]
    infos = infobox.xpath('//li')
    infos = [i.text for i in infos]

    info_dict = {}
    attrs = ('中文名', '话数', '上映年度', '片长', '别名', '放送开始', '放送星期', '原作', '导演', '脚本', '分镜', '演出', '音乐',
             '人物设定', '分镜构图', '美术监督', '色彩设计', '作画监督', '摄影监督', '原画', '主题歌编曲', '主题歌作曲', '主题歌演出',
             '企画', '制片人', '制作', '动画制作', '官方网站')
    for text in infos:
        k, v = text.split(': ', 1)
        if k in attrs:
            if info_dict.get(k):
                info_dict[k] += ' ' + v
            else:
                info_dict[k] = v

    # 评分信息
    rate = r.html.xpath('//span[@class="number"]')[0].text
    rate_people = r.html.xpath('//span[@property="v:votes"]')[0].text
    rank = r.html.xpath('//small[@class="alarm"]')[0].text
    # rank = re.findall()
    rank = int(rank[1:])
    print([rank, info_dict.get('中文名'), title_ori, float(rate), int(rate_people)])

    # [title_ori, rate, rate_people]
    # attrs = ('中文名', '话数', '上映年度', '片长', '别名', '放送开始', '放送星期', '原作', '导演', '脚本',
    # '分镜', '演出', '音乐', '人物设定', '分镜构图', '美术监督', '色彩设计', '作画监督', '摄影监督', '原画',
    # '主题歌编曲', '主题歌作曲', '主题歌演出', '企画', '制片人', '制作', '动画制作', '官方网站')


    try:
        c = r"INSERT INTO bangumi(brank, name, rate, ratepeople, 中文名, 话数, 上映年度, 片长, 别名, 放送开始, " \
            r"放送星期, 原作, 导演, 脚本, 分镜, 演出, 音乐, 人物设定, 分镜构图, 美术监督, 色彩设计, 作画监督, 摄影监督, " \
            r"原画, 主题歌编曲, 主题歌作曲, 主题歌演出, 企画, 制片人, 制作, 动画制作, 官方网站, url) " \
            r"VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(c, [rank, title_ori, float(rate), int(rate_people)] + [info_dict.get(k) for k in attrs] + [url])
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)

startpage = 1   # 开始的页数
target = 30     # 要爬取的页数
# url_page = 'https://bangumi.tv/anime/browser?sort=rank&page=2'
for page in range(startpage, startpage+target):
    print("== Collecting page ", page)
    url_page = 'https://bangumi.tv/anime/browser?sort=rank&page=' + str(page)
    r_page = session.get(url_page)
    bangumis = r_page.html.xpath('//h3')
    for bangumi in bangumis:
        # '/subject/770'
        # https://bangumi.tv/subject/3302
        url = 'https://bangumi.tv' + bangumi.xpath('//a')[0].attrs['href']
        try:
            get_one(url)
        except Exception as e:
            print(e)
            print(url)

