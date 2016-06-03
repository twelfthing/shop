#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-06-03
"""

from django.shortcuts import render
from django.views.generic import TemplateView

class AccountAuthView(TemplateView):
    template_name = 'accounts/login_registration.html'

    def get_context_data(self, **kwargs)



