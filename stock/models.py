# coding=utf-8

"""
    Author: ChengCheng
    Date  : 2016-05-28
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.conf import settings

from catelogue.models import Product, Partner





class StockRecord(models.Model):

    # Price info:
    price_currency = models.CharField(
        _("Currency"), max_length=12, default='CNY')

    cost_price = models.DecimalField(
        _("Cost Price"), decimal_places=2, max_digits=12,
        blank=True, null=True)

    #: Number of items in stock
    num_in_stock = models.PositiveIntegerField(
        _("Number in stock"), blank=True, null=True)

    #: The amount of stock allocated to orders but not fed back to the master
    #: stock system.  A typical stock update process will set the num_in_stock
    #: variable to a new value and reset num_allocated to zero
    num_allocated = models.IntegerField(
        _("Number allocated"), blank=True, null=True)

    #: Threshold for low-stock alerts.  When stock goes beneath this threshold,
    #: an alert is triggered so warehouse managers can order more.
    low_stock_threshold = models.PositiveIntegerField(
        _("Low Stock Threshold"), blank=True, null=True)

    # Date information
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True,
                                        db_index=True)

    
    class Meta:
        verbose_name = _("Stock record")
        verbose_name_plural = _("Stock records")

    @property
    def net_stock_level(self):
        """
        The effective number in stock (eg available to buy).

        This is correct property to show the customer, not the num_in_stock
        field as that doesn't account for allocations.  This can be negative in
        some unusual circumstances
        """
        if self.num_in_stock is None:
            return 0
        if self.num_allocated is None:
            return self.num_in_stock
        return self.num_in_stock - self.num_allocated

    # 2-stage stock management model

    def allocate(self, quantity):
        """
        Record a stock allocation.

        This normally happens when a product is bought at checkout.  When the
        product is actually shipped, then we 'consume' the allocation.
        """
        if self.num_allocated is None:
            self.num_allocated = 0
        self.num_allocated += quantity
        self.save()
    allocate.alters_data = True

    def is_allocation_consumption_possible(self, quantity):
        return quantity <= min(self.num_allocated, self.num_in_stock)

    def consume_allocation(self, quantity):
        if not self.is_allocation_consumption_possible(quantity):
            raise InvalidStockAdjustment(
                _('Invalid stock consumption request'))
        self.num_allocated -= quantity
        self.num_in_stock -= quantity
        self.save()
    consume_allocation.alters_data = True

    def cancel_allocation(self, quantity):
        self.num_allocated -= min(self.num_allocated, quantity)
        self.save()
    cancel_allocation.alters_data = True

    @property
    def is_below_threshold(self):
        if self.low_stock_threshold is None:
            return False
        return self.net_stock_level < self.low_stock_threshold


@python_2_unicode_compatible
class StockAlert(models.Model):
    """
    A stock alert. E.g. used to notify users when a product is 'back in stock'.
    """
    stockrecord = models.ForeignKey(
        StockRecord, related_name='alerts',
        verbose_name=_("Stock Record"))
    threshold = models.PositiveIntegerField(_("Threshold"))
    OPEN, CLOSED = "Open", "Closed"
    status_choices = (
        (OPEN, _("Open")),
        (CLOSED, _("Closed")),
    )
    status = models.CharField(_("Status"), max_length=128, default=OPEN,
                              choices=status_choices)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_closed = models.DateTimeField(_("Date Closed"), blank=True, null=True)

    def close(self):
        self.status = self.CLOSED
        self.date_closed = now()
        self.save()
    close.alters_data = True

    def __str__(self):
        return _('<stockalert for "%(stock)s" status %(status)s>') \
            % {'stock': self.stockrecord, 'status': self.status}

    class Meta:
        ordering = ('-date_created',)
        verbose_name = _('Stock alert')
        verbose_name_plural = _('Stock alerts')


        
