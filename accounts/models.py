import hashlib
import random

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import six, timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class CommunicationTypeManager(models.Manager):

    def get_and_render(self, code, context):
        try:
            commtype = self.get(code=code)
        except self.model.DoesNotExist:
            commtype = self.model(code=code)
        return commtype.get_messages(context)


@python_2_unicode_compatible
class Email(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='emails',
                             verbose_name=_("User"))
    subject = models.TextField(_('Subject'), max_length=255)
    body_text = models.TextField(_("Body Text"))
    body_html = models.TextField(_("Body HTML"), blank=True)
    date_sent = models.DateTimeField(_("Date Sent"), auto_now_add=True)

    class Meta:
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')

    def __str__(self):
        return _(u"Email to %(user)s with subject '%(subject)s'") % {
            'user': self.user.get_username(), 'subject': self.subject}


@python_2_unicode_compatible
class CommunicationEventType(models.Model):
    """
    A 'type' of communication.  Like a order confirmation email.
    """

    #: Code used for looking up this event programmatically.
    # e.g. PASSWORD_RESET. AutoSlugField uppercases the code for us because
    # it's a useful convention that's been enforced in previous Oscar versions
    code = models.SlugField(
        _('Code'), max_length=128, unique=True, help_text=_("Code used for looking up this event programmatically"))

    #: Name is the friendly description of an event for use in the admin
    name = models.CharField(
        _('Name'), max_length=255,
        help_text=_("This is just used for organisational purposes"))

    # We allow communication types to be categorised
    # For backwards-compatibility, the choice values are quite verbose
    ORDER_RELATED = 'Order related'
    USER_RELATED = 'User related'
    CATEGORY_CHOICES = (
        (ORDER_RELATED, _('Order related')),
        (USER_RELATED, _('User related'))
    )

    category = models.CharField(
        _('Category'), max_length=255, default=ORDER_RELATED,
        choices=CATEGORY_CHOICES)

    # Template content for emails
    # NOTE: There's an intentional distinction between None and ''. None
    # instructs Oscar to look for a file-based template, '' is just an empty
    # template.
    email_subject_template = models.CharField(
        _('Email Subject Template'), max_length=255, blank=True, null=True)
    email_body_template = models.TextField(
        _('Email Body Template'), blank=True, null=True)
    email_body_html_template = models.TextField(
        _('Email Body HTML Template'), blank=True, null=True,
        help_text=_("HTML template"))

    # Template content for SMS messages
    sms_template = models.CharField(_('SMS Template'), max_length=170,
                                    blank=True, null=True,
                                    help_text=_("SMS template"))

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

    objects = CommunicationTypeManager()

    # File templates
    email_subject_template_file = 'customer/emails/commtype_%s_subject.txt'
    email_body_template_file = 'customer/emails/commtype_%s_body.txt'
    email_body_html_template_file = 'customer/emails/commtype_%s_body.html'
    sms_template_file = 'customer/sms/commtype_%s_body.txt'

    class Meta:
        verbose_name = _("Communication event type")
        verbose_name_plural = _("Communication event types")

    def get_messages(self, ctx=None):
        """
        Return a dict of templates with the context merged in

        We look first at the field templates but fail over to
        a set of file templates that follow a conventional path.
        """
        code = self.code.lower()

        # Build a dict of message name to Template instances
        templates = {'subject': 'email_subject_template',
                     'body': 'email_body_template',
                     'html': 'email_body_html_template',
                     'sms': 'sms_template'}
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field is not None:
                # Template content is in a model field
                templates[name] = Template(field)
            else:
                # Model field is empty - look for a file template
                template_name = getattr(self, "%s_file" % attr_name) % code
                try:
                    templates[name] = get_template(template_name)
                except TemplateDoesNotExist:
                    templates[name] = None

        # Pass base URL for serving images within HTML emails
        if ctx is None:
            ctx = {}
        ctx['static_base_url'] = getattr(
            settings, 'OSCAR_STATIC_BASE_URL', None)

        messages = {}
        for name, template in templates.items():
            messages[name] = template.render(Context(ctx)) if template else ''

        # Ensure the email subject doesn't contain any newlines
        messages['subject'] = messages['subject'].replace("\n", "")
        messages['subject'] = messages['subject'].replace("\r", "")

        return messages

    def __str__(self):
        return self.name

    def is_order_related(self):
        return self.category == self.ORDER_RELATED

    def is_user_related(self):
        return self.category == self.USER_RELATED


