
""" https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/danmaku/danmaku_proto.md """

import requests
import google.protobuf.text_format as text_format
import bilibili.community.service.dm.v1.dm_pb2 as Danmaku

url = 'http://api.bilibili.com/x/v2/dm/web/history/seg.so'
params = {
    'type':1,           #弹幕类型
    'oid':144541892,    #cid
    'date':'2020-01-21' #弹幕日期
}
cookies = {
    'SESSDATA':'1f359612%2C1668602353%2Cf218c*51'
}
resp = requests.get(url,params,cookies=cookies)
data = resp.content

danmaku_seg = Danmaku.DmSegMobileReply()
danmaku_seg.ParseFromString(data)

# print(text_format.MessageToString(danmaku_seg.elems[0],as_utf8=True))
for i in range(40):
    print(text_format.MessageToString(danmaku_seg.elems[i],as_utf8=True))
