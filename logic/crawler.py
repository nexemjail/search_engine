import requests
import logging
import os.path
import argparse
import re
import urlparse
from bs4 import BeautifulSoup
import base64
import codecs
from metadata import CRAWLED_FILES_DIR
logging.getLogger().setLevel(logging.DEBUG)


def CustomException(Exception):
    pass

def request_url(url):
    header = {'User-agent': 'Anime bot 0.1'}
    response = requests.request('GET', url, headers=header)
    if response.status_code != 200:
        logging.exception('Got a response code {} in {}'.format(response.status_code, response.url))
        raise CustomException('Invalid status code {}'.format(response.status_code))
    return response.text


class Crawler(object):
    def __init__(self, domen,crawled_documents_dir):
        self.crawled_documents_dir = crawled_documents_dir
        self.domen = domen

    def _construct_valid_link(self, current_url):
        if not re.match(r'http(s)?://*', current_url):
            link = urlparse.urljoin(self.domen, current_url)
        else:
            link = current_url
        return link

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
        valid_filename = base64.b64encode(unicode.encode(url, encoding='UTF-8'))
        with codecs.open(os.path.join(self.crawled_documents_dir, valid_filename), 'w', encoding='UTF-16') as f:
            f.write(text)

    def crawl(self, current_page):
        while True:
            text = request_url(current_page)
            bs = BeautifulSoup(text, 'html.parser')
            a_tags = bs.select('a.title')

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
    crawler = Crawler('https://www.reddit.com/', CRAWLED_FILES_DIR)
    crawler.crawl('https://www.reddit.com/r/anime/')





