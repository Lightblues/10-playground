
灵感: <https://bgm.tv/blog/309472> 这里用GNN来预测动画排名

## 数据说明

`anime_info_t`: B站番剧信息

- 来源: 从 <https://www.bilibili.com/anime/index/> 爬取B站所有动画列表, 然后爬取B站相关数据
- 字段见 [番剧信息API](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/bangumi/info.md)
- 参见页面: <https://www.bilibili.com/bangumi/play/ss41410>
- 处理后共 3241 条
- 数据处理
    - 展开了数据中的 `stat, rating, rights, publish, new_ep` 项
    - 保留 episodes 数组中元素的 `id bvid long_title` 字段
    - 保留 seasons 数组中元素的 `season_id season_title` 字段
- 数据说明
    - 表中 `episodes seasons series` 三项为 array
    - 为了避免导出exls有些记录 `[ERR] Support 32767 characters in a cell only` 错误, 对于 episodes, seasons 内容进行了上述筛选, 并仅保留200集. 超长的番剧列表如下:

```sh
30it [00:00, 296.52it/s]WARNING:root:('33378', '名侦探柯南') episodes 1101 too long, only keep first 200
179it [00:00, 310.95it/s]WARNING:root:('5978', '博人传 火影忍者新时代') episodes 241 too long, only keep first 200
245it [00:00, 393.80it/s]WARNING:root:('1376', '家庭教师HITMAN REBORN!') episodes 203 too long, only keep first 200
397it [00:00, 563.37it/s]WARNING:root:('33415', '名侦探柯南（中配）') episodes 1100 too long, only keep first 200
471it [00:01, 609.24it/s]WARNING:root:('6260', '蜡笔小新 第一季（中文）') episodes 479 too long, only keep first 200
471it [00:01, 609.24it/s]WARNING:root:('3054', '游戏王 怪兽之决斗') episodes 224 too long, only keep first 200
542it [00:01, 636.09it/s]WARNING:root:('5761', '精灵宝可梦 无印') episodes 271 too long, only keep first 200
616it [00:01, 664.54it/s]WARNING:root:('6262', '蜡笔小新 第二季（中文）') episodes 873 too long, only keep first 200
1165it [00:02, 646.86it/s]WARNING:root:('103', 'KERORO军曹') episodes 358 too long, only keep first 200
1388it [00:02, 672.40it/s]WARNING:root:('32779', '哆啦A梦 第三季') episodes 312 too long, only keep first 200
1467it [00:02, 703.62it/s]WARNING:root:('2299', '乌龙派出所') episodes 342 too long, only keep first 200
```


`subject_t`: anime 基本信息, 爬取自 bgm.tv

- 来源: 从 <https://bgm.tv/anime/browser/> 得到 bangumi 动画区下的所有条目列表, 再爬取详细信息
- 相关字段见 [条目信息API](https://bangumi.github.io/api/#/%E6%9D%A1%E7%9B%AE/getSubjectById)
- 参见页面: <https://bgm.tv/subject/329906>
- 处理后共 16224 条
- 数据处理:
    - 展开了 `raing, collection`
    - collection 中的各计数为 bgm 用户标记数量
    - infobox 中的字段较为多样且为中文. 其中 `别名` 字段为 array
- 数据说明
    - 表中 `infobox, tags, persons` 字段内容为 array
