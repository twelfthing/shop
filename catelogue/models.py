# coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-11
"""

from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import get_language, pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.fields import GenericForeignKey


@python_2_unicode_compatible
class Category(models.Model):

    name = models.CharField(_('Name'), max_length=255, db_index=True)
    description = models.TextField(_('Description'), blank=True)
    image = models.ImageField(_('Image'), upload_to='categories', blank=True,
                              null=True, max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, db_index=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Attribute(models.Model):
    name = models.CharField(_('Name'), max_length=128, db_index=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Product(models.Model):

    upc = models.CharField(_("UPC"), max_length=64,
                           blank=True, null=True, unique=True)

    title = models.CharField(_('Title'),
                             max_length=255, blank=True)

    slug = models.SlugField(_('Slug'), max_length=255, unique=False)

    description = models.TextField(_('Description'), blank=True)

    attributes = models.ManyToManyField(
        Attribute,
        # through='AttributeValue',
        verbose_name=_("Attributes"),
        help_text=_("A product attribute is something that this product may "
                    "have, such as a size, as specified by its class"))

    rating = models.FloatField(_('Rating'), null=True, editable=False)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    date_updated = models.DateTimeField(
        _("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(Category,
                                        # through='ProductCategory',
                                        verbose_name=_("Categories"))

    is_discountable = models.BooleanField(_("Is discountable?"), default=True)

    # status = models.IntegerField(_('Status'), default=0)

    class Meta:
        ordering = ['-date_created']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', verbose_name=_("Product"))
    original = models.ImageField(
        _("Original"), max_length=255)
    caption = models.CharField(_("Caption"), max_length=200, blank=True)

    display_order = models.PositiveIntegerField(
        _("Display order"), default=0,
        help_text=_("An image with a display order of zero will be the primary"
                    " image for a product"))
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = _('ProductImage')
        verbose_name_plural = _('ProductImages')

    def __str__(self):
        return u"Image of '%s'" % self.product
