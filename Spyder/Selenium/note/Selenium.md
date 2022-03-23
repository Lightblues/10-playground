- 中文doc <https://www.selenium.dev/zh-cn/documentation/>
- pypi <https://pypi.org/project/selenium/>
- API <https://selenium-python.readthedocs.io/api.html>
- 其他
    - ChromeDriver: <https://chromedriver.chromium.org/home>

## 基本

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Chrome("/Users/frankshi/Downloads/chromedriver")

browser.get("http://www.baidu.com") 
print(browser.page_source[:1000])

# 三种方式获取
browser.get("http://www.taobao.com")
input_first = browser.find_element_by_id("J_SiteNav").text
input_second = browser.find_element_by_css_selector("#J_SiteNav").text
input_third = browser.find_element_by_xpath('//*[@id="J_SiteNav"]').text

# find_element + By 语法
input_first = browser.find_element(By.ID,"J_SiteNav").text
print(input_first)
```

注意连续爬取的时候, 可能因为页面没有加载好找不到元素, 需要等待. 见 <https://www.selenium.dev/zh-cn/documentation/webdriver/waits/>

```python
browser.get(url)
# 隐式等待
browser.implicitly_wait(10)
```

### 元素查找

当然还有 elements 版本

- find_element_by_name
- find_element_by_id
- find_element_by_xpath
- find_element_by_link_text
- find_element_by_partial_link_text
- find_element_by_tag_name
- find_element_by_class_name
- find_element_by_css_selector

### 元素属性

```python
# 好问题广场 id = guestSquare
browser.get("http://www.zhihu.com/explore")
logo = browser.find_element_by_id('guestSquare')
print(logo)
print(logo.get_attribute('class'))
```

```python
browser.get("http://www.zhihu.com/explore")
input = browser.find_element_by_class_name('css-1g4zjtl')

# text
print(input.text)

# 其他
print(input.id)
print(input.location)
print(input.tag_name)
print(input.size)
```

## 交互

- 参见API <https://selenium-python.readthedocs.io/api.html> 中的 7.2 Action Chains

```python
# browser.get("http://www.taobao.com")
input_str = browser.find_element_by_id('q')
input_str.send_keys("ipad")
time.sleep(3)
input_str.clear()
input_str.send_keys("MacBook pro")
button = browser.find_element_by_class_name('btn-search')
button.click()
```
