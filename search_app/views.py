from django.shortcuts import render
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from forms import SearchForm
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
# Create your views here.
from __init__ import searcher
from logic.natural_language import to_query_terms

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
    print 'search_results!'
    # query_words = query_terms(query)
    # id_pos = searcher.find_document(query_words)
    print to_query_terms(query)
    ids = searcher.find_document_OR(query)
    print ids
    snippets_and_urls = [(searcher.generate_snippet(doc_id, query), searcher.get_url(doc_id))
                         for doc_id in ids]
    print len(snippets_and_urls)
    return render(request, 'search_app/results.html', {'query': query, 'snippets_and_urls': snippets_and_urls})