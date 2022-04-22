import requests
import urllib.parse
from time import sleep
# from bs4 import BeautifulSoup
from base import BaseSpider
from selenium.webdriver.common import action_chains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from settings import *
from utils import clear_string, retry, _print, RetryException

from easonsi import utils

""" 用 selenium 模拟登陆网易云, 更新歌单 @220422
- 登陆: 网页打开后手动登陆
- 输入歌单: 原项目是从 QQ音乐爬取的, 现在 QQ音乐最多显示 10首歌; 这里用的是 Apply Music 导出的
- 输出: 模拟搜索、添加歌曲到 config 中定义的歌单中 (只需要 歌单 id 即可)

TODO: 尝试用 cookies 登录
"""

class Muaic163(BaseSpider):
    @retry(retry_times=3)
    def prepare(self):
        self.browser.get("http://music.163.com")
        # self.browser.set_window_size(1920, 1080)
        
        # 登陆
        # action = action_chains.ActionChains(self.browser)
        # action.send_keys()
        # self.browser.switch_to.frame("contentFrame")
        # self.browser.execute_script("document.getElementById('index-enter-default').click()")
        # self.browser.switch_to.default_content()
        # sleep(0.5)
        # self.browser.execute_script("document.querySelectorAll('[data-type=\"netease\"]')[0].click()")
        # sleep(0.5)
        # element = self.browser.find_element_by_css_selector('input[class="js-input u-txt"]')
        # element.send_keys(self.config.account)
        # sleep(0.5)
        # element = self.browser.find_element_by_css_selector('input[type=\"password\"]')
        # element.send_keys(self.config.password)
        # sleep(0.5)
        # self.browser.execute_script("document.querySelectorAll('[data-action=\"login\"]')[6].click()")
        # print("login sucess")

    def get_source_playlist(self):
        """ 获取源歌单
        每一个元素为 (song, singer)
        """
        res = []
        for d in utils.LoadCSV("data/jazz-rock.csv", sep=","):
            res.append([d[0], d[1]])
        self.source_playlist = res
        # response = requests.get(self.config.source_playlist_url)
        # html = response.content
        # soup = BeautifulSoup(html, "html.parser")
        # details = soup.find_all("div", class_="songlist__item")
        # song_details = list()
        # for detail in details:
        #     song = detail.select("span[class='songlist__songname_txt']")[0].text
        #     singer = detail.select("div[class='songlist__artist']")[0].text
            # song_details.append((clear_string(song), clear_string(singer), ''))
        # print("get qq playlist success")
        # self.source_playlist = song_details

    def get_target_playlist(self):
        self.target_playlist_tag = self.config.target_playlist_url.split("playlist?id=")[-1]

    def sync_song(self):
        for song_detail in self.source_playlist:
            song = song_detail[0]
            singer = song_detail[1]
            search_word = u"{} {}".format(song, singer)
            url_sw = urllib.parse.quote(search_word.encode('utf8'))

            @retry(retry_times=3)
            def _add(self):
                self.browser.get(wy_search_url.format(url_sw))
                self.browser.switch_to.frame("contentFrame")
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-res-action="fav"]'))
                )
                self.browser.execute_script("document.querySelectorAll('span[data-res-action=\"fav\"]')[0].click()")
                sleep(0.5)
                self.browser.execute_script("document.querySelectorAll('li[data-id=\"{}\"]')[0].click()".format(self.target_playlist_tag))
                sleep(0.5)
                _print(u"song:{} success".format(song))

            try:
                _add(self)
            except RetryException:
                _print(u"song:{}, sync error".format(song))
                self.failed_list.append(search_word)
            else:
                self.success_list.append(search_word)

if __name__ == '__main__':
    Muaic163().run()
