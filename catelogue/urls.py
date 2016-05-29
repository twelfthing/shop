#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-24
"""
from django.conf.urls import url
from catelogue.views import ProductListView, ProductDetailView


urlpatterns = [
    url(r"^$", ProductListView.as_view(), name="products"),
    url(r"^(?P<slug>.+)/$", ProductDetailView.as_view(), name="product"),
]

