
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

# ========================= 将之前保存的 QQ/网易云 歌单转为一样的 csv 格式 =========================
# %%
from easonsi import utils

def convert_platlist(fn):
    result = []
    platlist = ""
    for line in open(f"data/{fn}", "r", encoding="utf-8"):
        line = line.strip()
        if line.startswith("=="):
            platlist = line[2:].strip()
        elif line.find(" - ") != -1:
            song, singer = line.split(" - ", 1)
            result.append([song, singer, platlist])
    return result

result = convert_platlist("QQ.1.txt")
utils.SaveCSV(result, "data/QQ.1.csv", sep=",")

result = convert_platlist("netease.1.txt")
utils.SaveCSV(result, "data/netease.1.csv", sep=",")

# %%
utils.RemoveDupRows("data/netease.0.txt", ofn='*')
result = convert_platlist("netease.0.txt")
utils.SaveCSV(result, "data/netease.0.csv", sep=",")


# %%
