
""" 正好借这个 repo 做一下音乐管理?
导出的 Apply Music 列表名: Track name, Artist name, Album, Playlist name, Type
"""

#%%
from easonsi import utils

utils.SelectRowsbyCol("data/playlist-apple.csv", "data/jazz-rock.csv", ["Jazz Rock Essentials"], 3, sep=",")


# %%
res = []
for d in utils.LoadCSV("data/jazz-rock.csv", sep=","):
    res.append([d[0], d[1]])

res[:4]


# %%
