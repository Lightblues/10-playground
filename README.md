# playground

记录一些日常代码

## Automation

- Telegram-linkbot
    - 基于 Telegram Bot 的自动化链接整合方案.

## Spyder

基本框架: `requests_html` + `beautifulsoup4` + `pymongo`. 参见 `xiaoyuzhou.py`

---

- `douban_豆瓣` 豆瓣个人+书籍列表 @2204
    - 比较成熟的框架了, 对于反爬策略不太强的网络应该可以借鉴
- `01-basic-framework` 基本的 requests+lxml 爬取框架
    - `requests` 之后用 `lxml.etree` 解析, 利用 xpath 获取内容.
    - 适合简单网站, 少量数据的爬取; 这里的示例是 GitHub
- `daily_fudan` 基于「平安复旦」API的自动化填写, 利用 GitHub Action;
    - 还用了OCR模块进行验证码识别
- `Selenium` 框架
    - `Weibo-Xuyongbo` 给新闻学院一个学长写的爬虫作业 @2203
- `WaiJiaoBu` 爬取外交部例行记者会数据 @2107
- `fudan_dataanalysis` 爬取复旦专业 + QS大学排名 @2111
- `Selenium-music` 重新看了一个基于 Selenium 框架的歌单同步repo; 正好借机管理歌单 @2204

## ML

- `SVM-RDF` 利用 sklearn.svm 库对非线性可分数据集处理，主要研究的是 **多项式、高斯核函数**
- `recommendation_system` Google RS 教程 <https://colab.research.google.com/github/google/eng-edu/blob/main/ml/recommendation-systems/recommendation-systems.ipynb>
    - TF版本 MF ，完整的推荐系统
    - t-SNE 降维可视化
    - 构造数据、使用特征进行 Softmax 见 <https://developers.google.com/machine-learning/recommendation/dnn/softmax>
