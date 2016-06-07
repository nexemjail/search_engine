# -*- coding: utf8 -*-
import requests
import logging
import os.path
import re
import urlparse
from bs4 import BeautifulSoup
import base64
import codecs
import html2text
from metadata import CRAWLED_FILES_DIR,\
    CRAWLED_FILES_DIR_HACKERNEWS, CRAWLED_FILES_DIR_WIKI,\
    ALTCHARS, CRAWLED_FILES_DIR_WIKI_NEW
import robotexclusionrulesparser
import time
from natural_language import to_doc_terms
logging.getLogger().setLevel(logging.DEBUG)


class CustomException(BaseException):
    pass


def request_url(url):
    header = {'User-agent': 'Anime bot 0.1'}
    response = requests.request('GET', url, headers=header)
    if response.status_code != 200:
        logging.exception('Got a response code {} in {}'.format(response.status_code, response.url))
        raise CustomException('Invalid status code {}'.format(response.status_code))
    return response.text


def crawl_page(page):
    html = request_url(page)
    text = html2text.html2text(html)
    return text


class Crawler(object):
    def __init__(self, domain, crawled_documents_dir,
                 #add width
                 max_width = 15,
                 max_depth=3, short_hostname=''):
        self.crawled_documents_dir = crawled_documents_dir
        self.domain = domain
        self.max_width = 15
        self.short_hostname = short_hostname.encode('utf8')
        self.max_depth = max_depth
        self.robots_txt = robotexclusionrulesparser.RobotFileParserLookalike()
        self.robots_txt.set_url(urlparse.urljoin(self.domain, 'robots.txt'))
        self.robots_txt.read()
        # print self.robots_txt.user_agent
        crawl_delay = self.robots_txt.get_crawl_delay('*')
        if crawl_delay:
            self.crawl_delay = crawl_delay
        else:
            self.crawl_delay = 0
        self.crawled_links = set()

    def _construct_valid_link(self, current_url):
        # try:
        # TODO : validate
        if not re.match(r'http(s)?://.*[/(.html)]', current_url):
            link = urlparse.urljoin(self.domain, current_url)
        else:
            link = current_url

        if all([el in link for el in "<>#%{}|\^~[]"]):
            link = link.split('#')[0]
        for el in "<>#%{}|\^~[]":
            if el in link:
                link = link.split(el)[0]

        return link
        # except TypeError as e:
        #     print current_url
        #     print e

    @staticmethod
    def _check_link(link):
        match_obj = re.match(r'http(s)?://(www.)?reddit\.com/.*', link)
        return match_obj

    @staticmethod
    def _exctract_text(html):
        bs = BeautifulSoup(html,'html.parser')
        texts = bs.select('div.content .usertext-body')
        return ''.join(map(lambda text: text.text, texts))

    def _save_to_disk(self, url, text):
        valid_filename = base64.b64encode(url.encode('UTF-8'), ALTCHARS)
        with codecs.open(os.path.join(self.crawled_documents_dir, valid_filename), 'w', encoding='utf8') as f:
            f.write(text)

    def crawl_by_links(self, current_page, depth=0):
        current_page_encoded_utf = current_page.encode('utf8')
        if depth >= self.max_depth \
                or not self.robots_txt.can_fetch('*', current_page) \
                or self.short_hostname not in current_page\
                or current_page_encoded_utf in self.crawled_links:
            # print 'wasted {}'.format(current_page_encoded_utf)
            return
        try:
            html = request_url(current_page)
            bs = BeautifulSoup(html, 'html.parser')
            a_tags = bs.findAll('a')

            links = {self._construct_valid_link(a.get('href')) for a in a_tags if a and a.get('href')}

            self._save_to_disk(current_page, html2text.html2text(html))
            self.crawled_links.add(current_page_encoded_utf)
            print 'Crawled {}'.format(current_page_encoded_utf)
            time.sleep(self.crawl_delay/20)
            for link in links:
                self.crawl_by_links(link, depth + 1)
        except CustomException:
            return

    def crawl(self, current_page):
        while True:
            text = request_url(current_page)
            bs = BeautifulSoup(text, 'html.parser')
            a_tags = bs.findAll('a.title')
            try:
                links_to_crawl = {self._construct_valid_link(link.get('href')) for link in a_tags}
                for link in links_to_crawl:
                    if Crawler._check_link(link):
                        html = request_url(link)
                        text = Crawler._exctract_text(html)
                        self._save_to_disk(link, text)

                next_page_tag = bs.find('a', attrs={'rel': 'nofollow next'})
                current_page = self._construct_valid_link(next_page_tag.get('href'))
            except CustomException as e:
                logging.exception('got an href parsing error {}'.format(e))
                pass

if __name__ == '__main__':
    pass
    # html = request_url('http://tut.by/')
    # print html2text.html2text(html)
    # data = extract_all_text(html)
    # # print data
    # crawler = Crawler('https://news.ycombinator.com/', CRAWLED_FILES_DIR_HACKERNEWS,
    #                   short_hostname='news.ycombinator.com', max_depth=5)
    # crawler.crawl_by_links('https://news.ycombinator.com/')

    crawler = Crawler('https://en.wikipedia.org/', CRAWLED_FILES_DIR_WIKI_NEW,
                      short_hostname='en.wikipedia.org',max_depth=10)
    crawler.crawl_by_links('https://en.wikipedia.org/wiki/Monthly_Sh%C5%8Dnen_Ace')






