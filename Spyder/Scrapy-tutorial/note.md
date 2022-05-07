


```shell
scrapy startproject tutorial
cd tutorial
scrapy genspider quotes quotes.toscrape.com
# edit spiders/quotes.py
# start crawling
scrapy crawl quotes -o quotes.json
```


