#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""

from django.shortcuts import render
from django.http.response import HttpResponse
# Create your views here.

def index(request):
    return HttpResponse('<body>Hello world!!</body>', content_type="text/html")