@python_2_unicode_compatible
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name='notifications', db_index=True)

    # Not all notifications will have a sender.
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    # HTML is allowed in this field as it can contain links
    subject = models.CharField(max_length=255)
    body = models.TextField()

    # Some projects may want to categorise their notifications.  You may want
    # to use this field to show a different icons next to the notification.
    category = models.CharField(max_length=255, blank=True)

    INBOX, ARCHIVE = 'Inbox', 'Archive'
    choices = (
        (INBOX, _('Inbox')),
        (ARCHIVE, _('Archive')))
    location = models.CharField(max_length=32, choices=choices,
                                default=INBOX)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-date_sent',)
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()
    archive.alters_data = True

    @property
    def is_read(self):
        return self.date_read is not None


class ProductAlert(models.Model):
    product = models.ForeignKey('catelogue.Product')

    # A user is only required if the notification is created by a
    # registered user, anonymous users will only have an email address
    # attached to the notification
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, blank=True,
                             null=True, related_name="alerts",
                             verbose_name=_('User'))
    email = models.EmailField(_("Email"), db_index=True, blank=True)

    # This key are used to confirm and cancel alerts for anon users
    key = models.CharField(_("Key"), max_length=128, blank=True, db_index=True)

    # An alert can have two different statuses for authenticated
    # users ``ACTIVE`` and ``INACTIVE`` and anonymous users have an
    # additional status ``UNCONFIRMED``. For anonymous users a confirmation
    # and unsubscription key are generated when an instance is saved for
    # the first time and can be used to confirm and unsubscribe the
    # notifications.
    UNCONFIRMED, ACTIVE, CANCELLED, CLOSED = (
        'Unconfirmed', 'Active', 'Cancelled', 'Closed')
    STATUS_CHOICES = (
        (UNCONFIRMED, _('Not yet confirmed')),
        (ACTIVE, _('Active')),
        (CANCELLED, _('Cancelled')),
        (CLOSED, _('Closed')),
    )
    status = models.CharField(_("Status"), max_length=20,
                              choices=STATUS_CHOICES, default=ACTIVE)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_confirmed = models.DateTimeField(_("Date confirmed"), blank=True,
                                          null=True)
    date_cancelled = models.DateTimeField(_("Date cancelled"), blank=True,
                                          null=True)
    date_closed = models.DateTimeField(_("Date closed"), blank=True, null=True)

    class Meta:
        verbose_name = _('Product alert')
        verbose_name_plural = _('Product alerts')

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def can_be_confirmed(self):
        return self.status == self.UNCONFIRMED

    @property
    def can_be_cancelled(self):
        return self.status == self.ACTIVE

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED

    @property
    def is_active(self):
        return self.status == self.ACTIVE

    def confirm(self):
        self.status = self.ACTIVE
        self.date_confirmed = timezone.now()
        self.save()
    confirm.alters_data = True

    def cancel(self):
        self.status = self.CANCELLED
        self.date_cancelled = timezone.now()
        self.save()
    cancel.alters_data = True

    def close(self):
        self.status = self.CLOSED
        self.date_closed = timezone.now()
        self.save()
    close.alters_data = True

    def get_email_address(self):
        if self.user:
            return self.user.email
        else:
            return self.email

    def save(self, *args, **kwargs):
        if not self.id and not self.user:
            self.key = self.get_random_key()
            self.status = self.UNCONFIRMED
        # Ensure date fields get updated when saving from modelform (which just
        # calls save, and doesn't call the methods cancel(), confirm() etc).
        if self.status == self.CANCELLED and self.date_cancelled is None:
            self.date_cancelled = timezone.now()
        if not self.user and self.status == self.ACTIVE \
                and self.date_confirmed is None:
            self.date_confirmed = timezone.now()
        if self.status == self.CLOSED and self.date_closed is None:
            self.date_closed = timezone.now()

        return super(ProductAlert, self).save(*args, **kwargs)

    def get_random_key(self):
        """
        Get a random generated key based on SHA-1 and email address
        """
        salt = hashlib.sha1(str(random.random()).encode('utf8')).hexdigest()
        return hashlib.sha1((salt + self.email).encode('utf8')).hexdigest()

    def get_confirm_url(self):
        return reverse('customer:alerts-confirm', kwargs={'key': self.key})

    def get_cancel_url(self):
        return reverse('customer:alerts-cancel-by-key', kwargs={'key':
                                                                self.key})