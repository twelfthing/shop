#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""



from django.conf import settings
from django.contrib import admin
from django.conf.urls import include, url, patterns
from django.conf.urls.static import static
from catelogue.views import HomePageView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', HomePageView.as_view()),
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    print urlpatterns