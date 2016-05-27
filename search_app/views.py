from django.shortcuts import render
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from forms import SearchForm
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
# Create your views here.
from __init__ import searcher


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
    id_pos = searcher.find_document(query.split())
    urls = [searcher.get_url(doc_id) for doc_id, pos in id_pos]
    return render(request, 'search_app/results.html', {'query': query, 'urls': urls})