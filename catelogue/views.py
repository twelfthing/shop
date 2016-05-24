#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""

from django.shortcuts import render
from django.http.response import HttpResponse, JsonResponse 
from django.views.generic.base import TemplateView



class HomePageView(TemplateView):
	template_name = 'catelogue/home.html'

	def get_context_data(self, **kwargs):
		return {}

