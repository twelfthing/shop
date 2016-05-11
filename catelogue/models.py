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

class Option(models.Model):
    """
    An option that can be selected for a particular item when the product
    is added to the basket.

    For example,  a list ID for an SMS message send, or a personalised message
    to print on a T-shirt.

    This is not the same as an 'attribute' as options do not have a fixed value
    for a particular item.  Instead, option need to be specified by a customer
    when they add the item to their basket.
    """
    name = models.CharField(_("Name"), max_length=128)
    code = models.SlugField(_("Code"), max_length=128, unique=True)

    REQUIRED, OPTIONAL = ('Required', 'Optional')
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    type = models.CharField(_("Status"), max_length=128, default=REQUIRED,
                            choices=TYPE_CHOICES)

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.name

    @property
    def is_required(self):
        return self.type == self.REQUIRED


@python_2_unicode_compatible
class ProductClass(models.Model):
    name = models.CharField(_('Name'), max_length=128)
    slug = models.SlugField(_('Slug'), max_length=128, unique=True)

    requires_shipping = models.BooleanField(_("Requires shipping?"),
                                            default=True)

    track_stock = models.BooleanField(_("Track stock levels?"), default=True)
    options = models.ManyToManyField(
        Option, blank=True, verbose_name=_("Options"))

    class Meta:
        ordering = ['name']
        verbose_name = _("Product class")
        verbose_name_plural = _("Product classes")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Category(models.Model):

    name = models.CharField(_('Name'), max_length=255, db_index=True)
    description = models.TextField(_('Description'), blank=True)
    image = models.ImageField(_('Image'), upload_to='categories', blank=True,
                              null=True, max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, db_index=True)

    _slug_separator = '/'
    _full_name_separator = ' > '

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.full_name

@python_2_unicode_compatible
class AttributeOptionGroup(models.Model):
    name = models.CharField(_('Name'), max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)

