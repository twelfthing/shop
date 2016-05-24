#coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-24
"""

from catelogue.models import Product, Category, Attribute

def get_product_list(*args, **kwargs):

    return Product.objects.all()


def get_product_detail(slug, **kwargs):
    
    return Product.objects.get(slug=slug)

