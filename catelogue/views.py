#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""

from django.shortcuts import render
from django.http.response import HttpResponse, JsonResponse 
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from catelogue.query import get_product_list, get_product_detail

class ProductListView(ListView):

    template_name = 'catelogue/home.html'

    queryset = get_product_list()

    paginate_by = 10

    http_method_names = ['get', 'post']

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        return context

class ProductDetailView(DetailView):

    template_name = 'catelogue/detail.html'

    queryset = get_product_detail()

    http_method_names = ['get', 'post']    

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        return context
