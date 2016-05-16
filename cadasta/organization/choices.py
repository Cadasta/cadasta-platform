from django.utils.translation import ugettext as _


ADMIN_CHOICES = (('A', _('Administrator')),
                 ('M', _('Member')))

ROLE_CHOICES = (('PU', _('Project User')),
                ('DC', _('Data Collector')),
                ('PM', _('Project Manager')))

ACCESS_CHOICES = [("public", _("Public")),
                  ("private", _("Private"))]
