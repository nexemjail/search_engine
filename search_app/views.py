from django.shortcuts import render
from django.core.urlresolvers import reverse
from forms import SearchForm
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from logic.indexer import ShelveIndexer
from logic.searcher import Searcher
from logic.metadata import INDICES_DIR
import time

searcher = Searcher(INDICES_DIR, ShelveIndexer)


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
    ids = searcher.find_document_OR(query)
    # print ids/
    pre_snippets_time = time.time()
    snippets_and_urls = [(searcher.generate_snippet(doc_id, query), searcher.get_url(doc_id))
                         for doc_id in ids]
    # print len(snippets_and_urls)
    end_search_time = time.time()

    print 'snippets took {}'.format(end_search_time - pre_snippets_time)
    print 'finding documents took {}'.format(pre_snippets_time - begin_search_time)
    print 'whole searching procedure took {}'.format(end_search_time - begin_search_time)

    return render(request, 'search_app/results.html', {'query': query, 'snippets_and_urls': snippets_and_urls})