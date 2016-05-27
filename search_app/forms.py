from django import forms


class SearchForm(forms.Form):
    query = forms.CharField(label='query', min_length=1, required=True)
