
""" 
https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/other/bvid_desc.md
"""

table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF' #码表
tr = {} #反查码表
#初始化反查码表
for i in range(58):
    tr[table[i]] = i
s = [11, 10, 3, 8, 4, 6] #位置编码表
xor = 177451812 #固定异或值
add = 8728348608 #固定加法值

def bv2av(x):
    r = 0
    for i in range(6):
        r += tr[x[s[i]]] * 58 ** i
    return (r - add) ^ xor

def av2bv(x):
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    return ''. join(r)

# print(av2bv(170001))
# print(bv2av('BV17x411w7KC'))

print(bv2av("BV1YA4y197G8"))
print(bv2av("BV1gY4y1t7nE"))