@python_2_unicode_compatible
class ProductAttribute(models.Model):
    product_class = models.ForeignKey(
        ProductClass, related_name='attributes', blank=True,
        null=True, verbose_name=_("Product type"))
    name = models.CharField(_('Name'), max_length=128)
    code = models.SlugField(
        _('Code'), max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
        ])

    # Attribute types
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    RICHTEXT = "richtext"
    DATE = "date"
    OPTION = "option"
    ENTITY = "entity"
    FILE = "file"
    IMAGE = "image"
    TYPE_CHOICES = (
        (TEXT, _("Text")),
        (INTEGER, _("Integer")),
        (BOOLEAN, _("True / False")),
        (FLOAT, _("Float")),
        (RICHTEXT, _("Rich Text")),
        (DATE, _("Date")),
        (OPTION, _("Option")),
        (ENTITY, _("Entity")),
        (FILE, _("File")),
        (IMAGE, _("Image")),
    )
    type = models.CharField(
        choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))

    option_group = models.ForeignKey(
        AttributeOptionGroup, blank=True, null=True,
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option"'))
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        ordering = ['code']
        verbose_name = _('Product attribute')
        verbose_name_plural = _('Product attributes')

    @property
    def is_file(self):
        return self.type in [self.FILE, self.IMAGE]

    def __str__(self):
        return self.name





@python_2_unicode_compatible
class AttributeOption(models.Model):
    group = models.ForeignKey(
        AttributeOptionGroup, related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    def __str__(self):
        return self.option

    class Meta:
        unique_together = ('group', 'option')
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')





@python_2_unicode_compatible
class Product(models.Model):

    STANDALONE, PARENT, CHILD = 'standalone', 'parent', 'child'
    STRUCTURE_CHOICES = (
        (STANDALONE, _('Stand-alone product')),
        (PARENT, _('Parent product')),
        (CHILD, _('Child product'))
    )
    structure = models.CharField(
        _("Product structure"), max_length=10, choices=STRUCTURE_CHOICES,
        default=STANDALONE)

    upc = models.CharField(
        _("UPC"), max_length=64, blank=True, null=True, unique=True,
        help_text=_("Universal Product Code (UPC) is an identifier for "
                    "a product which is not specific to a particular "
                    " supplier. Eg an ISBN for a book."))

    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        verbose_name=_("Parent product"),
        help_text=_("Only choose a parent product if you're creating a child "
                    "product.  For example if this is a size "
                    "4 of a particular t-shirt.  Leave blank if this is a "
                    "stand-alone product (i.e. there is only one version of"
                    " this product)."))

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(pgettext_lazy(u'Product title', u'Title'),
                             max_length=255, blank=True)
    slug = models.SlugField(_('Slug'), max_length=255, unique=False)
    description = models.TextField(_('Description'), blank=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        ProductClass, null=True, blank=True, on_delete=models.PROTECT,
        verbose_name=_('Product type'), related_name="products",
        help_text=_("Choose what type of product this is"))
    attributes = models.ManyToManyField(
        ProductAttribute,
        through='ProductAttributeValue',
        verbose_name=_("Attributes"),
        help_text=_("A product attribute is something that this product may "
                    "have, such as a size, as specified by its class"))
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        Option, blank=True, verbose_name=_("Product options"),
        help_text=_("Options are values that can be associated with a item "
                    "when it is added to a customer's basket.  This could be "
                    "something like a personalised message to be printed on "
                    "a T-shirt."))

    recommended_products = models.ManyToManyField(
        'Product', through='ProductRecommendation', blank=True,
        verbose_name=_("Recommended products"),
        help_text=_("These are products that are recommended to accompany the "
                    "main product."))

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField(_('Rating'), null=True, editable=False)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(
        _("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        Category, through='ProductCategory',
        verbose_name=_("Categories"))

    #: Determines if a product may be used in an offer. It is illegal to
    #: discount some types of product (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such products
    #: Note that this flag is ignored for child products; they inherit from
    #: the parent product.
    is_discountable = models.BooleanField(
        _("Is discountable?"), default=True, help_text=_(
            "This flag indicates if this product can be used in an offer "
            "or not"))

    class Meta:
        ordering = ['-date_created']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    def __str__(self):
        if self.title:
            return self.title
        if self.attribute_summary:
            return u"%s (%s)" % (self.get_title(), self.attribute_summary)
        else:
            return self.get_title()


@python_2_unicode_compatible
class ProductCategory(models.Model):

    product = models.ForeignKey(Product, verbose_name=_("Product"))
    category = models.ForeignKey(Category,
                                 verbose_name=_("Category"))

    class Meta:
        ordering = ['product', 'category']
        unique_together = ('product', 'category')
        verbose_name = _('Product category')
        verbose_name_plural = _('Product categories')

    def __str__(self):
        return u"<productcategory for product '%s'>" % self.product


class ProductRecommendation(models.Model):
    primary = models.ForeignKey(
        Product, related_name='primary_recommendations',
        verbose_name=_("Primary product"))
    recommendation = models.ForeignKey(
        Product, verbose_name=_("Recommended product"))
    ranking = models.PositiveSmallIntegerField(
        _('Ranking'), default=0,
        help_text=_('Determines order of the products. A product with a higher'
                    ' value will appear before one with a lower ranking.'))

    class Meta:
        ordering = ['primary', '-ranking']
        unique_together = ('primary', 'recommendation')
        verbose_name = _('Product recommendation')
        verbose_name_plural = _('Product recomendations')


@python_2_unicode_compatible
class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(
        ProductAttribute, verbose_name=_("Attribute"))
    product = models.ForeignKey(
        Product, related_name='attribute_values',
        verbose_name=_("Product"))

    value_text = models.TextField(_('Text'), blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
    value_option = models.ForeignKey(
        AttributeOption, blank=True, null=True,
        verbose_name=_("Value option"))
    value_file = models.FileField(max_length=255,
                                  blank=True, null=True)
    value_image = models.ImageField(max_length=255,
                                    blank=True, null=True)
    value_entity = GenericForeignKey(
        'entity_content_type', 'entity_object_id')

    entity_content_type = models.ForeignKey(
        ContentType, null=True, blank=True, editable=False)
    entity_object_id = models.PositiveIntegerField(
        null=True, blank=True, editable=False)

    def _get_value(self):
        return getattr(self, 'value_%s' % self.attribute.type)

    def _set_value(self, new_value):
        if self.attribute.is_option and isinstance(new_value, six.string_types):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(
                option=new_value)
        setattr(self, 'value_%s' % self.attribute.type, new_value)

    value = property(_get_value, _set_value)

    class Meta:
        unique_together = ('attribute', 'product')
        verbose_name = _('Product attribute value')
        verbose_name_plural = _('Product attribute values')

    def __str__(self):
        return self.summary()
