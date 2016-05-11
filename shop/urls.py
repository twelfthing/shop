#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""



from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from catelogue.views import index

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', index),
]
if not settings.DEBUG:
    import debug_toolbar
    urlpatterns += url(r'^__debug__/', include(debug_toolbar.urls))
