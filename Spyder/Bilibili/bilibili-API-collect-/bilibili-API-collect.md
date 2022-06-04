

弹幕

- 关注一篇稿件的历史弹幕
- [历史弹幕](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/danmaku/history.md)
- 需要自行编译 Proto [dm.proto](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/grpc_api/bilibili/community/service/dm/v1/dm.proto)
    - `protoc -I=[bilibili] --python_out=[out] bilibili/community/service/dm/v1/dm.proto` 注意可能需要修改一下文件名

笔记

- [视频笔记](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/note)
- 只关注公开笔记, 可以针对 稿件/用户级别 的笔记列表, 还可以爬取笔记内容
- 示例视频: <https://www.bilibili.com/video/BV1YA4y197G8>

排行榜

- [排行榜 & 最新视频](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/ranking&dynamic)
- <https://www.bilibili.com/v/popular/rank/all>
- 分区列表 (tid): <https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/video/video_zone.md>. 另可参考 [here](https://github.com/Vespa314/bilibili-api/blob/master/api.md)

答题

- [转正答题](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/newbie_exam)

视频

- [视频](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/video)
- info 中的属性很全
- 高能进度条 (一组数值)
- 视频快照 (一组图片)

剧集 bangumi

- [剧集](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/bangumi/info.md)
- 通过 番剧ssid / 剧集epid 查询

evaluate link
bkg_cover cover

episodes

评论区

- 感觉直接爬取热评即可, 不分析树结构
- [评论区](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/comment)

收藏夹

- 这里的 media_id 就是收藏夹的 fid

用户

- 基本信息
- 状态数 (投稿、播放量等)
- 用户关系: 关注、粉丝
- [个人空间](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/user/space.md)
    - 置顶、代表作、tag、空间公告
    - 玩过的游戏、投币的视频
    - 投稿、频道、收藏、课程、订阅

直播

专栏
