from django import forms


class SearchForm(forms.Form):
    query = forms.CharField(label='query', min_length=1, required=True)


class IndexUrlForm(forms.Form):
    url_to_index = forms.CharField(label='url to index', min_length=5,required=True)


