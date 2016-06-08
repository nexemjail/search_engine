from natural_language import Term, to_doc_terms
from crawler import request_url
import html2text


def crawl_page(page):
    html = request_url(page)
    terms = to_doc_terms(html2text.html2text(html))
    return terms