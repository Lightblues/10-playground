


## mysql: mysql.connector

- 官方 API: <https://dev.mysql.com/doc/connector-python/en/connector-python-reference.html>
    - 主要其中的 `connection, cursor` 类
- from [廖雪峰](https://www.liaoxuefeng.com/wiki/1016959663602400/1017802264972000)

```python
# 导入MySQL驱动:
>>> import mysql.connector
# 注意把password设为你的root口令:
>>> conn = mysql.connector.connect(user='root', password='password', database='test')
>>> cursor = conn.cursor()
# 创建user表:
>>> cursor.execute('create table user (id varchar(20) primary key, name varchar(20))')
# 插入一行记录，注意MySQL的占位符是%s:
>>> cursor.execute('insert into user (id, name) values (%s, %s)', ['1', 'Michael'])
>>> cursor.rowcount
1
# 提交事务:
>>> conn.commit()
>>> cursor.close()
# 运行查询:
>>> cursor = conn.cursor()
>>> cursor.execute('select * from user where id = %s', ('1',))
>>> values = cursor.fetchall()
>>> values
[('1', 'Michael')]
# 关闭Cursor和Connection:
>>> cursor.close()
True
>>> conn.close()
```

### 检查记录是否存在

```python
cursor = self.conn.cursor(buffered=True)
cursor.execute(query, (id,))
if cursor.rowcount > 0:
    print(f'{id} is cached')
    return cursor.fetchone()
cursor.close()
```


## Response 解析

### 直接用 xpath

```python
r = requests.get(url)
html = r.html
cover_link = html.xpath('//*[@id="mainpic"]/a/img/@src')[0]
```

### 将文本解析为 html (在用 xpath)

需求: 可能将 r.content 存储为 str 了.

```python
from lxml import html
import requests
url = 'https://www.data.gov/'
r = requests.get(url)
doc = html.fromstring(r.content)
link = doc.xpath('//a[@href="/metrics"]/text()')[0]
```

### 利用 BeautifulSoup 解析

注意 bs4 不能用 Xpath 语法

- doc: <https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/>

#### find_all()

[here](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/#find-all)

```python
soup = BeautifulSoup(content, 'html.parser')
```

- `name` 参数可以查找所有名字为 `name` 的tag,字符串对象会被自动忽略掉.

```python
soup.find_all("title")
# [<title>The Dormouse's story</title>]
```

- 如果一个指定名字的参数不是搜索内置的参数名,搜索时会把该参数当作指定名字tag的属性来搜索,如果包含一个名字为 `id` 的参数,Beautiful Soup会搜索每个tag的”id”属性.
    - 对于不满足变量名的名字, 可以通过 `find_all()` 方法的 `attrs` 参数定义一个字典参数来搜索包含特殊属性的tag

```python
soup.find_all(id='link2')
# [<a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>]
soup.find_all(href=re.compile("elsie"))
# [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>]

soup.find_all(href=re.compile("elsie"), id='link1')
# [<a class="sister" href="http://example.com/elsie" id="link1">three</a>]

data_soup.find_all(attrs={"data-foo": "value"})
# [<div data-foo="value">foo!</div>]
```

- 按照CSS类名搜索tag的功能, 注意参数名是 `class_`

```python
soup.find_all("a", class_="sister")
# [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>,
#  <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>,
#  <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>]

def has_six_characters(css_class):
    return css_class is not None and len(css_class) == 6

soup.find_all(class_=has_six_characters)
# [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>,
#  <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>,
#  <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>]

css_soup = BeautifulSoup('<p class="body strikeout"></p>')
css_soup.find_all("p", class_="strikeout")
# [<p class="body strikeout"></p>]
```

## 解析 url: urllib.parse

- 转义字符: `urllib.parse.quote(" 中文 ")`


