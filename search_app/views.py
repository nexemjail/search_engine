from django.shortcuts import render
from django.core.urlresolvers import reverse
from forms import SearchForm, IndexUrlForm
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from logic.indexer import ShelveIndexer
from logic.searcher import Searcher
from logic.metadata import INDICES_DIR, INDEX_WIKI, CRAWLED_USER_PAGES, INDEX_WIKI_MINI
from logic.crawler import crawl_page
import multiprocessing.pool
import time

searcher = Searcher(INDEX_WIKI_MINI, ShelveIndexer)


@require_http_methods(['GET', 'POST'])
def index(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            return HttpResponseRedirect(reverse('search_app:search_results', args=(query,)))
        return render(request, 'search_app/index.html', {'form': form})
    elif request.method == 'GET':
        form = SearchForm()
        return render(request, 'search_app/index.html', {'form': form})


@require_http_methods(['GET'])
def search_results(request, query):
    # print 'search_results!'
    # query_words = query_terms(query)
    # id_pos = searcher.find_document(query_words)
    # print to_query_terms(query)
    begin_search_time = time.time()
    ids = list(searcher.find_document_OR(query))
    pre_snippets_time = time.time()
    # snippets = [searcher.generate_snippet(id_, query) for id_ in ids]
    snippets = searcher.generate_snippets(ids, query)
    urls = [searcher.get_url(doc_id) for doc_id in ids]
    snippets_and_urls = zip(snippets, urls)
    # print len(snippets_and_urls)
    end_search_time = time.time()

    # print 'snippets took {}'.format(end_search_time - pre_snippets_time)
    # print 'finding documents took {}'.format(pre_snippets_time - begin_search_time)
    # print 'whole searching procedure took {}'.format(end_search_time - begin_search_time)

    return render(request, 'search_app/results.html',
                  {'query': query, 'snippets_and_urls': snippets_and_urls,
                   'results_count' : len(ids), 'searching_time' : end_search_time - begin_search_time})


@require_http_methods(['GET', 'POST'])
def index_url(request):
    if request.method == 'GET':
        form = IndexUrlForm()
    elif request.method == 'POST':
        form = IndexUrlForm(request.POST, request.FILES)
        if form.is_valid():
            url_to_index = form.cleaned_data['url_to_index']
            filename = form.cleaned_data['file']
            links = []
            if url_to_index:
                links.append(url_to_index)
            elif filename:
                links.extend([x for x in filename.read().split('\n') if x and not x.isspace()])
            _ = [searcher.indices.add_document(crawl_page(link), link.encode('utf8')) for link in links]
            return HttpResponseRedirect(reverse('search_app:index'))
    return render(request, 'search_app/index_form.html', {'form': form})


@require_http_methods(['GET'])
def indexed_urls(request):
    urls = searcher.indices.id_to_url.values()
    return render(request, 'search_app/urls_list.html', {'urls': urls})




