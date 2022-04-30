
## API

### 抓取豆瓣 已读/已看列表: get_movie_list

`get_movie_list(self, user_id="easonshi99")`

从个人主页爬取列表

        输出: movie_watched
            movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment
        处理重复主键: REPLACE

例子

douban_crawler.get_book_list()
douban_crawler.get_movie_list()

### 爬取详细信息

#### 爬取原始数据: get_movie

`get_movie(self, movie_id)`

爬取书籍, 保存原始信息

        输入: movie_id
        输出: 保存到 movie_raw 表
        数据格式: is_cached, (movie_id, url, title, year, cover_link, info_text, rating_text, content)
            其中 is_cached 标记是否已经缓存, 若未缓存, 说明发起了请求

例子: douban_crawler.get_movie(1304102)

#### 处理、合并中间数据

`process_movie(self, d_movie_watched, d_movie_raw, version=1)`

处理原始数据, 入库

        输入: d_movie_watched 为个人已看页面信息, d_movie_raw 为详情页的原始信息
        输出: movie_full
        输出结构:
            movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment, 
            director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website, 
            rate, rate_num, link_report, version
            其中, 值为数字的: movie_id, rate_num 为整数, rate, my_rate 为浮点数
        重复主键处理: 若version不同则更新, 否则不更新

#### 爬取所有列表

`get_movie_all(self)`

从 movie_watched 表爬取所有书籍信息

        输入: movie_watched 所包括的电影 (movie_id)
        中间结果: 调用 self.get_movie(movie_id) 将原始文本保存在 movie_raw
        输出: movie_full 记录所有电影的信息
            通过调用 process_movie(self, d_movie_watched, d_movie_raw, version=1) 得到完整的电影信息

### 处理数据

TODO: 抽象一些处理 mysql 数据的函数, 例如: 合并表

#### 更新表: update_movie_full_single_col

`update_movie_full_single_col(self, columnns: str, col_update:str, f)`

基于所定义的处理函数 f, 用表的若干列更新 movie_full 表的某一列

        参数:
            f: 处理函数, 输入为 columnns 所定义的列, 输出为要更新的列的值
            columnns: f 的输入参数, 例如 `"author, subtitle, publisher"` 筛选三个列, 这三个就作为 f输入参数
            col_update: 进行更新的列名
        注意在 SELECT 时自动加上了 movie_id 列, 从而进行对应的 UPDATE

例如 douban_crawler.update_movie_full_single_col("link_report", "link_report", douban_crawler.process_link_report) 处理电影描述中的段首空白.

## 数据表格式

### movie 表格式

- `movie_watched`: 从个人页面爬到的
    - movie_id, user_id, url, title, intro, my_rate, my_rate_time, my_comment
- `movie_raw`: 保存 content
    - movie_id, url, title, year, cover_link, info_text, rating_text, content
- `movie_full`: 最终处理的结果
    - movie_id, url, title, year, cover_link, my_rate, my_rate_time, my_comment,
    - director, scriptwriter, actors, types, official_website, country, language, release_date, duration, alias, imdb, series_premiere_time, series_season_num, series_set_number, series_episode_length, douban_website,
    - rate, rate_num, link_report, version
- `movie_feishu`: 从飞书 Database 导入的表 (temp)
    - title , link_report , my_comment , alias , my_status , my_note , my_tags , types , year , my_rate , my_feishu_date , url , other_links , feishu_update_time , feishu_create_time

## debug

### 处理爬取失败的情况

```js
安东尼奥尼的中国 https://movie.douban.com/subject/1292327/
[error] (1292285, 'https://movie.douban.com/subject/1292285/', "微观世界 Microcosmos: Le peuple de l'herbe")
```
