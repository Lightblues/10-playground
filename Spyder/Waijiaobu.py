# -*- coding: utf-8 -*-
"""
爬取外交部新闻发言记录：首页 > 发言人表态 > 例行记者会
"""
from tqdm import tqdm
import requests
import json
from bs4 import BeautifulSoup


prefix = "http://new.fmprc.gov.cn/web/fyrbt_673021/jzhsl_673025/"
listpage = "default_{}.shtml"

def get_onelist(pageindex):
    response = requests.get(prefix + pageindex)
    response.encoding = "utf8"      # 手动设置 encoding
    soup = BeautifulSoup(response.text, 'html.parser')

    # name 过滤类别，attrs 过滤属性
    links = soup.find(name='div', attrs={"class": "rebox_news"})        # find_all 的区别在于 limit=1
    aas = links.find_all('a', href=True)        # 简洁语法
    contents = []
    for a in aas:
        try:
            href = a['href']        # 访问属性
            contents.append(get_oneday(href[1:]))
        except Exception as e:
            print(e)
    return contents

def get_oneday(href):
    response = requests.get(prefix+href)
    response.encoding = "utf8"
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find(class_="vibox")
    return {
        "date": content.find(name='span', attrs={"id": "News_Body_Time"}).text,
        "text": content.text        # text 获取网页渲染内容
    }

contents = []
for i in tqdm(range(25, 7, -1)):
# for i in [25]:
    contents.extend(get_onelist(listpage.format(i)))

# 保存为 JSON 格式
with open("../data/Waijiaobu/wjb_2020.txt", "w", encoding="utf-8") as f:
    for c in contents:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")