"""search_engine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from views import index, search_results, index_url, indexed_urls

app_name = 'search_app'
urlpatterns = [
    url(r'^search_results/(?P<query>.*)$', search_results, name='search_results'),
    url(r'index_url', index_url, name='index_url'),
    url(r'indexed_urls', indexed_urls, name='indexed_urls'),
    url(r'.*', index, name='index'),
]
